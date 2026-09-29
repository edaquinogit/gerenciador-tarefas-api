"""Perfis, setores e revogação de sessões; mantém contas e tarefas antigas."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "usuario", sa.Column("perfil", sa.String(), nullable=False, server_default="FUNCIONARIO")
    )
    op.add_column("usuario", sa.Column("setor", sa.String(), nullable=True))
    op.add_column(
        "usuario", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0")
    )


def downgrade():
    raise RuntimeError(
        "Reversão de perfis exige backup e plano de reconciliação. Consulte docs/migracao.md."
    )
