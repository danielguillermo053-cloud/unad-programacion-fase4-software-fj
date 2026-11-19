"""Pestaña Resumen: cifras generales y próximas reservas."""

import tkinter as tk
from tkinter import ttk

from interfaz.comunes import crear_tabla, dinero, llenar


class PestanaResumen(ttk.Frame):
    TITULO = "Resumen"

    def __init__(self, padre, app):
        super().__init__(padre)
        self.app = app
        tarjetas = ttk.Frame(self)
        tarjetas.pack(fill="x", padx=8, pady=12)
        self.cifras = {}
        for col, (clave, titulo) in enumerate([("clientes", "Clientes"), ("servicios", "Servicios disponibles"),
                                               ("activas", "Reservas activas"), ("ingresos", "Ingresos (procesadas)")]):
            marco = ttk.LabelFrame(tarjetas, text=titulo)
            marco.grid(row=0, column=col, padx=6, sticky="nsew")
            tarjetas.columnconfigure(col, weight=1)
            self.cifras[clave] = tk.StringVar(value="0")
            ttk.Label(marco, textvariable=self.cifras[clave], font=app.fuente_grande, anchor="center").pack(
                fill="x", padx=10, pady=10)
        ttk.Label(self, text="Próximas reservas activas", font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=10)
        self.tabla = crear_tabla(self, [("hora", "Inicio", 140), ("cliente", "Cliente", 200),
                                        ("servicio", "Servicio", 200), ("estado", "Estado", 110), ("id", "Reserva", 70)])
        ttk.Label(self, text="Los datos viven en memoria durante la sesión (el enunciado no permite bases de datos).",
                  foreground="#666").pack(anchor="w", padx=10, pady=(0, 6))

    def refrescar(self):
        g = self.app.gestor
        datos = g.resumen()
        self.cifras["clientes"].set(str(datos["clientes"]))
        self.cifras["servicios"].set(f"{datos['disponibles']} / {datos['servicios']}")
        self.cifras["activas"].set(str(datos["activas"]))
        self.cifras["ingresos"].set(dinero(datos["ingresos"]))
        proximas = sorted((r for r in g.reservas if r.activa), key=lambda r: r.inicio)[:12]
        llenar(self.tabla, [(r.id, (f"{r.inicio:%d/%m/%Y %H:%M}", r.cliente.nombre, r.servicio.nombre,
                                    r.estado, f"#{r.id}"), (r.estado,)) for r in proximas])
