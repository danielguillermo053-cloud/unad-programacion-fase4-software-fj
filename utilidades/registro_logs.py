"""Registro de eventos y errores en un archivo de logs (único uso de archivos del sistema)."""

import logging
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVO_LOG = os.path.join(RAIZ, "logs", "software_fj.log")


def _crear_logger() -> logging.Logger:
    os.makedirs(os.path.dirname(ARCHIVO_LOG), exist_ok=True)
    logger = logging.getLogger("software_fj")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        manejador = logging.FileHandler(ARCHIVO_LOG, mode="a", encoding="utf-8")
        manejador.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
        logger.addHandler(manejador)
    return logger


log = _crear_logger()
