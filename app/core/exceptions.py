"""Errores de aplicación y handlers HTTP uniformes."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Error de negocio con un código HTTP asociado."""

    status_code = 400

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NoEncontrado(AppError):
    status_code = 404


class Conflicto(AppError):
    status_code = 409


class Invalido(AppError):
    status_code = 422


def _sqlstate(exc: IntegrityError) -> str | None:
    orig = getattr(exc, "orig", None)
    state = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    if state is None and orig is not None:
        nested = getattr(orig, "orig", None)
        state = getattr(nested, "sqlstate", None) or getattr(nested, "pgcode", None)
    return state


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    state = _sqlstate(exc)
    if state == "23505":
        return JSONResponse(
            status_code=409,
            content={"detail": "Ya existe un registro con esos datos"},
        )
    if state == "23503":
        return JSONResponse(
            status_code=409,
            content={"detail": "La operación entra en conflicto con datos relacionados"},
        )
    if state in {"23502", "23514"}:
        return JSONResponse(
            status_code=422,
            content={"detail": "Los datos enviados no cumplen una restricción"},
        )
    logger.exception("Error de integridad no mapeado", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error inesperado"},
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error inesperado"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
