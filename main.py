"""Punto de entrada de Software FJ.

    python main.py            -> abre la aplicación (interfaz gráfica)
    python main.py --consola  -> ejecuta la simulación de 22 operaciones por consola
"""

import sys

from utilidades.registro_logs import log


def main() -> None:
    if "--consola" in sys.argv[1:]:
        from logica.simulacion import simulacion
        log.info("Inicio en modo consola.")
        simulacion()
    else:
        from interfaz import iniciar
        log.info("Inicio en modo gráfico.")
        iniciar()


if __name__ == "__main__":
    main()
