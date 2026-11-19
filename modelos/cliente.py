"""Cliente de Software FJ: datos encapsulados y validados."""

import re

from modelos.entidad import EntidadBase
from utilidades.excepciones import ClienteInvalidoError


def _validar(valor, patron: str, mensaje: str) -> str:
    """Quita espacios y comprueba el formato; si falla lanza ClienteInvalidoError."""
    valor = valor.strip() if isinstance(valor, str) else valor
    if not isinstance(valor, str) or not re.fullmatch(patron, valor):
        raise ClienteInvalidoError(mensaje.format(valor))
    return valor


class Cliente(EntidadBase):
    def __init__(self, nombre: str, documento: str, correo: str, telefono: str):
        super().__init__()
        self.nombre, self.documento, self.correo, self.telefono = nombre, documento, correo, telefono

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        self.__nombre = _validar(valor, r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]{3,60}",
                                 "Nombre inválido: '{}' (solo letras, 3 a 60 caracteres).").title()

    @property
    def documento(self) -> str:
        return self.__documento

    @documento.setter
    def documento(self, valor):
        self.__documento = _validar(valor, r"\d{6,12}", "Documento inválido: '{}' (6 a 12 dígitos).")

    @property
    def correo(self) -> str:
        return self.__correo

    @correo.setter
    def correo(self, valor):
        self.__correo = _validar(valor, r"[\w.+-]+@[\w-]+\.[\w.-]+", "Correo inválido: '{}'.").lower()

    @property
    def telefono(self) -> str:
        return self.__telefono

    @telefono.setter
    def telefono(self, valor):
        self.__telefono = _validar(valor, r"\d{7,10}", "Teléfono inválido: '{}' (7 a 10 dígitos).")

    def describir(self) -> str:
        return f"Cliente #{self.id}: {self.nombre} | Doc: {self.documento} | {self.correo}"
