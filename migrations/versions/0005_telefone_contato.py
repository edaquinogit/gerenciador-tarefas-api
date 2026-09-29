"""Telefone como contato; e-mails legados preservados sem obrigatoriedade."""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("usuario") as batch:
        batch.add_column(sa.Column("telefone", sa.String(), nullable=True))
        batch.alter_column("email", existing_type=sa.String(), nullable=True)


def downgrade():
    raise RuntimeError("Downgrade destrutivo recusado. Restaure backup e código compatível.")
