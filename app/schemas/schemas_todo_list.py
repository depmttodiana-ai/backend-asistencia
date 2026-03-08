from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


# ==================== ESQUEMAS DE LECTURA (Output) ====================
class TodoListSchema(BaseModel):
    """Schema para lectura de una tarea de la lista To-Do"""

    id: int
    fecha: date
    trabajo: str
    estado: str  # en espera, pausado, completado
    turno: Optional[str] = None
    supervisor_encargado: Optional[str] = None

    # Nuevas fechas
    fecha_inscripcion: date
    fecha_inicio_trabajo: Optional[date] = None
    fecha_finalizacion: Optional[date] = None

    # Observaciones (Reducido a 3)
    observacion_1: Optional[str] = None
    observacion_2: Optional[str] = None
    observacion_3: Optional[str] = None

    # Fotografías
    foto_1: Optional[str] = None
    foto_2: Optional[str] = None
    foto_3: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== ESQUEMAS DE INSERCIÓN (Input) ====================
class TodoListCreate(BaseModel):
    """Schema para crear una nueva tarea en la lista To-Do"""

    fecha: date = Field(default_factory=date.today, description="Fecha de la actividad")
    trabajo: str = Field(
        ..., min_length=3, description="Descripción de la labor de mantenimiento"
    )
    estado: str = Field(
        default="en espera",
        pattern="^(en espera|pausado|completado)$",
        description="Estado de la tarea",
    )
    turno: Optional[str] = Field(None, description="Turno de la actividad")
    supervisor_encargado: Optional[str] = Field(None, description="Supervisor a cargo del turno")

    # Nuevas fechas
    fecha_inscripcion: date = Field(default_factory=date.today)
    fecha_inicio_trabajo: Optional[date] = None
    fecha_finalizacion: Optional[date] = None

    # Observaciones y fotos
    observacion_1: Optional[str] = None
    observacion_2: Optional[str] = None
    observacion_3: Optional[str] = None

    foto_1: Optional[str] = None
    foto_2: Optional[str] = None
    foto_3: Optional[str] = None


# ==================== ESQUEMAS DE ACTUALIZACIÓN (PATCH/PUT) ====================
class TodoListUpdate(BaseModel):
    """Schema para actualización parcial de una tarea"""

    fecha: Optional[date] = None
    trabajo: Optional[str] = Field(None, min_length=3)
    estado: Optional[str] = Field(None, pattern="^(en espera|pausado|completado)$")
    turno: Optional[str] = None
    supervisor_encargado: Optional[str] = None

    fecha_inscripcion: Optional[date] = None
    fecha_inicio_trabajo: Optional[date] = None
    fecha_finalizacion: Optional[date] = None

    observacion_1: Optional[str] = None
    observacion_2: Optional[str] = None
    observacion_3: Optional[str] = None

    foto_1: Optional[str] = None
    foto_2: Optional[str] = None
    foto_3: Optional[str] = None


# ==================== ESQUEMA DE RESPUESTA DE LISTA ====================
class TodoListListResponse(BaseModel):
    """Respuesta paginada o listado de tareas To-Do"""

    success: bool = True
    total: int
    data: List[TodoListSchema]

    class Config:
        from_attributes = True
