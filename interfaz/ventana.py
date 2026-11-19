"""Ventana principal: menú, pestañas, barra de estado y manejo central de errores."""

import io
import tkinter as tk
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from interfaz.pestana_clientes import PestanaClientes
from interfaz.pestana_registro import PestanaRegistro
from interfaz.pestana_reservas import PestanaReservas
from interfaz.pestana_resumen import PestanaResumen
from interfaz.pestana_servicios import PestanaServicios
from logica.gestor import GestorSoftwareFJ
from logica.simulacion import simulacion
from modelos import AlquilerEquipo, AsesoriaEspecializada, ReservaSala
from utilidades.excepciones import ErrorSoftwareFJ
from utilidades.registro_logs import log


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Software FJ - Gestión de clientes, servicios y reservas")
        self.geometry("1020x680")
        self.minsize(900, 600)
        self.gestor = GestorSoftwareFJ()
        self.estado = tk.StringVar(value="Bienvenido. Empiece registrando un cliente y un servicio.")
        self.fuente_grande = tkfont.nametofont("TkDefaultFont").copy()
        self.fuente_grande.configure(size=20, weight="bold")
        self._crear_menu()
        ttk.Label(self, textvariable=self.estado, relief="sunken", anchor="w", padding=3).pack(fill="x", side="bottom")
        cuaderno = ttk.Notebook(self)
        cuaderno.pack(fill="both", expand=True, padx=8, pady=8)
        self.pestanas = [clase(cuaderno, self) for clase in (
            PestanaResumen, PestanaClientes, PestanaServicios, PestanaReservas, PestanaRegistro)]
        for pestana in self.pestanas:
            cuaderno.add(pestana, text=pestana.TITULO)
        self.refrescar()

    def _crear_menu(self):
        barra = tk.Menu(self)
        archivo = tk.Menu(barra, tearoff=False)
        archivo.add_command(label="Cargar datos de demostración", command=self.cargar_demo)
        archivo.add_command(label="Ejecutar simulación de 22 operaciones", command=self.ver_simulacion)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self.destroy)
        barra.add_cascade(label="Archivo", menu=archivo)
        ayuda = tk.Menu(barra, tearoff=False)
        ayuda.add_command(label="Acerca de", command=lambda: messagebox.showinfo(
            "Software FJ", "Sistema de gestión de clientes, servicios y reservas.\n\nLos datos se guardan solo en "
            "memoria durante la sesión; únicamente los eventos y errores se escriben en el archivo de logs."))
        barra.add_cascade(label="Ayuda", menu=ayuda)
        self.config(menu=barra)

    def refrescar(self):
        """Actualiza todas las pestañas con los datos actuales."""
        for pestana in self.pestanas:
            pestana.refrescar()

    def ejecutar(self, accion, mensaje_ok: str):
        """Ejecuta una acción protegida: si falla informa y registra, pero la aplicación sigue viva.
        Devuelve el resultado (True si la acción no devuelve nada) o None si hubo error."""
        try:
            resultado = accion()
        except ErrorSoftwareFJ as error:
            causa = f" Causa: {error.__cause__}" if error.__cause__ else ""
            log.error(f"GUI: {error}{causa}")
            self.estado.set(f"Error: {error}")
            messagebox.showerror("No se pudo completar la operación", f"{error}{causa}")
            return None
        except Exception as error:
            log.critical(f"GUI: error inesperado {error!r}")
            self.estado.set("Error inesperado (ver pestaña Registro).")
            messagebox.showerror("Error inesperado", repr(error))
            return None
        else:
            if resultado is not False:
                self.estado.set(mensaje_ok)
            return True if resultado is None else resultado
        finally:
            self.refrescar()

    def cargar_demo(self):
        """Carga clientes, servicios y reservas de ejemplo."""
        def accion():
            g = self.gestor
            ana = g.registrar_cliente("Ana María Ruiz", "1082345678", "ana@correo.com", "3001234567")
            luis = g.registrar_cliente("Luis Pérez", "1098765432", "luis@correo.com", "3109876543")
            sala = g.agregar_servicio(ReservaSala("Sala Ejecutiva", 50000, 10))
            equipo = g.agregar_servicio(AlquilerEquipo("Proyector HD", 15000, "Proyector", 3))
            asesoria = g.agregar_servicio(AsesoriaEspecializada("Asesoría Cloud", 90000, "Cloud"))
            manana = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            g.crear_reserva(ana, sala, 2, manana, personas=6)
            g.crear_reserva(luis, equipo, 4, manana, 0.05, cantidad=2)
            g.crear_reserva(luis, asesoria, 1.5, manana.replace(hour=14), nivel="senior")
        self.ejecutar(accion, "Datos de demostración cargados.")

    def ver_simulacion(self):
        """Ejecuta la simulación (con su propio gestor) y muestra su salida en una ventana."""
        salida = io.StringIO()
        try:
            with redirect_stdout(salida):
                simulacion()
        except Exception as error:
            log.critical(f"GUI: fallo al ejecutar la simulación {error!r}")
            salida.write(f"\nLa simulación terminó con un error inesperado: {error!r}")
        ventana = tk.Toplevel(self)
        ventana.title("Resultado de la simulación (22 operaciones)")
        ventana.geometry("900x560")
        marco = ttk.Frame(ventana)
        marco.pack(fill="both", expand=True, padx=8, pady=8)
        texto = tk.Text(marco, wrap="word", font=("Courier", 9))
        scroll = ttk.Scrollbar(marco, orient="vertical", command=texto.yview)
        texto.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        texto.pack(side="left", fill="both", expand=True)
        texto.insert("end", salida.getvalue())
        texto.configure(state="disabled")
        self.estado.set("Simulación ejecutada. Sus eventos quedaron en el registro.")
        self.refrescar()


def iniciar() -> None:
    """Crea la ventana y arranca el ciclo de eventos."""
    App().mainloop()
