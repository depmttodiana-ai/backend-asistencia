from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date
from enum import Enum


# --- ENUMERACIONES ---
class EstadoEmpleado(str, Enum):
    """Estados posibles de un empleado"""

    ACTIVO = "activo"
    INACTIVO = "inactivo"
    VACACIONES = "vacaciones"
    LICENCIA = "licencia"
    SUSPENDIDO = "suspendido"


# --- ESQUEMAS DE LECTURA (Output) ---
class EmpleadoBase(BaseModel):
    """Schema base con campos comunes"""

    codigo: str = Field(
        ..., min_length=1, max_length=20, description="Código único del empleado"
    )
    nombre: str = Field(
        ..., min_length=1, max_length=100, description="Nombre del empleado"
    )
    apellido: str = Field(
        ..., min_length=1, max_length=100, description="Apellido del empleado"
    )
    cargo: str = Field(
        ..., min_length=1, max_length=100, description="Cargo del empleado"
    )
    # estado: EstadoEmpleado = Field(
    #     default=EstadoEmpleado.ACTIVO, description="Estado del empleado"
    # )
    fecha_ingreso: Optional[date] = Field(
        None, description="Fecha de ingreso a la empresa"
    )

    @field_validator("codigo")
    @classmethod
    def codigo_must_be_alphanumeric(cls, v: str) -> str:
        """Valida que el código sea alfanumérico"""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("El código debe ser alfanumérico (puede contener - y _)")
        return v.upper()

    @field_validator("nombre", "apellido")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """Valida que nombre y apellido no estén vacíos"""
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v.strip().title()


class EmpleadoSchema(EmpleadoBase):
    """Schema completo para lectura (incluye ID)"""

    id: int = Field(..., description="ID único del empleado")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "codigo": "EMP-001",
                "nombre": "Juan",
                "apellido": "Pérez",
                "cargo": "Técnico de Mantenimiento",
                "estado": "activo",
                "fecha_ingreso": "2024-01-15",
            }
        }


class EmpleadoResumen(BaseModel):
    """Schema resumido para listados"""

    id: int
    codigo: str
    nombre: str
    apellido: str
    cargo: str
    # estado: EstadoEmpleado

    class Config:
        from_attributes = True

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"


# --- ESQUEMAS DE CREACIÓN (Input) ---
class EmpleadoCreate(EmpleadoBase):
    """Schema para crear un nuevo empleado"""

    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "EMP-001",
                "nombre": "Juan",
                "apellido": "Pérez",
                "cargo": "Técnico de Mantenimiento",
                "estado": "activo",
                "fecha_ingreso": "2024-01-15",
            }
        }


# --- ESQUEMAS DE ACTUALIZACIÓN (PUT - Todos los campos requeridos) ---
class EmpleadoUpdate(EmpleadoBase):
    """Schema para actualización completa (PUT)"""

    pass


# --- ESQUEMAS DE ACTUALIZACIÓN PARCIAL (PATCH - Campos opcionales) ---
class EmpleadoPatch(BaseModel):
    """Schema para actualización parcial (PATCH)"""

    codigo: Optional[str] = Field(None, min_length=1, max_length=20)
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    apellido: Optional[str] = Field(None, min_length=1, max_length=100)
    cargo: Optional[str] = Field(None, min_length=1, max_length=100)
    # estado: Optional[EstadoEmpleado] = None
    fecha_ingreso: Optional[date] = None

    @field_validator("codigo")
    @classmethod
    def codigo_must_be_alphanumeric(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("El código debe ser alfanumérico (puede contener - y _)")
        return v.upper()

    @field_validator("nombre", "apellido")
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v.strip().title()

    class Config:
        json_schema_extra = {"example": {"estado": "vacaciones"}}


# --- ESQUEMAS DE RESPUESTA ---
class EmpleadoResponse(BaseModel):
    """Schema para respuestas de operaciones exitosas"""

    success: bool = True
    message: str
    data: Optional[EmpleadoSchema] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Empleado creado exitosamente",
                "data": {
                    "id": 1,
                    "codigo": "EMP-001",
                    "nombre": "Juan",
                    "apellido": "Pérez",
                    "cargo": "Técnico de Mantenimiento",
                    "estado": "activo",
                },
            }
        }


class EmpleadoListResponse(BaseModel):
    """Schema para respuestas de listados"""

    success: bool = True
    total: int
    data: list[EmpleadoResumen]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total": 2,
                "data": [
                    {
                        "id": 1,
                        "codigo": "EMP-001",
                        "nombre": "Juan",
                        "apellido": "Pérez",
                        "cargo": "Técnico de Mantenimiento",
                        "estado": "activo",
                    }
                ],
            }
        }


# --- ESQUEMAS DE FILTROS ---
class EmpleadoFiltros(BaseModel):
    """Schema para filtros de búsqueda"""

    # estado: Optional[EstadoEmpleado] = None
    cargo: Optional[str] = None
    search: Optional[str] = Field(
        None, description="Búsqueda por código, nombre o apellido"
    )
    fecha_ingreso_desde: Optional[date] = None
    fecha_ingreso_hasta: Optional[date] = None

    class Config:
        json_schema_extra = {
            "example": {
                "estado": "activo",
                "cargo": "Técnico de Mantenimiento",
                "search": "Juan",
            }
        }
