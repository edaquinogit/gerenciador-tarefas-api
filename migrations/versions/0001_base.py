"""Baseline equivalente ao schema anterior; bancos existentes exigem adoção validada."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_usuario_username", "usuario", ["username"], unique=True)
    op.create_table(
        "tarefa",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("prioridade", sa.String(), nullable=False),
        sa.Column("concluido", sa.Boolean(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
    )


def downgrade():
    raise RuntimeError(
        "Baseline contém dados de usuários e tarefas. Restaure um backup validado para reverter."
    )
