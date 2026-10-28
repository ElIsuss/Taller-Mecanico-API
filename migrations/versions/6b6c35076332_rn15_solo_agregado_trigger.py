"""rn15 solo agregado trigger

Revision ID: 6b6c35076332
Revises: 92c8c4836886
Create Date: 2026-10-28 16:46:49.282322

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b6c35076332'
down_revision: Union[str, Sequence[str], None] = '92c8c4836886'
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
        # Sin ';' final: asyncpg prepara el statement y rechaza el terminador
        # que sí tolera psql. Lo mismo aplica al downgrade.
        # La lista de argumentos '()' es obligatoria en EXECUTE FUNCTION.
        op.execute(
            sa.text(
                f"""
                CREATE TRIGGER trg_{table}_solo_agregado
                BEFORE UPDATE OR DELETE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION {_FUNCION_SOLO_AGREGADO}()
                """
            )
        )


def downgrade() -> None:
    """Downgrade schema: elimina disparadores y funcion RN-15."""
    for table in _TABLAS_SOLO_AGREGADO:
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{table}_solo_agregado ON {table}"))
    op.execute(sa.text(f"DROP FUNCTION IF EXISTS {_FUNCION_SOLO_AGREGADO}()"))
