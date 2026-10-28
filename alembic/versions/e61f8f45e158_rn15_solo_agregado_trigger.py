"""rn15 solo-agregado-trigger

Revision ID: e61f8f45e158
Revises: 8a0885ca0494
Create Date: 2026-10-28 15:45:34.062889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e61f8f45e158'
down_revision: Union[str, Sequence[str], None] = '8a0885ca0494'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tablas protegidas por RN-15: solo agregado (INSERT permitido, UPDATE/DELETE rechazado).
_TABLAS_SOLO_AGREGADO = (
    "historial_estado_orden",
    "movimiento_stock",
    "historial_precio_repuesto",
)

_FUNCION_SOLO_AGREGADO = "fn_rechazar_update_delete_solo_agregado"


def upgrade() -> None:
    """Upgrade schema: crea funcion y disparadores RN-15 (solo agregado)."""
    op.execute(
        sa.text(
            f"""
            CREATE OR REPLACE FUNCTION {_FUNCION_SOLO_AGREGADO}()
            RETURNS trigger AS $$
            BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    RAISE EXCEPTION
                        'RN-15: la tabla % es de solo agregado; no se permiten UPDATE ni DELETE',
                        TG_TABLE_NAME;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )
    )

    for table in _TABLAS_SOLO_AGREGADO:
        op.execute(
            sa.text(
                f"""
                CREATE TRIGGER trg_{table}_solo_agregado
                BEFORE UPDATE OR DELETE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION {_FUNCION_SOLO_AGREGADO};
                """
            )
        )


def downgrade() -> None:
    """Downgrade schema: elimina disparadores y funcion RN-15."""
    for table in _TABLAS_SOLO_AGREGADO:
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{table}_solo_agregado ON {table};"))
    op.execute(sa.text(f"DROP FUNCTION IF EXISTS {_FUNCION_SOLO_AGREGADO}();"))
