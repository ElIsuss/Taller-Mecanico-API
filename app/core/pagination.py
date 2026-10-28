"""Paginación uniforme para los listados de la API."""

from math import ceil
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

from app.core.exceptions import Invalido

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    """Envoltorio de respuesta para listados paginados."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class PaginaParams:
    """Parámetros de paginación comunes (dependencia de FastAPI)."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=100),
    ) -> None:
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


def calcular_pages(total: int, size: int) -> int:
    """Cantidad de páginas; 0 cuando no hay elementos."""
    if total <= 0:
        return 0
    return ceil(total / size)


def construir_pagina(
    items: list[T],
    total: int,
    params: PaginaParams,
) -> Pagina[T]:
    """Arma la página y rechaza números de página fuera de rango."""
    pages = calcular_pages(total, params.size)
    if params.page > max(pages, 1):
        raise Invalido("La página solicitada está fuera de rango")
    return Pagina(
        items=items,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )
