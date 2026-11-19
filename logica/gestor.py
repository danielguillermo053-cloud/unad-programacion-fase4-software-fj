"""Gestor de Software FJ: listas internas y reglas de negocio (sin base de datos)."""

from datetime import datetime
from functools import wraps

from modelos import Cliente, Reserva, Servicio
from utilidades.excepciones import (ClienteInvalidoError, ConflictoHorarioError, ErrorSoftwareFJ,
                                    OperacionNoPermitidaError, ReservaInvalidaError)
from utilidades.registro_logs import log


def registrar_errores(metodo):
    @wraps(metodo)
    def protegido(*args, **kwargs):
        try:
            return metodo(*args, **kwargs)
        except ErrorSoftwareFJ as error:
            causa = f" | Causa: {error.__cause__}" if error.__cause__ else ""
            log.error(f"Gestor.{metodo.__name__}: {error}{causa}")
            raise
        except Exception as error:
            log.critical(f"Gestor.{metodo.__name__}: error inesperado {error!r}")
            raise
    return protegido


class GestorSoftwareFJ:
    def __init__(self):
        self.clientes: list[Cliente] = []
        self.servicios: list[Servicio] = []
        self.reservas: list[Reserva] = []
        self._ids = {"cliente": 0, "servicio": 0, "reserva": 0}

    def _nuevo_id(self, tipo: str) -> int:
        self._ids[tipo] += 1
        return self._ids[tipo]

    @staticmethod
    def _buscar(lista, identificador):
        return next((e for e in lista if str(e.id) == str(identificador)), None)

    def buscar_cliente(self, identificador):
        return self._buscar(self.clientes, identificador)

    def buscar_servicio(self, identificador):
        return self._buscar(self.servicios, identificador)

    def buscar_reserva(self, identificador):
        return self._buscar(self.reservas, identificador)

    def _documento_repetido(self, documento, excepto=None) -> bool:
        return any(c.documento == documento and c is not excepto for c in self.clientes)

    @registrar_errores
    def registrar_cliente(self, nombre, documento, correo, telefono) -> Cliente:
        cliente = Cliente(nombre, documento, correo, telefono)
        if self._documento_repetido(cliente.documento):
            raise ClienteInvalidoError(f"Ya existe un cliente con el documento {cliente.documento}.")
        cliente.establecer_id(self._nuevo_id("cliente"))
        self.clientes.append(cliente)
        log.info(f"Cliente registrado: {cliente}")
        return cliente

    @registrar_errores
    def actualizar_cliente(self, cliente: Cliente, nombre, documento, correo, telefono) -> Cliente:
        """Si algún dato es inválido, el cliente conserva sus datos anteriores."""
        antes = (cliente.nombre, cliente.documento, cliente.correo, cliente.telefono)
        try:
            cliente.nombre, cliente.documento, cliente.correo, cliente.telefono = nombre, documento, correo, telefono
            if self._documento_repetido(cliente.documento, excepto=cliente):
                raise ClienteInvalidoError(f"Ya existe otro cliente con el documento {cliente.documento}.")
        except ErrorSoftwareFJ:
            cliente.nombre, cliente.documento, cliente.correo, cliente.telefono = antes
            raise
        log.info(f"Cliente actualizado: {cliente}")
        return cliente

    @registrar_errores
    def eliminar_cliente(self, cliente: Cliente) -> None:
        if any(r.activa and r.cliente is cliente for r in self.reservas):
            raise OperacionNoPermitidaError(f"{cliente.nombre} tiene reservas activas; cancélelas primero.")
        self.clientes.remove(cliente)
        log.info(f"Cliente eliminado: {cliente}")

    @registrar_errores
    def agregar_servicio(self, servicio: Servicio) -> Servicio:
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("El objeto no corresponde a un Servicio válido.")
        if servicio in self.servicios:
            raise OperacionNoPermitidaError("Este servicio ya está registrado.")
        servicio.establecer_id(self._nuevo_id("servicio"))
        self.servicios.append(servicio)
        log.info(f"Servicio creado: {servicio}")
        return servicio

    @registrar_errores
    def actualizar_tarifa(self, servicio: Servicio, tarifa: float) -> Servicio:
        if servicio not in self.servicios:
            raise OperacionNoPermitidaError("El servicio no está registrado.")
        servicio.tarifa_hora = tarifa
        log.info(f"Tarifa actualizada: {servicio}")
        return servicio

    @registrar_errores
    def cambiar_disponibilidad(self, servicio: Servicio) -> Servicio:
        if servicio not in self.servicios:
            raise OperacionNoPermitidaError("El servicio no está registrado.")
        servicio.disponible = not servicio.disponible
        log.info(f"Disponibilidad cambiada: {servicio}")
        return servicio

    @registrar_errores
    def eliminar_servicio(self, servicio: Servicio) -> None:
        if any(r.activa and r.servicio is servicio for r in self.reservas):
            raise OperacionNoPermitidaError(f"'{servicio.nombre}' tiene reservas activas; cancélelas primero.")
        self.servicios.remove(servicio)
        log.info(f"Servicio eliminado: {servicio}")

    @registrar_errores
    def crear_reserva(self, cliente: Cliente, servicio: Servicio, horas: float,
                      inicio: datetime = None, descuento: float = 0.0, **parametros) -> Reserva:
        if cliente not in self.clientes or servicio not in self.servicios:
            raise ReservaInvalidaError("El cliente y el servicio deben estar registrados en el sistema.")
        reserva = Reserva(cliente, servicio, horas, inicio, descuento, **parametros)
        solapadas = [r for r in self.reservas
                     if r.servicio is servicio and r.ocupa_horario and r.solapa_con(reserva)]
        if not servicio.hay_cupo(solapadas, **parametros):
            raise ConflictoHorarioError(
                f"'{servicio.nombre}' no tiene cupo entre {reserva.inicio:%d/%m %H:%M} y {reserva.fin:%d/%m %H:%M}.")
        reserva.establecer_id(self._nuevo_id("reserva"))
        self.reservas.append(reserva)
        log.info(f"Reserva creada: {reserva}")
        return reserva

    def resumen(self) -> dict:
        procesadas = [r for r in self.reservas if r.estado == Reserva.PROCESADA]
        return {"clientes": len(self.clientes), "servicios": len(self.servicios),
                "disponibles": sum(s.disponible for s in self.servicios),
                "activas": sum(r.activa for r in self.reservas), "procesadas": len(procesadas),
                "ingresos": sum(r.costo_total for r in procesadas)}
