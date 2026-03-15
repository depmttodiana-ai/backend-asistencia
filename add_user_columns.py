from app.core.database import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255);"))
            print("Columna 'email' agregada.")
        except Exception as e:
            print(f"Error agregando 'email': {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN reset_password_token VARCHAR(255);"))
            print("Columna 'reset_password_token' agregada.")
        except Exception as e:
            print(f"Error agregando 'reset_password_token': {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN reset_password_expires TIMESTAMP;"))
            print("Columna 'reset_password_expires' agregada.")
        except Exception as e:
            print(f"Error agregando 'reset_password_expires': {e}")
            
        conn.commit()

if __name__ == "__main__":
    run_migration()
