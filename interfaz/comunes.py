"""Funciones y constantes que comparten todas las pestañas."""

import math
import re
from tkinter import ttk

from modelos import Reserva
from utilidades.excepciones import ErrorSoftwareFJ, OperacionNoPermitidaError, ParametroFaltanteError

COLOR_ESTADO = {Reserva.PENDIENTE: "#fff4cc", Reserva.CONFIRMADA: "#d9ecff", Reserva.PROCESADA: "#d9f5dd",
                Reserva.CANCELADA: "#e4e4e4", Reserva.FALLIDA: "#ffd9d9"}


def dinero(valor: float) -> str:
    """$1,234 (con centavos solo si hacen falta)."""
    return f"${valor:,.2f}" if round(valor) != valor else f"${valor:,.0f}"


def numero(texto: str, nombre: str) -> float:
    """Texto -> número. Entiende '$ 80.000' y '1,500,000' como miles y acepta coma decimal."""
    texto = texto.strip().replace("$", "").replace(" ", "")
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", texto):
        texto = re.sub(r"[.,]", "", texto)
    texto = texto.replace(",", ".")
    if not texto:
        raise ParametroFaltanteError(f"Falta el campo '{nombre}'.")
    try:
        valor = float(texto)
        if not math.isfinite(valor):
            raise ValueError
        return valor
    except ValueError as error:
        raise ErrorSoftwareFJ(f"'{nombre}' debe ser un número (se recibió '{texto}').") from error


def entero(texto: str, nombre: str) -> int:
    valor = numero(texto, nombre)
    if valor != int(valor):
        raise ErrorSoftwareFJ(f"'{nombre}' debe ser un número entero.")
    return int(valor)


def crear_tabla(padre, columnas, altura=10):
    """Treeview con scroll. columnas = [(id, título, ancho)]."""
    marco = ttk.Frame(padre)
    tabla = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings", height=altura, selectmode="browse")
    for ident, titulo, ancho in columnas:
        tabla.heading(ident, text=titulo)
        tabla.column(ident, width=ancho, anchor="w")
    scroll = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)
    tabla.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    marco.pack(fill="both", expand=True, padx=8, pady=8)
    for estado, color in COLOR_ESTADO.items():
        tabla.tag_configure(estado, background=color)
    return tabla


def llenar(tabla, filas) -> None:
    """Reemplaza las filas (iid, valores, etiquetas) conservando la selección."""
    seleccion = tabla.selection()
    tabla.delete(*tabla.get_children())
    for iid, valores, etiquetas in filas:
        tabla.insert("", "end", iid=str(iid), values=valores, tags=etiquetas)
    if seleccion and tabla.exists(seleccion[0]):
        tabla.selection_set(seleccion[0])


def seleccionado(tabla, buscador, nombre: str):
    """Objeto de la fila marcada, o una excepción clara si no hay selección."""
    marcada = tabla.selection()
    objeto = buscador(marcada[0]) if marcada else None
    if objeto is None:
        raise OperacionNoPermitidaError(f"Seleccione {nombre} de la tabla.")
    return objeto
