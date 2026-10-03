"""Autorizacao individual de senha e recuperacao de avisos ausentes."""

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "autorizacaosenha",
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), primary_key=True),
        sa.Column("status", sqlmodel.AutoString(), nullable=False),
        sa.Column("solicitado_em", sa.DateTime(), nullable=False),
        sa.Column("decidido_em", sa.DateTime()),
        sa.Column("expira_em", sa.DateTime()),
        sa.Column("consumido_em", sa.DateTime()),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("usuario.id")),
        sa.Column("versao", sa.Integer(), nullable=False),
    )
    # Preserva avisos lidos e histórico; recupera apenas os destinatários ausentes.
    # Avisos legados para coleta permanecem armazenados, porém a API não os expõe.
    op.execute(
        sa.text("""
        INSERT INTO notificacao (evento_id, ordem_id, usuario_id, mensagem, criado_em, lida_em)
        SELECT e.id, o.id, u.id,
               'Ordem #' || o.id || ' ficou pronta: ' || o.quantidade || ' ' || o.unidade || ' de ' || o.produto || '.',
               e.criado_em, NULL
        FROM eventoordem e
        JOIN ordem o ON o.id = e.ordem_id
        JOIN usuario u ON (u.id = o.solicitante_id OR u.perfil = 'ADMIN')
        WHERE e.acao = 'ETAPA' AND e.status_novo = 'PRONTO' AND u.is_active = true
          AND NOT EXISTS (
              SELECT 1 FROM notificacao n WHERE n.evento_id = e.id AND n.usuario_id = u.id
          )
    """)
    )


def downgrade():
    raise RuntimeError("Permissões e avisos preservam histórico. Restaure um backup validado.")
