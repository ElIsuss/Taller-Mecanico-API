from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clientes.models import Cliente
from app.modules.clientes.repository import ClienteRepository
from app.modules.clientes.unit_of_work import ClienteUnitOfWork
from app.modules.repuestos.models import Repuesto
from app.modules.repuestos.service import registrar_movimiento_stock


@pytest.mark.asyncio
async def test_domain_uow_commits_shared_session_on_success() -> None:
    session = AsyncMock(spec=AsyncSession)
    uow = ClienteUnitOfWork(session=session)

    assert uow.clientes.session is session
    assert uow.vehiculos.session is session
    assert uow.usuarios.session is session

    async with uow:
        pass

    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_domain_uow_rolls_back_shared_session_on_error() -> None:
    session = AsyncMock(spec=AsyncSession)
    uow = ClienteUnitOfWork(session=session)

    with pytest.raises(RuntimeError, match="transaction failed"):
        async with uow:
            raise RuntimeError("transaction failed")

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_repository_save_flushes_without_committing() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    repository = ClienteRepository(session)
    cliente = Cliente(nombre="Test", documento="DOC-1", telefono="")

    await repository.save(cliente)

    session.add.assert_called_once_with(cliente)
    session.flush.assert_awaited_once()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_repository_without_session_fails_explicitly() -> None:
    repository = ClienteRepository(None)

    with pytest.raises(RuntimeError, match="Repository session is not available"):
        await repository.get_by_id(1)


@pytest.mark.asyncio
async def test_stock_change_is_recorded_through_the_shared_movement_operation() -> None:
    uow = Mock()
    uow.movimientos_stock.add = AsyncMock()
    uow.flush = AsyncMock()
    repuesto = Repuesto(
        id=1,
        codigo="REP-1",
        descripcion="Repuesto de prueba",
        precio=Decimal("10.00"),
        stock=5,
    )

    movimiento = await registrar_movimiento_stock(
        uow,
        repuesto,
        cantidad=-2,
        motivo="terminación",
        usuario_id=7,
        orden_id=12,
    )

    assert repuesto.stock == 3
    assert movimiento.repuesto_id == repuesto.id
    assert movimiento.orden_id == 12
    assert movimiento.cantidad == -2
    uow.movimientos_stock.add.assert_awaited_once_with(movimiento)
    uow.flush.assert_awaited_once()
