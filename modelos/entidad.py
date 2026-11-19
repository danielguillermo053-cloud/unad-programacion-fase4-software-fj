"""Clase abstracta general del sistema."""

from abc import ABC, abstractmethod

from utilidades.excepciones import OperacionNoPermitidaError


class EntidadBase(ABC):
    """Toda entidad (cliente, servicio, reserva) tiene un id y sabe describirse."""

    def __init__(self):
        self._id = None

    @property
    def id(self) -> int:
        return self._id

    def establecer_id(self, valor: int) -> None:
        if self._id is not None:
            raise OperacionNoPermitidaError("La entidad ya tiene un identificador asignado.")
        self._id = valor

    @abstractmethod
    def describir(self) -> str:
        """Texto descriptivo de la entidad (método abstracto)."""

    def __str__(self) -> str:
        return self.describir()
