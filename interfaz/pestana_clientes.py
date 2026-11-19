"""Pestaña Clientes: registrar, editar, eliminar y buscar."""

import tkinter as tk
from tkinter import messagebox, ttk

from interfaz.comunes import crear_tabla, llenar, seleccionado

CAMPOS = [("nombre", "Nombre completo"), ("documento", "Documento"), ("correo", "Correo"), ("telefono", "Teléfono")]


class PestanaClientes(ttk.Frame):
    TITULO = "Clientes"

    def __init__(self, padre, app):
        super().__init__(padre)
        self.app, self.g = app, app.gestor
        formulario = ttk.LabelFrame(self, text="Datos del cliente (seleccione una fila para editarla)")
        formulario.pack(fill="x", padx=8, pady=8)
        formulario.columnconfigure(1, weight=1)
        formulario.columnconfigure(3, weight=1)
        self.vars = {clave: tk.StringVar() for clave, _ in CAMPOS}
        for i, (clave, etiqueta) in enumerate(CAMPOS):
            fila, col = divmod(i, 2)
            ttk.Label(formulario, text=etiqueta).grid(row=fila, column=col * 2, padx=6, pady=4, sticky="e")
            ttk.Entry(formulario, textvariable=self.vars[clave], width=24).grid(
                row=fila, column=col * 2 + 1, padx=6, pady=4, sticky="ew")
        botones = ttk.Frame(formulario)
        botones.grid(row=2, column=0, columnspan=4, pady=6)
        for texto, comando in [("Registrar nuevo", self.registrar), ("Guardar cambios", self.actualizar),
                               ("Eliminar", self.eliminar), ("Limpiar formulario", self.limpiar)]:
            ttk.Button(botones, text=texto, command=comando).pack(side="left", padx=4)

        buscador = ttk.Frame(self)
        buscador.pack(fill="x", padx=8)
        ttk.Label(buscador, text="Buscar:").pack(side="left")
        self.var_buscar = tk.StringVar()
        self.var_buscar.trace_add("write", lambda *_: self.refrescar())
        ttk.Entry(buscador, textvariable=self.var_buscar, width=40).pack(side="left", padx=6)
        self.tabla = crear_tabla(self, [("id", "ID", 50), ("nombre", "Nombre", 220), ("doc", "Documento", 120),
                                        ("correo", "Correo", 250), ("tel", "Teléfono", 110)])
        self.tabla.bind("<<TreeviewSelect>>", lambda _e: self._cargar_en_formulario())

    def _datos(self):
        return [self.vars[clave].get() for clave, _ in CAMPOS]

    def _cargar_en_formulario(self):
        marcada = self.tabla.selection()
        cliente = self.g.buscar_cliente(marcada[0]) if marcada else None
        if cliente:
            for clave in self.vars:
                self.vars[clave].set(getattr(cliente, clave))

    def limpiar(self):
        for variable in self.vars.values():
            variable.set("")
        self.tabla.selection_remove(self.tabla.selection())

    def registrar(self):
        if self.app.ejecutar(lambda: self.g.registrar_cliente(*self._datos()), "Cliente registrado."):
            self.limpiar()

    def actualizar(self):
        def accion():
            cliente = seleccionado(self.tabla, self.g.buscar_cliente, "un cliente")
            return self.g.actualizar_cliente(cliente, *self._datos())
        self.app.ejecutar(accion, "Datos del cliente actualizados.")

    def eliminar(self):
        def accion():
            cliente = seleccionado(self.tabla, self.g.buscar_cliente, "un cliente")
            if not messagebox.askyesno("Eliminar cliente", f"¿Eliminar a {cliente.nombre}?"):
                return False
            self.g.eliminar_cliente(cliente)
            self.limpiar()
        self.app.ejecutar(accion, "Cliente eliminado.")

    def refrescar(self):
        filtro = self.var_buscar.get().strip().lower()
        llenar(self.tabla, [(c.id, (c.id, c.nombre, c.documento, c.correo, c.telefono), ())
                            for c in self.g.clientes
                            if not filtro or filtro in f"{c.nombre} {c.documento} {c.correo}".lower()])
