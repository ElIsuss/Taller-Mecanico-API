"""Verificación de que los routers quedan documentados en OpenAPI (C-03)."""

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_docs_responde(client):
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_incluye_los_recursos(client):
    response = await client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    for path in (
        "/clientes",
        "/vehiculos",
        "/repuestos",
        "/ordenes",
        "/estados-orden",
    ):
        assert path in spec["paths"]
    tags = {
        tag
        for operations in spec["paths"].values()
        for operation in operations.values()
        for tag in operation.get("tags", [])
    }
    assert {"clientes", "vehiculos", "repuestos", "ordenes", "estados-orden"} <= tags
