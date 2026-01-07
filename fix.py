from sqlmodel import Session, SQLModel
from database import engine
from models import Usuario
from security import gerar_hash_senha
import os

# 1. Deletar banco
if os.path.exists("database.db"):
    os.remove("database.db")

# 2. Criar tabelas
from models import Usuario, Tarefa
SQLModel.metadata.create_all(engine)

# 3. Criar Admin
with Session(engine) as session:
    senha_teste = "admin"
    hash_seguro = gerar_hash_senha(senha_teste)
    
    admin = Usuario(
        username="admin",
        email="admin@admin.com",
        password_hash=hash_seguro,
        is_active=True,
        is_admin=True
    )
    session.add(admin)
    session.commit()
    print(f"✅ Sucesso! Admin criado com a senha: {senha_teste}")
    print(f"🔐 Hash gerado no banco: {hash_seguro}")