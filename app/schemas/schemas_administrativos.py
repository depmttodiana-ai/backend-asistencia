from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date
from enum import Enum


# --- ENUMERACIONES ---
class CargoAdministrativo(str, Enum):
    """Cargos administrativos permitidos"""

    COORDINADOR = "Coordinador de Mantenimiento"
    SUPERVISOR = "Supervisor de Mantenimiento"
    COORDINADOR_GENERAL = "Coordinador General"
    SUPERVISOR_GENERAL = "Supervisor General"


class EstadoAdministrativo(str, Enum):
    """Estados posibles de un administrativo"""

    ACTIVO = "activo"
    INACTIVO = "inactivo"
    VACACIONES = "vacaciones"
    LICENCIA = "licencia"


# --- ESQUEMAS DE LECTURA (Output) ---
class AdministrativoBase(BaseModel):
    """Schema base con campos comunes para administrativos"""

    codigo: str = Field(
        ..., min_length=1, max_length=20, description="Código único del administrativo"
    )
    nombre: str = Field(
        ..., min_length=1, max_length=100, description="Nombre del administrativo"
    )
    apellido: str = Field(
        ..., min_length=1, max_length=100, description="Apellido del administrativo"
    )
    cargo: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Cargo administrativo (Coordinador/Supervisor)",
    )
    estado: EstadoAdministrativo = Field(
        default=EstadoAdministrativo.ACTIVO, description="Estado del administrativo"
    )
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

    @field_validator("cargo")
    @classmethod
    def cargo_must_be_administrative(cls, v: str) -> str:
        """Valida que el cargo sea administrativo (Coordinador o Supervisor)"""
        cargo_lower = v.lower().strip()
        if "coordinador" not in cargo_lower and "supervisor" not in cargo_lower:
            raise ValueError(
                'El cargo debe ser administrativo (debe contener "Coordinador" o "Supervisor")'
            )
        return v.strip().title()


class AdministrativoSchema(AdministrativoBase):
    """Schema completo para lectura (incluye ID)"""

    id: int = Field(..., description="ID único del administrativo")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "codigo": "ADM-001",
                "nombre": "María",
                "apellido": "González",
                "cargo": "Coordinador de Mantenimiento",
                "estado": "activo",
                "fecha_ingreso": "2024-01-15",
            }
        }


class AdministrativoResumen(BaseModel):
    """Schema resumido para listados"""

    id: int
    codigo: str
    nombre: str
    apellido: str
    cargo: str
    estado: EstadoAdministrativo

    class Config:
        from_attributes = True

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    @property
    def nivel_jerarquico(self) -> str:
        """Determina el nivel jerárquico basado en el cargo"""
        if "coordinador" in self.cargo.lower():
            return "Coordinación"
        elif "supervisor" in self.cargo.lower():
            return "Supervisión"
        return "Administrativo"


class AdministrativoDetallado(AdministrativoSchema):
    """Schema con información detallada"""

    nivel_jerarquico: Optional[str] = Field(
        None, description="Nivel jerárquico del administrativo"
    )

    class Config:
        from_attributes = True


# --- ESQUEMAS DE CREACIÓN (Input) ---
class AdministrativoCreate(AdministrativoBase):
    """Schema para crear un nuevo administrativo"""

    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "ADM-001",
                "nombre": "María",
                "apellido": "González",
                "cargo": "Coordinador de Mantenimiento",
                "estado": "activo",
                "fecha_ingreso": "2024-01-15",
            }
        }


# --- ESQUEMAS DE ACTUALIZACIÓN (PUT - Todos los campos requeridos) ---
class AdministrativoUpdate(AdministrativoBase):
    """Schema para actualización completa (PUT)"""

    pass


# --- ESQUEMAS DE ACTUALIZACIÓN PARCIAL (PATCH - Campos opcionales) ---
class AdministrativoPatch(BaseModel):
    """Schema para actualización parcial (PATCH)"""

    codigo: Optional[str] = Field(None, min_length=1, max_length=20)
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    apellido: Optional[str] = Field(None, min_length=1, max_length=100)
    cargo: Optional[str] = Field(None, min_length=1, max_length=100)
    estado: Optional[EstadoAdministrativo] = None
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

    @field_validator("cargo")
    @classmethod
    def cargo_must_be_administrative(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cargo_lower = v.lower().strip()
        if "coordinador" not in cargo_lower and "supervisor" not in cargo_lower:
            raise ValueError(
                'El cargo debe ser administrativo (debe contener "Coordinador" o "Supervisor")'
            )
        return v.strip().title()

    class Config:
        json_schema_extra = {"example": {"estado": "vacaciones"}}


# --- ESQUEMAS DE RESPUESTA ---
class AdministrativoResponse(BaseModel):
    """Schema para respuestas de operaciones exitosas"""

    success: bool = True
    message: str
    data: Optional[AdministrativoSchema] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Administrativo creado exitosamente",
                "data": {
                    "id": 1,
                    "codigo": "ADM-001",
                    "nombre": "María",
                    "apellido": "González",
                    "cargo": "Coordinador de Mantenimiento",
                    "estado": "activo",
                },
            }
        }


class AdministrativoListResponse(BaseModel):
    """Schema para respuestas de listados"""

    success: bool = True
    total: int
    data: list[AdministrativoResumen]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total": 2,
                "data": [
                    {
                        "id": 1,
                        "codigo": "ADM-001",
                        "nombre": "María",
                        "apellido": "González",
                        "cargo": "Coordinador de Mantenimiento",
                        "estado": "activo",
                    }
                ],
            }
        }


# --- ESQUEMAS DE FILTROS ---
class AdministrativoFiltros(BaseModel):
    """Schema para filtros de búsqueda de administrativos"""

    estado: Optional[EstadoAdministrativo] = None
    tipo_cargo: Optional[str] = Field(
        None, description="Filtrar por 'coordinador' o 'supervisor'"
    )
    search: Optional[str] = Field(
        None, description="Búsqueda por código, nombre o apellido"
    )
    fecha_ingreso_desde: Optional[date] = None
    fecha_ingreso_hasta: Optional[date] = None

    class Config:
        json_schema_extra = {
            "example": {
                "estado": "activo",
                "tipo_cargo": "coordinador",
                "search": "María",
            }
        }


# --- ESQUEMAS ESTADÍSTICAS ---
class AdministrativosEstadisticas(BaseModel):
    """Schema para estadísticas de administrativos"""

    total_administrativos: int
    total_coordinadores: int
    total_supervisores: int
    por_estado: dict[str, int]
    activos: int
    inactivos: int

    class Config:
        json_schema_extra = {
            "example": {
                "total_administrativos": 10,
                "total_coordinadores": 3,
                "total_supervisores": 7,
                "por_estado": {"activo": 8, "inactivo": 1, "vacaciones": 1},
                "activos": 8,
                "inactivos": 2,
            }
        }
