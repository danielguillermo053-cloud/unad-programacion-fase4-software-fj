"""Servicio (clase abstracta) y sus tres especializaciones: sala, equipo y asesoría."""

from abc import abstractmethod
import math

from modelos.entidad import EntidadBase
from utilidades.excepciones import CalculoInconsistenteError, ParametroFaltanteError, ServicioInvalidoError

IVA = 0.19


def _entero_positivo(valor, mensaje: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ServicioInvalidoError(mensaje.format(valor))
    return valor


def _texto(valor, mensaje: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ServicioInvalidoError(mensaje)
    return valor.strip()


def _numero_finito(valor, mensaje: str) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ServicioInvalidoError(mensaje.format(valor))
    numero = float(valor)
    if not math.isfinite(numero):
        raise ServicioInvalidoError(mensaje.format(valor))
    return numero


class Servicio(EntidadBase):
    """Contrato común: cada servicio calcula su costo, valida parámetros y decide su cupo."""

    TIPO = "Servicio"

    def __init__(self, nombre: str, tarifa_hora: float):
        super().__init__()
        self._nombre = _texto(nombre, "El nombre del servicio es obligatorio.")
        self.tarifa_hora = tarifa_hora
        self.disponible = True

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_hora(self) -> float:
        return self._tarifa_hora

    @tarifa_hora.setter
    def tarifa_hora(self, valor):
        tarifa = _numero_finito(valor, "Tarifa inválida: {}.")
        if tarifa <= 0:
            raise ServicioInvalidoError(f"Tarifa inválida: {valor}.")
        self._tarifa_hora = tarifa

    @abstractmethod
    def calcular_costo_base(self, horas: float, **parametros) -> float:
        """Costo sin impuestos ni descuentos."""

    @abstractmethod
    def validar_parametros(self, horas: float, **parametros) -> None:
        """Lanza una excepción si la reserva pedida no es válida para este servicio."""

    @abstractmethod
    def detalle(self) -> str:
        """Datos propios de cada tipo de servicio."""

    def hay_cupo(self, solapadas: list, **parametros) -> bool:
        """Por defecto atiende una reserva a la vez; los hijos pueden cambiarlo."""
        return not solapadas

    def desglosar(self, horas: float, *extra, **parametros) -> dict:
        """desglosar(h) -> base+IVA | desglosar(h, desc) -> con descuento | desglosar(h, desc, imp) -> impuesto propio."""
        if len(extra) > 2:
            raise ParametroFaltanteError("Demasiados argumentos para calcular el costo.")
        descuento = extra[0] if extra else 0.0
        impuesto = extra[1] if len(extra) == 2 else IVA
        descuento = _numero_finito(descuento, "Descuento inválido: {}.")
        impuesto = _numero_finito(impuesto, "Impuesto inválido: {}.")
        if not 0 <= descuento < 1 or not 0 <= impuesto <= 1:
            raise CalculoInconsistenteError(f"Descuento ({descuento}) o impuesto ({impuesto}) fuera de rango.")
        horas = _numero_finito(horas, "Duración inválida: {}.")
        if horas <= 0:
            raise CalculoInconsistenteError(f"Duración inválida: {horas}.")
        base = self.calcular_costo_base(horas, **parametros)
        subtotal = base * (1 - descuento)
        total = subtotal * (1 + impuesto)
        if total <= 0:
            raise CalculoInconsistenteError(f"Costo inconsistente: {total}.")
        return {"base": round(base, 2), "tasa_descuento": descuento, "descuento": round(base - subtotal, 2),
                "subtotal": round(subtotal, 2), "tasa_impuesto": impuesto,
                "impuesto": round(total - subtotal, 2), "total": round(total, 2)}

    def calcular_costo(self, horas: float, *extra, **parametros) -> float:
        return self.desglosar(horas, *extra, **parametros)["total"]

    def describir(self) -> str:
        estado = "Disponible" if self.disponible else "No disponible"
        return f"Servicio #{self.id}: {self.nombre} | ${self.tarifa_hora:,.0f}/h | {estado}"


class ReservaSala(Servicio):
    TIPO = "Sala"

    def __init__(self, nombre: str, tarifa_hora: float, capacidad: int):
        super().__init__(nombre, tarifa_hora)
        self._capacidad = _entero_positivo(capacidad, "Capacidad inválida: {}.")

    def validar_parametros(self, horas, **parametros):
        personas = parametros.get("personas")
        if personas is None:
            raise ParametroFaltanteError("Falta el parámetro 'personas'.")
        if isinstance(personas, bool) or not isinstance(personas, int):
            raise ServicioInvalidoError(f"Cantidad de personas inválida: {personas}.")
        if not 1 <= horas <= 8:
            raise ServicioInvalidoError(f"Duración inválida para sala: {horas:g} h (1-8).")
        if not 1 <= personas <= self._capacidad:
            raise ServicioInvalidoError(f"{personas} personas exceden la capacidad ({self._capacidad}).")

    def calcular_costo_base(self, horas, **parametros):
        return self.tarifa_hora * horas

    def detalle(self):
        return f"Capacidad: {self._capacidad} personas"

    def describir(self):
        return f"[Sala] {super().describir()} | {self.detalle()}"


class AlquilerEquipo(Servicio):
    TIPO = "Equipo"
    SEGURO = 0.05

    def __init__(self, nombre: str, tarifa_hora: float, tipo_equipo: str, stock: int = 1):
        super().__init__(nombre, tarifa_hora)
        self._tipo_equipo = _texto(tipo_equipo, "El tipo de equipo es obligatorio.")
        self._stock = _entero_positivo(stock, "Unidades en inventario inválidas: {}.")

    def validar_parametros(self, horas, **parametros):
        cantidad = parametros.get("cantidad")
        if cantidad is None:
            raise ParametroFaltanteError("Falta el parámetro 'cantidad'.")
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad < 1:
            raise ServicioInvalidoError(f"Cantidad inválida: {cantidad}.")
        if cantidad > self._stock:
            raise ServicioInvalidoError(f"Se piden {cantidad} unidades y el inventario es de {self._stock}.")
        if not 1 <= horas <= 72:
            raise ServicioInvalidoError(f"Duración inválida para equipo: {horas:g} h (1-72).")

    def hay_cupo(self, solapadas, **parametros):
        """Sobrescrito: varias reservas a la vez mientras alcance el inventario."""
        en_uso = sum(r.parametros.get("cantidad", 1) for r in solapadas)
        return en_uso + parametros.get("cantidad", 1) <= self._stock

    def calcular_costo_base(self, horas, **parametros):
        return self.tarifa_hora * horas * parametros.get("cantidad", 1) * (1 + self.SEGURO)

    def detalle(self):
        return f"Tipo: {self._tipo_equipo} | Inventario: {self._stock} unid."

    def describir(self):
        return f"[Equipo] {super().describir()} | {self.detalle()}"


class AsesoriaEspecializada(Servicio):
    TIPO = "Asesoría"
    RECARGOS = {"junior": 0.0, "senior": 0.30}

    def __init__(self, nombre: str, tarifa_hora: float, especialidad: str):
        super().__init__(nombre, tarifa_hora)
        self._especialidad = _texto(especialidad, "La especialidad es obligatoria.")

    def validar_parametros(self, horas, **parametros):
        nivel = parametros.get("nivel")
        if nivel is None:
            raise ParametroFaltanteError("Falta el parámetro 'nivel'.")
        if nivel not in self.RECARGOS:
            raise ServicioInvalidoError(f"Nivel inválido: '{nivel}' (junior/senior).")
        if not 0.5 <= horas <= 6:
            raise ServicioInvalidoError(f"Duración inválida para asesoría: {horas:g} h (0.5-6).")

    def calcular_costo_base(self, horas, **parametros):
        return self.tarifa_hora * horas * (1 + self.RECARGOS.get(parametros.get("nivel", "junior"), 0.0))

    def detalle(self):
        return f"Especialidad: {self._especialidad}"

    def describir(self):
        return f"[Asesoría] {super().describir()} | {self.detalle()}"
