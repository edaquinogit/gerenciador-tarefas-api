"""Schema imutável anterior às migrações, usado somente para adoção validada."""

import sqlalchemy as sa

metadata = sa.MetaData()
sa.Table(
    "usuario",
    metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("username", sa.String(), nullable=False, unique=True, index=True),
    sa.Column("email", sa.String(), nullable=False, unique=True),
    sa.Column("password_hash", sa.String(), nullable=False),
    sa.Column("is_active", sa.Boolean(), nullable=False),
)
sa.Table(
    "tarefa",
    metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("titulo", sa.String(), nullable=False),
    sa.Column("prioridade", sa.String(), nullable=False),
    sa.Column("concluido", sa.Boolean(), nullable=False),
    sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
)
