"""
Schemas de validación para Órdenes de Trabajo

Proporciona validación Pydantic para:
- Creación de órdenes
- Actualización de órdenes
- Respuestas del API
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TrabajoItem(BaseModel):
    """
    Representa un trabajo individual dentro de la orden diaria
    """

    a_realizar: Optional[str] = Field(
        None, description="Trabajo planificado a realizar"
    )
    realizado: Optional[str] = Field(
        None, description="Trabajo efectivamente realizado"
    )


class OrdenTrabajoCreate(BaseModel):
    """
    Schema para crear una nueva orden de trabajo diaria
    """

    fecha: date = Field(..., description="Fecha del trabajo")

    # Trabajos (hasta 5)
    trabajo_1_a_realizar: Optional[str] = Field(None, max_length=5000)
    trabajo_1_realizado: Optional[str] = Field(None, max_length=5000)

    trabajo_2_a_realizar: Optional[str] = Field(None, max_length=5000)
    trabajo_2_realizado: Optional[str] = Field(None, max_length=5000)

    trabajo_3_a_realizar: Optional[str] = Field(None, max_length=5000)
    trabajo_3_realizado: Optional[str] = Field(None, max_length=5000)

    trabajo_4_a_realizar: Optional[str] = Field(None, max_length=5000)
    trabajo_4_realizado: Optional[str] = Field(None, max_length=5000)

    trabajo_5_a_realizar: Optional[str] = Field(None, max_length=5000)
    trabajo_5_realizado: Optional[str] = Field(None, max_length=5000)

    @field_validator("fecha")
    @classmethod
    def validar_fecha_no_futura(cls, v: date) -> date:
        """Validar que la fecha no sea mayor que hoy"""
        if v > date.today():
            raise ValueError("La fecha no puede ser superior a la fecha actual")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "fecha": "2026-02-08",
                "trabajo_1_a_realizar": "Mantenimiento preventivo del compresor",
                "trabajo_1_realizado": "Se realizó cambio de aceite y limpieza de filtros",
                "trabajo_2_a_realizar": "Inspección de bombas hidráulicas",
                "trabajo_2_realizado": "Todas las bombas operando correctamente",
            }
        }


class OrdenTrabajoUpdate(BaseModel):
    """
    Schema para actualizar una orden de trabajo existente.
    Todos los campos son opcionales.
    """

    fecha: Optional[date] = None

    trabajo_1_a_realizar: Optional[str] = Field(None, max_length=5000)
    trabajo_1_realizado: Optional[str] = Field(None, max_length=5000)

    trabajo_2_a_realizar: Optional[str] = Field(None, max_length=5000)
    trabajo_2_realizado: Optional[str] = Field(None, max_length=5000)

    trabajo_3_a_realizar: Optional[str] = Field(None, max_length=5000)
    trabajo_3_realizado: Optional[str] = Field(None, max_length=5000)

    trabajo_4_a_realizar: Optional[str] = Field(None, max_length=5000)
    trabajo_4_realizado: Optional[str] = Field(None, max_length=5000)

    trabajo_5_a_realizar: Optional[str] = Field(None, max_length=5000)
    trabajo_5_realizado: Optional[str] = Field(None, max_length=5000)

    class Config:
        json_schema_extra = {
            "example": {
                "trabajo_1_realizado": "Se completó el mantenimiento según lo planificado"
            }
        }


class OrdenTrabajoSchema(BaseModel):
    """
    Schema de respuesta completo de una orden de trabajo
    """

    id: int
    fecha: date

    trabajo_1_a_realizar: Optional[str] = None
    trabajo_1_realizado: Optional[str] = None

    trabajo_2_a_realizar: Optional[str] = None
    trabajo_2_realizado: Optional[str] = None

    trabajo_3_a_realizar: Optional[str] = None
    trabajo_3_realizado: Optional[str] = None

    trabajo_4_a_realizar: Optional[str] = None
    trabajo_4_realizado: Optional[str] = None

    trabajo_5_a_realizar: Optional[str] = None
    trabajo_5_realizado: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrdenTrabajoListResponse(BaseModel):
    """
    Schema para respuesta de listado con paginación
    """

    success: bool = True
    total: int = Field(..., description="Total de registros encontrados")
    skip: int = Field(..., description="Número de registros omitidos")
    limit: int = Field(..., description="Límite de registros por página")
    data: list[OrdenTrabajoSchema] = Field(
        ..., description="Lista de órdenes de trabajo"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total": 50,
                "skip": 0,
                "limit": 10,
                "data": [
                    {
                        "id": 1,
                        "fecha": "2026-02-08",
                        "trabajo_1_a_realizar": "Mantenimiento compresor",
                        "trabajo_1_realizado": "Completado exitosamente",
                        "created_at": "2026-02-08T10:00:00",
                        "updated_at": "2026-02-08T10:00:00",
                    }
                ],
            }
        }
