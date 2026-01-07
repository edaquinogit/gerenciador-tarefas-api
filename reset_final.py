from sqlmodel import Session, SQLModel
from database import engine
from models import Usuario
from security import gerar_hash_senha
import os

# Força a criação do admin exatamente como o security.py espera
def reset_absoluto():
    if os.path.exists("database.db"):
        os.remove("database.db")
    
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Vamos usar uma senha simples para garantir: admin
        senha_limpa = "admin" 
        novo_admin = Usuario(
            username="admin",
            email="admin@admin.com",
            password_hash=gerar_hash_senha(senha_limpa),
            is_active=True,
            is_admin=True
        )
        session.add(novo_admin)
        session.commit()
    print("🚀 Banco resetado e usuário 'admin' criado com senha 'admin'")

if __name__ == "__main__":
    reset_absoluto()