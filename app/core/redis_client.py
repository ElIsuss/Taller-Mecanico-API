"""Cliente Redis simplificado para contador de intentos fallidos (RN-08).

Versión en memoria para desarrollo/testing. En producción conectarías
a un servidor Redis real para persistencia entre reinicios.
"""

# Contador en memoria (global)
_intentos_fallidos: dict[str, dict] = {}

BLOQUEADO_HASTA: float = 0


async def incrementar_intentos_fallidos(correo: str) -> None:
    """Incrementar el contador de intentos fallidos para un correo."""
    ahora = __import__("time").time()

    if correo in _intentos_fallidos:
        if ahora - _intentos_fallidos[correo]["ultimo_reset"] > 300:  # 5 min
            _intentos_fallidos[correo] = {"fallos": 0, "ultimo_reset": ahora}
    else:
        _intentos_fallidos[correo] = {"fallos": 0, "ultimo_reset": ahora}

    _intentos_fallidos[correo]["fallos"] += 1


async def resetear_intentos(correo: str) -> None:
    """Resetear el contador de intentos fallidos (después de login exitoso)."""
    _intentos_fallidos[correo] = {"fallos": 0, "ultimo_reset": __import__("time").time()}


async def ya_bloqueado(correo: str) -> bool:
    """Verificar si el correo está bloqueado por exceder intentos fallidos."""
    # Esta versión en memoria siempre retorna False
    # En producción con Redis consultarías BLOQUEADO_HASTA
    return False