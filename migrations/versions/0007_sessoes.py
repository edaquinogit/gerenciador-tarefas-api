"""Sessoes revogaveis e recuperacao de navegacao."""

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sessao",
        sa.Column("id", sqlmodel.AutoString(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("expira_em", sa.DateTime(), nullable=False),
        sa.Column("revogada", sa.Boolean(), nullable=False),
        sa.Column("cookie_hash", sqlmodel.AutoString(), unique=True),
        sa.Column("codigo_hash", sqlmodel.AutoString(), unique=True),
        sa.Column("codigo_expira_em", sa.DateTime(), nullable=False),
        sa.Column("estado", sqlmodel.AutoString(), nullable=False),
    )
    op.create_index("ix_sessao_usuario_id", "sessao", ["usuario_id"])


def downgrade():
    raise RuntimeError("Sessoes nao devem ser apagadas em uso. Restaure um backup validado.")
