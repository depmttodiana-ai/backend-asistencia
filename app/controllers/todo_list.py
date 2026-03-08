from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    Form,
    File,
    UploadFile,
)
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import date
import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

from app.core.database import get_db
from app.core.auth_deps import any_auth
from app.models.models_todo_list import TodoList
from app.schemas.schemas_todo_list import (
    TodoListSchema,
    TodoListUpdate,
    TodoListListResponse,
)

# Cargar configuración de Cloudinary
load_dotenv()
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

router = APIRouter(
    prefix="/todo-list",
    tags=["To-Do List Mantenimiento"],
)

# ==================== RUTAS GET ====================


@router.get("/", response_model=TodoListListResponse, dependencies=[Depends(any_auth)])
def get_todo_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    fecha: Optional[date] = Query(None, description="Filtrar por fecha específica"),
    estado: Optional[str] = Query(
        None, description="Filtrar por estado (en espera, pausado, completado)"
    ),
    db: Session = Depends(get_db),
):
    """
    Obtiene la lista de tareas de mantenimiento con filtros opcionales.
    Cualquier usuario autenticado puede ver la lista.
    """
    query = db.query(TodoList)

    if fecha:
        query = query.filter(TodoList.fecha == fecha)
    if estado:
        query = query.filter(TodoList.estado == estado)

    total = query.count()
    tareas = (
        query.order_by(desc(TodoList.fecha), desc(TodoList.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return TodoListListResponse(success=True, total=total, data=tareas)


@router.get(
    "/{task_id}", response_model=TodoListSchema, dependencies=[Depends(any_auth)]
)
def get_task_by_id(task_id: int, db: Session = Depends(get_db)):
    """Obtiene una tarea específica por su ID."""
    task = db.query(TodoList).filter(TodoList.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


# ==================== RUTAS POST ====================


@router.post(
    "/",
    response_model=TodoListSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(any_auth)],
)
def create_task(
    fecha: date = Form(...),
    trabajo: str = Form(...),
    estado: str = Form("en espera"),
    fecha_inscripcion: date = Form(default=date.today()),
    turno: Optional[str] = Form(None),
    supervisor_encargado: Optional[str] = Form(None),
    fecha_inicio_trabajo: Optional[date] = Form(None),
    fecha_finalizacion: Optional[date] = Form(None),
    observacion_1: Optional[str] = Form(None),
    observacion_2: Optional[str] = Form(None),
    observacion_3: Optional[str] = Form(None),
    fotos: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Crea una nueva tarea en la lista de mantenimiento mediante FORMULARIO.
    Permite subir hasta 3 imágenes directamente a CLOUDINARY.
    """

    # 1. Procesar imágenes si existen
    rutas_fotos = []
    if fotos:
        for i, foto in enumerate(fotos):
            if i >= 3:
                break  # Máximo 3 fotos según requerimiento actual

            try:
                # Leer y subir a Cloudinary
                content = foto.file.read()
                response = cloudinary.uploader.upload(
                    content, folder="todo_list_mantenimiento"
                )
                rutas_fotos.append(response.get("secure_url"))
            except Exception as e:
                print(f"Error subiendo foto {foto.filename} a Cloudinary: {e}")
                rutas_fotos.append(None)

    # Rellenar lista para mapeo a BD
    while len(rutas_fotos) < 3:
        rutas_fotos.append(None)

    # 2. Crear objeto en BD
    nueva_tarea = TodoList(
        fecha=fecha,
        trabajo=trabajo,
        estado=estado,
        turno=turno,
        supervisor_encargado=supervisor_encargado,
        fecha_inscripcion=fecha_inscripcion,
        fecha_inicio_trabajo=fecha_inicio_trabajo,
        fecha_finalizacion=fecha_finalizacion,
        observacion_1=observacion_1,
        observacion_2=observacion_2,
        observacion_3=observacion_3,
        foto_1=rutas_fotos[0],
        foto_2=rutas_fotos[1],
        foto_3=rutas_fotos[2],
    )

    try:
        db.add(nueva_tarea)
        db.commit()
        db.refresh(nueva_tarea)
        return nueva_tarea
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error al crear la tarea: {str(e)}"
        )


# ==================== RUTAS PATCH (Actualización Parcial) ====================


@router.patch(
    "/{task_id}", response_model=TodoListSchema, dependencies=[Depends(any_auth)]
)
def update_task(task_id: int, task_data: TodoListUpdate, db: Session = Depends(get_db)):
    """
    Actualiza parcialmente una tarea.
    Se actualizará el campo 'updated_at' automáticamente.
    """
    task = db.query(TodoList).filter(TodoList.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    update_data = task_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(task, key, value)

    try:
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error al actualizar la tarea: {str(e)}"
        )


# ==================== RUTAS DELETE ====================


@router.delete(
    "/{task_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(any_auth)]
)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Elimina una tarea de la lista."""
    task = db.query(TodoList).filter(TodoList.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    try:
        db.delete(task)
        db.commit()
        return {"success": True, "message": "Tarea eliminada correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error al eliminar la tarea: {str(e)}"
        )
