"""Pestaña Reservas: crear con fecha y hora, costo en vivo, confirmar, cobrar, cancelar y ver detalle."""

import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

from interfaz.comunes import crear_tabla, dinero, entero, llenar, numero, seleccionado
from modelos import AlquilerEquipo, AsesoriaEspecializada, Reserva, ReservaSala
from utilidades.excepciones import ErrorSoftwareFJ, ParametroFaltanteError

ETIQUETA_PARAM = {ReservaSala: "Número de personas", AlquilerEquipo: "Cantidad de equipos",
                  AsesoriaEspecializada: "Nivel (junior / senior)"}


class PestanaReservas(ttk.Frame):
    TITULO = "Reservas"

    def __init__(self, padre, app):
        super().__init__(padre)
        self.app, self.g = app, app.gestor
        inicio = datetime.now() + timedelta(hours=1)
        self.cliente, self.servicio = tk.StringVar(), tk.StringVar()
        self.fecha, self.hora, self.minutos = tk.StringVar(value=f"{inicio:%Y-%m-%d}"), tk.StringVar(value=f"{inicio:%H}"), tk.StringVar(value="00")
        self.horas, self.param, self.desc = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.etiqueta_param, self.estimacion = tk.StringVar(value="Parámetro del servicio"), tk.StringVar()

        formulario = ttk.LabelFrame(self, text="Nueva reserva")
        formulario.pack(fill="x", padx=8, pady=(8, 4))
        formulario.columnconfigure(1, weight=1)
        formulario.columnconfigure(3, weight=1)

        def etiqueta(texto, fila, col, variable=None):
            ttk.Label(formulario, text=texto, textvariable=variable).grid(row=fila, column=col, padx=6, pady=4, sticky="e")

        def entrada(variable, fila, col):
            ttk.Entry(formulario, textvariable=variable, width=24).grid(row=fila, column=col, padx=6, pady=4, sticky="ew")

        etiqueta("Cliente", 0, 0)
        self.combo_clientes = ttk.Combobox(formulario, textvariable=self.cliente, state="readonly", width=24)
        self.combo_clientes.grid(row=0, column=1, padx=6, pady=4, sticky="ew")
        etiqueta("Servicio", 0, 2)
        self.combo_servicios = ttk.Combobox(formulario, textvariable=self.servicio, state="readonly", width=24)
        self.combo_servicios.grid(row=0, column=3, padx=6, pady=4, sticky="ew")
        self.combo_servicios.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_etiqueta())

        etiqueta("Fecha (AAAA-MM-DD)", 1, 0)
        marco = ttk.Frame(formulario)
        marco.grid(row=1, column=1, padx=6, pady=4, sticky="w")
        ttk.Entry(marco, textvariable=self.fecha, width=12).pack(side="left")
        ttk.Label(marco, text="  Hora").pack(side="left")
        ttk.Spinbox(marco, from_=0, to=23, width=4, format="%02.0f", textvariable=self.hora, wrap=True).pack(side="left", padx=2)
        ttk.Label(marco, text=":").pack(side="left")
        ttk.Spinbox(marco, values=("00", "15", "30", "45"), width=4, textvariable=self.minutos, wrap=True).pack(side="left", padx=2)
        etiqueta("Duración (horas)", 1, 2)
        entrada(self.horas, 1, 3)
        etiqueta("", 2, 0, self.etiqueta_param)
        entrada(self.param, 2, 1)
        etiqueta("Descuento (%) opcional", 2, 2)
        entrada(self.desc, 2, 3)
        self.aviso = ttk.Label(formulario, textvariable=self.estimacion, wraplength=860)
        self.aviso.grid(row=3, column=0, columnspan=4, padx=8, pady=2, sticky="w")
        ttk.Button(formulario, text="Crear reserva", command=self.crear).grid(row=4, column=0, columnspan=4, pady=6)
        for variable in (self.servicio, self.horas, self.param, self.desc):
            variable.trace_add("write", lambda *_: self._estimar())

        acciones = ttk.LabelFrame(self, text="Reserva seleccionada (doble clic para ver el detalle)")
        acciones.pack(fill="x", padx=8, pady=4)
        self.botones = {}
        for clave, texto in (("confirmar", "Confirmar"), ("procesar", "Procesar y cobrar"), ("cancelar", "Cancelar reserva")):
            self.botones[clave] = ttk.Button(acciones, text=texto, command=lambda c=clave: self.accion(c))
            self.botones[clave].pack(side="left", padx=6, pady=6)
        ttk.Label(acciones, text="Filtrar por estado:").pack(side="left", padx=(30, 4))
        self.filtro = tk.StringVar(value="Todas")
        combo = ttk.Combobox(acciones, textvariable=self.filtro, state="readonly", width=14,
                             values=["Todas", "Activas", Reserva.PENDIENTE, Reserva.CONFIRMADA,
                                     Reserva.PROCESADA, Reserva.CANCELADA, Reserva.FALLIDA])
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda _e: self.refrescar())
        self.tabla = crear_tabla(self, [("id", "ID", 45), ("cliente", "Cliente", 170), ("servicio", "Servicio", 170),
                                        ("inicio", "Inicio", 125), ("fin", "Fin", 125), ("estado", "Estado", 105),
                                        ("total", "Total", 120)], altura=8)
        self.tabla.bind("<<TreeviewSelect>>", lambda _e: self._actualizar_botones())
        self.tabla.bind("<Double-1>", lambda _e: self.ver_detalle())

    def _servicio(self):
        return self.g.buscar_servicio(self.servicio.get().split(" - ")[0]) if self.servicio.get() else None

    def _cliente(self):
        return self.g.buscar_cliente(self.cliente.get().split(" - ")[0]) if self.cliente.get() else None

    def _actualizar_etiqueta(self):
        self.etiqueta_param.set(ETIQUETA_PARAM.get(type(self._servicio()), "Parámetro del servicio"))

    def _parametros(self, servicio) -> dict:
        """Convierte el campo de parámetro al tipo que pide cada servicio (vacío -> lo avisa el servicio)."""
        valor = self.param.get().strip()
        if not valor:
            return {}
        if isinstance(servicio, ReservaSala):
            return {"personas": entero(valor, "Personas")}
        if isinstance(servicio, AlquilerEquipo):
            return {"cantidad": entero(valor, "Cantidad")}
        return {"nivel": valor.lower()}

    def _descuento(self) -> float:
        texto = self.desc.get().strip()
        return numero(texto, "Descuento") / 100 if texto else 0.0

    def _inicio(self) -> datetime:
        try:
            fecha = datetime.strptime(self.fecha.get().strip(), "%Y-%m-%d")
        except ValueError as error:
            raise ErrorSoftwareFJ("La fecha debe tener el formato AAAA-MM-DD (por ejemplo 2026-11-25).") from error
        try:
            return fecha.replace(hour=int(self.hora.get()), minute=int(self.minutos.get()))
        except ValueError as error:
            raise ErrorSoftwareFJ("La hora o los minutos no son válidos.") from error

    def _estimar(self):
        """Costo estimado en verde, o el motivo del problema en rojo."""
        servicio = self._servicio()
        if servicio is None or not self.horas.get().strip():
            self.estimacion.set("Elija un servicio y escriba la duración para ver el costo estimado.")
            self.aviso.configure(foreground="#666")
            return
        try:
            horas, parametros = numero(self.horas.get(), "Duración"), self._parametros(servicio)
            servicio.validar_parametros(horas, **parametros)
            d = servicio.desglosar(horas, self._descuento(), **parametros)
        except ErrorSoftwareFJ as error:
            self.estimacion.set(f"⚠ {error}")
            self.aviso.configure(foreground="#b00020")
        else:
            self.estimacion.set(f"Costo estimado: base {dinero(d['base'])} − descuento {dinero(d['descuento'])} "
                                f"+ IVA {dinero(d['impuesto'])} = TOTAL {dinero(d['total'])}")
            self.aviso.configure(foreground="#1b6e2d")

    def crear(self):
        def accion():
            cliente, servicio = self._cliente(), self._servicio()
            if cliente is None or servicio is None:
                raise ParametroFaltanteError("Seleccione un cliente y un servicio.")
            return self.g.crear_reserva(cliente, servicio, numero(self.horas.get(), "Duración"), self._inicio(),
                                        self._descuento(), **self._parametros(servicio))
        if self.app.ejecutar(accion, "Reserva creada en estado PENDIENTE. Confírmela para continuar."):
            for variable in (self.horas, self.param, self.desc):
                variable.set("")

    def accion(self, nombre: str):
        def ejecutar():
            reserva = seleccionado(self.tabla, self.g.buscar_reserva, "una reserva")
            if nombre == "confirmar":
                return reserva.confirmar()
            if nombre == "cancelar":
                if not messagebox.askyesno("Cancelar reserva", f"¿Cancelar la reserva #{reserva.id}?"):
                    return False
                return reserva.cancelar()
            return reserva.procesar()
        resultado = self.app.ejecutar(ejecutar, f"Reserva: '{nombre}' realizado correctamente.")
        if nombre == "procesar" and isinstance(resultado, float):
            messagebox.showinfo("Reserva procesada", f"Total cobrado: {dinero(resultado)}")

    def _actualizar_botones(self):
        """Solo se habilitan las acciones que tienen sentido para el estado de la reserva marcada."""
        marcada = self.tabla.selection()
        r = self.g.buscar_reserva(marcada[0]) if marcada else None
        permitidas = {"confirmar": r is not None and r.estado == Reserva.PENDIENTE,
                      "procesar": r is not None and r.estado == Reserva.CONFIRMADA,
                      "cancelar": r is not None and r.activa}
        for clave, boton in self.botones.items():
            boton.state(["!disabled"] if permitidas[clave] else ["disabled"])

    def ver_detalle(self):
        """Detalle tipo factura de la reserva marcada (cobrado o estimado)."""
        marcada = self.tabla.selection()
        r = self.g.buscar_reserva(marcada[0]) if marcada else None
        if r is None:
            return
        try:
            d = r.desglose or r.servicio.desglosar(r.horas, r.descuento, **r.parametros)
            cobro = (f"\n--- Cobro ({'COBRADO' if r.desglose else 'ESTIMADO'}) ---\nValor base:   {dinero(d['base'])}\n"
                     f"Descuento ({d['tasa_descuento']:.0%}): -{dinero(d['descuento'])}\nSubtotal:     {dinero(d['subtotal'])}\n"
                     f"IVA ({d['tasa_impuesto']:.0%}):    {dinero(d['impuesto'])}\nTOTAL:        {dinero(d['total'])}")
        except ErrorSoftwareFJ as error:
            cobro = f"\nNo se puede calcular el cobro: {error}"
        extras = ", ".join(f"{k}: {v}" for k, v in r.parametros.items())
        messagebox.showinfo(f"Reserva #{r.id}", (
            f"Cliente:  {r.cliente.nombre} (doc. {r.cliente.documento})\nServicio: {r.servicio.nombre}\n"
            f"Inicio:   {r.inicio:%d/%m/%Y %H:%M}\nFin:      {r.fin:%d/%m/%Y %H:%M}  ({r.horas:g} h)\n"
            f"Datos:    {extras}\nEstado:   {r.estado}{cobro}"))

    def refrescar(self):
        self.combo_clientes["values"] = [f"{c.id} - {c.nombre}" for c in self.g.clientes]
        self.combo_servicios["values"] = [f"{s.id} - {s.nombre}" for s in self.g.servicios if s.disponible]
        f = self.filtro.get()
        visibles = sorted((r for r in self.g.reservas if f == "Todas" or (f == "Activas" and r.activa) or r.estado == f),
                          key=lambda r: r.inicio)
        llenar(self.tabla, [(r.id, (r.id, r.cliente.nombre, r.servicio.nombre, f"{r.inicio:%d/%m/%Y %H:%M}",
                                    f"{r.fin:%d/%m/%Y %H:%M}", r.estado,
                                    dinero(r.costo_total) if r.costo_total is not None else "-"), (r.estado,))
                            for r in visibles])
        self._actualizar_botones()
        self._estimar()
