"""Reserva: integra cliente, servicio, horario, duración y estado."""

from datetime import datetime, timedelta
import math

from modelos.cliente import Cliente
from modelos.entidad import EntidadBase
from modelos.servicios import Servicio
from utilidades.excepciones import (CalculoInconsistenteError, ErrorSoftwareFJ, OperacionNoPermitidaError,
                                    ReservaInvalidaError, ServicioNoDisponibleError)
from utilidades.registro_logs import log


class Reserva(EntidadBase):
    PENDIENTE, CONFIRMADA, CANCELADA, PROCESADA, FALLIDA = (
        "PENDIENTE", "CONFIRMADA", "CANCELADA", "PROCESADA", "FALLIDA")

    def __init__(self, cliente: Cliente, servicio: Servicio, horas: float,
                 inicio: datetime = None, descuento: float = 0.0, **parametros):
        super().__init__()
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un Cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un Servicio válido.")
        if isinstance(horas, bool) or not isinstance(horas, (int, float)):
            raise ReservaInvalidaError(f"Duración inválida: {horas!r}.")
        if not math.isfinite(float(horas)):
            raise ReservaInvalidaError(f"Duración inválida: {horas!r}.")
        if isinstance(descuento, bool) or not isinstance(descuento, (int, float)):
            raise ReservaInvalidaError(f"Descuento inválido: {descuento!r} (entre 0 % y 99 %).")
        if not math.isfinite(float(descuento)) or not 0 <= descuento < 1:
            raise ReservaInvalidaError(f"Descuento inválido: {descuento!r} (entre 0 % y 99 %).")
        ahora = datetime.now().replace(second=0, microsecond=0)
        inicio = ahora if inicio is None else inicio
        if not isinstance(inicio, datetime):
            raise ReservaInvalidaError("La fecha de inicio no es válida.")
        if inicio < ahora - timedelta(minutes=1):
            raise ReservaInvalidaError(f"La fecha de inicio ({inicio:%d/%m/%Y %H:%M}) ya pasó.")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(f"'{servicio.nombre}' no está disponible.")
        try:
            servicio.validar_parametros(horas, **parametros)
        except ErrorSoftwareFJ as error:
            raise ReservaInvalidaError(f"Parámetros rechazados por '{servicio.nombre}'.") from error
        self.cliente, self.servicio, self.horas = cliente, servicio, horas
        self.inicio, self.descuento, self.parametros = inicio, descuento, parametros
        self.estado = Reserva.PENDIENTE
        self.costo_total = self.desglose = None

    @property
    def fin(self) -> datetime:
        return self.inicio + timedelta(hours=self.horas)

    @property
    def activa(self) -> bool:
        return self.estado in (Reserva.PENDIENTE, Reserva.CONFIRMADA)

    @property
    def ocupa_horario(self) -> bool:
        return self.estado not in (Reserva.CANCELADA, Reserva.FALLIDA)

    def solapa_con(self, otra: "Reserva") -> bool:
        return self.inicio < otra.fin and otra.inicio < self.fin

    def confirmar(self) -> None:
        if self.estado != Reserva.PENDIENTE:
            raise OperacionNoPermitidaError(f"No se puede confirmar una reserva {self.estado}.")
        self.estado = Reserva.CONFIRMADA
        log.info(f"Reserva #{self.id} confirmada.")

    def cancelar(self) -> None:
        if not self.activa:
            raise OperacionNoPermitidaError(f"No se puede cancelar una reserva {self.estado}.")
        self.estado = Reserva.CANCELADA
        log.info(f"Reserva #{self.id} cancelada.")

    def procesar(self, *extra) -> float:
        """Calcula y cobra. Sin argumentos usa el descuento guardado; con argumentos, la variante pedida."""
        try:
            if self.estado != Reserva.CONFIRMADA:
                raise OperacionNoPermitidaError(f"Reserva #{self.id} en estado {self.estado}; debe estar CONFIRMADA.")
            if not self.servicio.disponible:
                raise ServicioNoDisponibleError(f"'{self.servicio.nombre}' dejó de estar disponible.")
            if not extra and self.descuento:
                extra = (self.descuento,)
            desglose = self.servicio.desglosar(self.horas, *extra, **self.parametros)
        except CalculoInconsistenteError as error:
            self.estado = Reserva.FALLIDA
            raise ReservaInvalidaError(f"Cálculo inconsistente en reserva #{self.id}.") from error
        except ErrorSoftwareFJ as error:
            raise ReservaInvalidaError(f"No se pudo procesar la reserva #{self.id}.") from error
        else:
            self.estado, self.desglose, self.costo_total = Reserva.PROCESADA, desglose, desglose["total"]
            log.info(f"Reserva #{self.id} procesada. Total: ${self.costo_total:,.2f}.")
            return self.costo_total
        finally:
            log.info(f"Fin del intento de procesamiento de la reserva #{self.id}.")

    def describir(self) -> str:
        total = f"${self.costo_total:,.2f}" if self.costo_total is not None else "por calcular"
        return (f"Reserva #{self.id}: {self.cliente.nombre} -> {self.servicio.nombre} | "
                f"{self.inicio:%d/%m/%Y %H:%M} ({self.horas:g} h) | {self.estado} | Total: {total}")
