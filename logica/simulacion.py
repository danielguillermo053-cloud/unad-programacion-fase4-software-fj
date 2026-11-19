"""Simulación de 22 operaciones válidas e inválidas (modo consola o desde el menú de la interfaz)."""

from logica.gestor import GestorSoftwareFJ
from modelos import AlquilerEquipo, AsesoriaEspecializada, ReservaSala
from utilidades.excepciones import ErrorSoftwareFJ
from utilidades.registro_logs import ARCHIVO_LOG, log


def ejecutar(numero: int, titulo: str, accion):
    """Ejecuta una operación protegida: si falla, registra el error y la simulación continúa."""
    print(f"\n[{numero:02d}] {titulo}")
    try:
        resultado = accion()
    except ErrorSoftwareFJ as error:
        causa = f" | Causa: {error.__cause__}" if error.__cause__ else ""
        print(f"     X ERROR CONTROLADO: {error}{causa}")
        log.error(f"Operación {numero} ({titulo}): {error}{causa}")
    except Exception as error:
        print(f"     X ERROR INESPERADO: {error!r}")
        log.critical(f"Operación {numero} ({titulo}): error inesperado {error!r}")
    else:
        print(f"     OK: {resultado}")
        return resultado
    finally:
        log.info(f"Operación {numero} finalizada.")


def simulacion() -> None:
    g = GestorSoftwareFJ()
    print("=== SIMULACIÓN SOFTWARE FJ ===")

    ana = ejecutar(1, "Registro válido de cliente",
                   lambda: g.registrar_cliente("ana maría ruiz", "1082345678", "ana@correo.com", "3001234567"))
    ejecutar(2, "Registro inválido: correo mal formado",
             lambda: g.registrar_cliente("Luis Pérez", "1098765432", "luis-correo.com", "3109876543"))
    luis = ejecutar(3, "Registro válido de cliente",
                    lambda: g.registrar_cliente("Luis Pérez", "1098765432", "luis@correo.com", "3109876543"))
    ejecutar(4, "Registro inválido: documento con letras",
             lambda: g.registrar_cliente("Marta Gil", "12AB56", "marta@correo.com", "3201112233"))
    ejecutar(5, "Registro inválido: documento repetido",
             lambda: g.registrar_cliente("Otra Ana", "1082345678", "otra@correo.com", "3001112222"))

    sala = ejecutar(6, "Creación válida de sala",
                    lambda: g.agregar_servicio(ReservaSala("Sala Ejecutiva", 50000, 10)))
    ejecutar(7, "Creación inválida: tarifa negativa",
             lambda: g.agregar_servicio(AlquilerEquipo("Portátil Pro", -20000, "Portátil", 4)))
    equipo = ejecutar(8, "Creación válida de equipo (inventario de 3 unidades)",
                      lambda: g.agregar_servicio(AlquilerEquipo("Proyector HD", 15000, "Proyector", 3)))
    asesoria = ejecutar(9, "Creación válida de asesoría",
                        lambda: g.agregar_servicio(AsesoriaEspecializada("Asesoría Cloud", 90000, "Cloud")))

    r1 = ejecutar(10, "Reserva exitosa de sala (4 personas, 2 h)", lambda: g.crear_reserva(ana, sala, 2, personas=4))
    ejecutar(11, "Reserva fallida: 25 personas exceden la capacidad (error encadenado)",
             lambda: g.crear_reserva(luis, sala, 2, personas=25))
    ejecutar(12, "Reserva fallida: falta el parámetro 'cantidad'", lambda: g.crear_reserva(luis, equipo, 5))
    r2 = ejecutar(13, "Reserva exitosa de asesoría senior (3 h)",
                  lambda: g.crear_reserva(luis, asesoria, 3, nivel="senior"))
    ejecutar(14, "Reserva fallida: la sala ya está ocupada en ese horario",
             lambda: g.crear_reserva(luis, sala, 1, personas=2))
    ejecutar(15, "Reserva fallida: 5 unidades superan el inventario de 3",
             lambda: g.crear_reserva(luis, equipo, 2, cantidad=5))

    ejecutar(16, "Confirmar y procesar reserva de sala (base + IVA)", lambda: (r1.confirmar(), r1.procesar())[1])
    ejecutar(17, "Procesar asesoría SIN confirmar (operación no permitida)", lambda: r2.procesar())
    ejecutar(18, "Confirmar y procesar asesoría con 10 % de descuento", lambda: (r2.confirmar(), r2.procesar(0.10))[1])
    ejecutar(19, "Cancelar una reserva ya procesada (no permitido)", lambda: r1.cancelar())
    ejecutar(20, "Cálculo inconsistente: descuento del 150 %", lambda: asesoria.calcular_costo(2, 1.5, nivel="junior"))
    ejecutar(21, "Reservar un servicio no disponible",
             lambda: (g.cambiar_disponibilidad(equipo), g.crear_reserva(ana, equipo, 4, cantidad=2))[1])
    ejecutar(22, "Dato de tipo incorrecto (duración como texto)", lambda: g.crear_reserva(ana, sala, "dos", personas=3))

    datos = g.resumen()
    print(f"\n=== RESUMEN ===\nClientes: {datos['clientes']} | Servicios: {datos['servicios']} | "
          f"Reservas: {len(g.reservas)} | Ingresos: ${datos['ingresos']:,.2f}")
    for reserva in g.reservas:
        print(" -", reserva)
    print(f"\nEl sistema terminó sin interrupciones. Log en: {ARCHIVO_LOG}")
