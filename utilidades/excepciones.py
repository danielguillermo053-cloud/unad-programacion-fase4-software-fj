"""Excepciones personalizadas de Software FJ (todas heredan de ErrorSoftwareFJ)."""


class ErrorSoftwareFJ(Exception):
    """Base común: permite capturar cualquier error propio con un solo except."""


class ClienteInvalidoError(ErrorSoftwareFJ):
    """Datos de cliente que no cumplen las validaciones."""


class ServicioInvalidoError(ErrorSoftwareFJ):
    """Servicio creado o configurado con parámetros incorrectos."""


class ServicioNoDisponibleError(ErrorSoftwareFJ):
    """Se intentó usar un servicio no disponible."""


class ParametroFaltanteError(ErrorSoftwareFJ):
    """Falta un parámetro obligatorio en una operación."""


class ReservaInvalidaError(ErrorSoftwareFJ):
    """La reserva no se puede crear o procesar."""


class OperacionNoPermitidaError(ErrorSoftwareFJ):
    """Operación no válida para el estado actual."""


class CalculoInconsistenteError(ErrorSoftwareFJ):
    """Un cálculo de costos dio un resultado inconsistente."""


class ConflictoHorarioError(ErrorSoftwareFJ):
    """El servicio no tiene cupo en el horario pedido."""
