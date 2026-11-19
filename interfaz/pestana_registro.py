"""Pestaña Registro: visor del archivo de logs con los errores resaltados."""

import tkinter as tk
from tkinter import ttk

from utilidades.registro_logs import ARCHIVO_LOG


class PestanaRegistro(ttk.Frame):
    TITULO = "Registro (logs)"

    def __init__(self, padre, app):
        super().__init__(padre)
        superior = ttk.Frame(self)
        superior.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(superior, text=f"Archivo: {ARCHIVO_LOG}").pack(side="left")
        self.solo_errores = tk.BooleanVar(value=False)
        ttk.Checkbutton(superior, text="Mostrar solo errores", variable=self.solo_errores,
                        command=self.refrescar).pack(side="right")
        marco = ttk.Frame(self)
        marco.pack(fill="both", expand=True, padx=8, pady=8)
        self.texto = tk.Text(marco, wrap="none", state="disabled", font=("Courier", 9))
        vertical = ttk.Scrollbar(marco, orient="vertical", command=self.texto.yview)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.texto.xview)
        self.texto.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        vertical.pack(side="right", fill="y")
        self.texto.pack(side="left", fill="both", expand=True)
        horizontal.pack(fill="x", padx=8)
        self.texto.tag_configure("ERROR", foreground="#b00020")
        self.texto.tag_configure("CRITICAL", foreground="#ffffff", background="#b00020")

    def refrescar(self):
        try:
            with open(ARCHIVO_LOG, encoding="utf-8") as archivo:
                lineas = archivo.readlines()
        except OSError as error:  # Si no se puede leer, la app sigue funcionando.
            lineas = [f"No se pudo leer el log: {error}\n"]
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        for linea in lineas:
            nivel = "CRITICAL" if "| CRITICAL" in linea else "ERROR" if "| ERROR" in linea else ""
            if not self.solo_errores.get() or nivel:
                self.texto.insert("end", linea, nivel)
        self.texto.see("end")
        self.texto.configure(state="disabled")
