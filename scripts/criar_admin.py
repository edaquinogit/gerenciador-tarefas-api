from sqlmodel import Session, select
from database import engine, create_db_and_tabelas 
from models import Usuario
from security import pwd_context

def criar_admin_oficial():
    # Garante que o arquivo .db e as tabelas existam
    create_db_and_tabelas()
    
    with Session(engine) as session:
        # Busca se já existe o admin
        statement = select(Usuario).where(Usuario.username == "admin")
        existente = session.exec(statement).first()
        
        if existente:
            print("ℹ️ O usuário 'admin' já existe no banco.")
        else:
            senha_hash = pwd_context.hash("123456")
            novo_usuario = Usuario(
                username="admin",
                email="admin@exemplo.com",  # Adicionamos o e-mail aqui 📧
                password_hash=senha_hash
            )
            session.add(novo_usuario)
            session.commit()
            print("✅ Sucesso! Usuário 'admin' criado com o e-mail 'admin@exemplo.com'")

if __name__ == "__main__":
    criar_admin_oficial()