"""categoria automatica nas ordens"""

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ordem") as batch:
        batch.add_column(
            sa.Column(
                "categoria",
                sqlmodel.sql.sqltypes.AutoString(),
                nullable=False,
                server_default="OUTROS",
            )
        )
        batch.create_index(op.f("ix_ordem_categoria"), ["categoria"], unique=False)


def downgrade():
    raise RuntimeError("Categorias operacionais não devem ser apagadas. Restaure backup validado.")
