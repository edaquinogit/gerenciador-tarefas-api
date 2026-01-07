from sqlmodel import Session, select
from database import engine
import os
from models import Usuario
from security import gerar_hash_senha

def reset_total():
    # 1. Forçamos o fechamento do banco para evitar erro de arquivo aberto
    print("🔄 Reiniciando banco de dados...")
    if os.path.exists("database.db"):
        try:
            os.remove("database.db")
        except:
            print("❌ FECHE O UVICORN E O STREAMLIT ANTES!")
            return

    # 2. Recriamos as tabelas (importante importar models aqui)
    import models
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

    # 3. Criamos o admin com uma senha SIMPLES para teste
    with Session(engine) as session:
        senha_limpa = "admin123"  # <--- SUA SENHA SERÁ ESTA
        hash_correto = gerar_hash_senha(senha_limpa)
        
        admin = Usuario(
            username="admin",
            email="admin@teste.com",
            password_hash=hash_correto,
            is_active=True,
            is_admin=True
        )
        session.add(admin)
        session.commit()
        
    print(f"✅ BANCO RESETADO!")
    print(f"👤 Usuário: admin")
    print(f"🔑 Senha: {senha_limpa}")

if __name__ == "__main__":
    reset_total()