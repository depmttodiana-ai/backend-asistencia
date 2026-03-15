from app.core.database import engine
from sqlalchemy import text

def run_migration_names():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN nombre VARCHAR(100);"))
            print("Columna 'nombre' agregada.")
        except Exception as e:
            print(f"Error agregando 'nombre': {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN apellido VARCHAR(100);"))
            print("Columna 'apellido' agregada.")
        except Exception as e:
            print(f"Error agregando 'apellido': {e}")
            
        conn.commit()

if __name__ == "__main__":
    run_migration_names()
