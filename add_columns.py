from app.core.database import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE todo_list ADD COLUMN turno VARCHAR(50);"))
            print("Columna 'turno' agregada.")
        except Exception as e:
            print(f"Error agregando 'turno': {e}")
            
        try:
            conn.execute(text("ALTER TABLE todo_list ADD COLUMN supervisor_encargado VARCHAR(100);"))
            print("Columna 'supervisor_encargado' agregada.")
        except Exception as e:
            print(f"Error agregando 'supervisor_encargado': {e}")
            
        conn.commit()

if __name__ == "__main__":
    run_migration()
