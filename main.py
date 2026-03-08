from fastapi import FastAPI
from app.core.database import engine
from app.models import models
from app.models import models_empleados
from app.models import models_trabajos_diarios
from app.controllers import (
    asistencia,
    empleados,
    administrativos,
    reportes,
    pdf_reportes,
    auth,
    reportes_word,
    orden_de_trabajo,
    todo_list,
)

from sqlalchemy import text

from app.models import models_ordenes_trabajo
from app.models import models_todo_list

# Crear tablas (solo para desarrollo, en prod usar Alembic)
models.Base.metadata.create_all(bind=engine)
models_empleados.Base.metadata.create_all(bind=engine)
models_trabajos_diarios.Base.metadata.create_all(bind=engine)
models_ordenes_trabajo.Base.metadata.create_all(bind=engine)
models_todo_list.Base.metadata.create_all(bind=engine)

# Generar Vista de Base de Datos para Reportes
with engine.connect() as conn:
    # Eliminamos la vista primero para evitar errores de cambio de estructura en PostgreSQL
    conn.execute(text("DROP VIEW IF EXISTS vw_reporte_asistencia_completo;"))

    conn.execute(
        text("""
        CREATE VIEW vw_reporte_asistencia_completo AS
        SELECT 
            a.id,
            e.id AS id_empleado,
            a.fecha,
            e.codigo,
            e.nombre,
            e.apellido,
            e.cargo,
            e.fecha_ingreso,
            t.nombre AS turno,
            a.estado,
            CASE 
                WHEN a.estado = 'V' THEN 'Presente'
                WHEN a.estado = 'X' THEN 'Falta'
                ELSE a.estado 
            END AS estado_detalle,
            CASE WHEN f.fecha IS NOT NULL THEN 'SÍ' ELSE 'NO' END AS es_feriado,
            f.descripcion AS descripcion_feriado
        FROM empleados e
        JOIN asistencia a ON e.id = a.empleado_id
        LEFT JOIN turnos t ON a.turno_id = t.id
        LEFT JOIN feriados f ON a.fecha = f.fecha;
    """)
    )
    conn.commit()

from fastapi.middleware.cors import CORSMiddleware
# import os (eliminado por desuso)

app = FastAPI(
    title="API Palmeras Diana - Sistema de Mantenimiento",
    description="API REST para gestión de empleados, asistencia y mantenimiento",
    version="1.0.0",
)

# Configuración de CORS
origins = [
    "https://mtto-diana-asistencia.netlify.app",  # Producción
    "http://localhost:5173",  # Desarrollo local (Vite)
    "http://127.0.0.1:5173",  # Variante local
    "http://192.168.1.13:5173",  # Acceso local por IP (para probar desde móvil)
    "http://192.168.1.13:8000",  # El mismo backend por IP
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Los archivos se gestionan ahora a través de Cloudinary. No es necesario montar carpetas locales.

# Importar e incluir los Routers (Controladores)
app.include_router(asistencia.router, tags=["Asistencia"])
app.include_router(empleados.router, tags=["Empleados"])
app.include_router(administrativos.router, tags=["Administrativos"])
app.include_router(reportes.router, prefix="/reportes", tags=["Reportes Excel"])
app.include_router(pdf_reportes.router, prefix="/pdf-reportes", tags=["Reportes PDF"])
app.include_router(auth.router, tags=["Autenticación"])
app.include_router(reportes_word.router, tags=["Trabajos Diarios y Reportes Word"])
app.include_router(orden_de_trabajo.router, tags=["Órdenes de Trabajo"])
app.include_router(todo_list.router, tags=["To-Do List Mantenimiento"])


@app.get("/")
def root():
    return {"message": "Backend Palmeras Diana Activo - Estructura MVC"}
