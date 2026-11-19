"""Pestaña Servicios: crear, actualizar tarifa, activar/desactivar y eliminar."""

import tkinter as tk
from tkinter import messagebox, ttk

from interfaz.comunes import crear_tabla, dinero, entero, llenar, numero, seleccionado
from modelos import AlquilerEquipo, AsesoriaEspecializada, ReservaSala

CAMPO_EXTRA = {"Sala": "Capacidad (personas)", "Equipo": "Tipo de equipo", "Asesoría": "Especialidad"}


class PestanaServicios(ttk.Frame):
    TITULO = "Servicios"

    def __init__(self, padre, app):
        super().__init__(padre)
        self.app, self.g = app, app.gestor
        formulario = ttk.LabelFrame(self, text="Datos del servicio")
        formulario.pack(fill="x", padx=8, pady=8)
        formulario.columnconfigure(1, weight=1)
        formulario.columnconfigure(3, weight=1)
        self.tipo, self.nombre, self.tarifa = tk.StringVar(value="Sala"), tk.StringVar(), tk.StringVar()
        self.extra, self.stock = tk.StringVar(), tk.StringVar()
        self.etiqueta_extra = tk.StringVar(value=CAMPO_EXTRA["Sala"])

        def campo(texto, fila, col, variable=None, etiqueta_var=None):
            ttk.Label(formulario, text=texto, textvariable=etiqueta_var).grid(row=fila, column=col, padx=6, pady=4, sticky="e")
            if variable is not None:
                entrada = ttk.Entry(formulario, textvariable=variable, width=24)
                entrada.grid(row=fila, column=col + 1, padx=6, pady=4, sticky="ew")
                return entrada

        ttk.Label(formulario, text="Tipo").grid(row=0, column=0, padx=6, pady=4, sticky="e")
        combo = ttk.Combobox(formulario, textvariable=self.tipo, values=list(CAMPO_EXTRA), state="readonly", width=24)
        combo.grid(row=0, column=1, padx=6, pady=4, sticky="ew")
        combo.bind("<<ComboboxSelected>>", lambda _e: self._cambiar_tipo())
        campo("Nombre", 0, 2, self.nombre)
        campo("Tarifa por hora ($)", 1, 0, self.tarifa)
        campo("", 1, 2, self.extra, self.etiqueta_extra)
        self.etiqueta_stock = ttk.Label(formulario, text="Unidades en inventario")
        self.entrada_stock = ttk.Entry(formulario, textvariable=self.stock, width=24)
        self.etiqueta_stock.grid(row=2, column=2, padx=6, pady=4, sticky="e")
        self.entrada_stock.grid(row=2, column=3, padx=6, pady=4, sticky="ew")
        self._cambiar_tipo()
        botones = ttk.Frame(formulario)
        botones.grid(row=3, column=0, columnspan=4, pady=6)
        for texto, comando in [("Crear servicio", self.crear), ("Actualizar tarifa del seleccionado", self.actualizar_tarifa),
                               ("Activar / desactivar", self.cambiar_disponibilidad), ("Eliminar", self.eliminar)]:
            ttk.Button(botones, text=texto, command=comando).pack(side="left", padx=4)
        self.tabla = crear_tabla(self, [("id", "ID", 45), ("tipo", "Tipo", 80), ("nombre", "Nombre", 190),
                                        ("tarifa", "Tarifa/h", 100), ("estado", "Estado", 110), ("detalle", "Detalles", 330)])
        self.tabla.bind("<<TreeviewSelect>>", lambda _e: self._cargar_tarifa())

    def _cambiar_tipo(self):
        """El inventario solo aplica a equipos."""
        self.etiqueta_extra.set(CAMPO_EXTRA[self.tipo.get()])
        for widget in (self.etiqueta_stock, self.entrada_stock):
            widget.grid() if self.tipo.get() == "Equipo" else widget.grid_remove()

    def _cargar_tarifa(self):
        marcada = self.tabla.selection()
        servicio = self.g.buscar_servicio(marcada[0]) if marcada else None
        if servicio:
            self.tarifa.set(f"{servicio.tarifa_hora:g}")

    def crear(self):
        def accion():
            tipo, nombre, tarifa, extra = self.tipo.get(), self.nombre.get(), numero(self.tarifa.get(), "Tarifa por hora"), self.extra.get()
            if tipo == "Sala":
                servicio = ReservaSala(nombre, tarifa, entero(extra, "Capacidad"))
            elif tipo == "Equipo":
                servicio = AlquilerEquipo(nombre, tarifa, extra, entero(self.stock.get(), "Inventario"))
            else:
                servicio = AsesoriaEspecializada(nombre, tarifa, extra)
            return self.g.agregar_servicio(servicio)
        if self.app.ejecutar(accion, "Servicio creado."):
            for variable in (self.nombre, self.tarifa, self.extra, self.stock):
                variable.set("")

    def actualizar_tarifa(self):
        def accion():
            servicio = seleccionado(self.tabla, self.g.buscar_servicio, "un servicio")
            return self.g.actualizar_tarifa(servicio, numero(self.tarifa.get(), "Tarifa por hora"))
        self.app.ejecutar(accion, "Tarifa actualizada (aplica a nuevos cobros).")

    def cambiar_disponibilidad(self):
        self.app.ejecutar(lambda: self.g.cambiar_disponibilidad(
            seleccionado(self.tabla, self.g.buscar_servicio, "un servicio")), "Disponibilidad actualizada.")

    def eliminar(self):
        def accion():
            servicio = seleccionado(self.tabla, self.g.buscar_servicio, "un servicio")
            if not messagebox.askyesno("Eliminar servicio", f"¿Eliminar '{servicio.nombre}'?"):
                return False
            self.g.eliminar_servicio(servicio)
        self.app.ejecutar(accion, "Servicio eliminado.")

    def refrescar(self):
        llenar(self.tabla, [(s.id, (s.id, s.TIPO, s.nombre, dinero(s.tarifa_hora),
                                    "Disponible" if s.disponible else "No disponible", s.detalle()), ())
                            for s in self.g.servicios])
