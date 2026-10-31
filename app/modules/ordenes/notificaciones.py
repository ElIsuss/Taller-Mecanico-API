"""Avisos al cliente que se ejecutan después de enviar la respuesta HTTP."""

import logging

logger = logging.getLogger("taller.avisos")


def enviar_aviso_cliente(orden_id: int, cliente: str, estado: str) -> None:
    """Registra el aviso al cliente fuera del ciclo de la petición."""
    logger.warning(
        "Aviso enviado al cliente %s: orden %s %s",
        cliente,
        orden_id,
        estado,
    )
