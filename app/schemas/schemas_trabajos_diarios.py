from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


# ==================== ESQUEMAS DE LECTURA (Output) ====================
class TrabajoDiarioSchema(BaseModel):
    """Schema para lectura de un trabajo diario"""

    id: int
    fecha: date
    sitio_trabajo: str
    maquinaria_trabajada: Optional[str] = None
    trabajo_realizado: str

    foto_1: Optional[str] = None
    foto_2: Optional[str] = None
    foto_3: Optional[str] = None
    foto_4: Optional[str] = None
    foto_5: Optional[str] = None
    foto_6: Optional[str] = None
    foto_7: Optional[str] = None
    foto_8: Optional[str] = None

    created_at: date
    updated_at: date

    class Config:
        from_attributes = True


# ==================== ESQUEMAS DE INSERCIÓN (Input) ====================
class TrabajoDiarioCreate(BaseModel):
    """Schema para crear un nuevo trabajo diario"""

    fecha: date = Field(..., description="Fecha en que se realizó el trabajo")
    sitio_trabajo: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Lugar donde se realizó el trabajo",
    )
    maquinaria_trabajada: Optional[str] = Field(
        None, max_length=255, description="Maquinaria en la que se trabajó"
    )
    trabajo_realizado: str = Field(
        ..., min_length=10, description="Descripción detallada del trabajo realizado"
    )

    foto_1: Optional[str] = None
    foto_2: Optional[str] = None
    foto_3: Optional[str] = None
    foto_4: Optional[str] = None
    foto_5: Optional[str] = None
    foto_6: Optional[str] = None
    foto_7: Optional[str] = None
    foto_8: Optional[str] = None


# ==================== ESQUEMAS DE ACTUALIZACIÓN (PATCH/PUT) ====================
class TrabajoDiarioUpdate(BaseModel):
    """Schema para actualización parcial de un trabajo diario"""

    fecha: Optional[date] = None
    sitio_trabajo: Optional[str] = Field(None, min_length=3, max_length=255)
    maquinaria_trabajada: Optional[str] = Field(None, max_length=255)
    trabajo_realizado: Optional[str] = Field(None, min_length=10)

    foto_1: Optional[str] = None
    foto_2: Optional[str] = None
    foto_3: Optional[str] = None
    foto_4: Optional[str] = None
    foto_5: Optional[str] = None
    foto_6: Optional[str] = None
    foto_7: Optional[str] = None
    foto_8: Optional[str] = None


# ==================== ESQUEMA DE RESPUESTA DE LISTA ====================
class TrabajoDiarioListResponse(BaseModel):
    """Respuesta paginada de trabajos diarios"""

    success: bool = True
    total: int
    skip: int
    limit: int
    data: List[TrabajoDiarioSchema]

    class Config:
        from_attributes = True


# ==================== ESQUEMA PARA GENERACIÓN DE REPORTE WORD ====================
class ReporteWordRequest(BaseModel):
    """Request para generar reporte en Word de un trabajo específico"""

    trabajo_id: int = Field(..., description="ID del trabajo diario a reportar")

    class Config:
        json_schema_extra = {"example": {"trabajo_id": 1}}
