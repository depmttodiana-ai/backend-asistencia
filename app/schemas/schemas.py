from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


# --- ESQUEMAS DE LECTURA (Output) ---
class AsistenciaSchema(BaseModel):
    id: int
    id_empleado: int
    codigo: str
    nombre: str
    apellido: str
    cargo: str
    fecha_ingreso: Optional[date] = None
    turno: str
    fecha: date
    estado: str
    estado_detalle: str
    es_feriado: Optional[str] = None
    descripcion_feriado: Optional[str] = None
    observacion: Optional[str] = None

    class Config:
        from_attributes = True


# --- ESQUEMAS DE INSERCIÓN (Input) ---
class AsistenciaCreate(BaseModel):
    empleado_id: int
    turno_id: int
    fecha: date
    estado: str = Field(
        ...,
        pattern="^(Presente|Falta|Vacaciones|Licencia|Suspendido|x|v|pvc|pr|Feriado)$",
    )
    observacion: Optional[str] = None
    he_diurnas: Optional[float] = 0.0
    he_nocturnas: Optional[float] = 0.0
    es_feriado: Optional[bool] = False


class HorasExtrasCreate(BaseModel):
    empleado_id: int
    fecha: date
    cantidad_horas: float
    tipo: str = Field(..., pattern="^(diurna|nocturna)$")


class FeriadoCreate(BaseModel):
    fecha: date
    descripcion: str


# --- ESQUEMAS DE ACTUALIZACIÓN (PATCH - Campos Opcionales) ---


# Asistencia: Ahora todos son opcionales para PATCH
class AsistenciaUpdate(BaseModel):
    empleado_id: Optional[int] = None
    turno_id: Optional[int] = None
    fecha: Optional[date] = None
    estado: Optional[str] = Field(None, pattern="^(x|v|pr|pcv)$")


# Horas Extras: Mantenemos como estaba (ya era patch)
class HorasExtrasUpdate(BaseModel):
    empleado_id: Optional[int] = None
    fecha: Optional[date] = None
    cantidad_horas: Optional[float] = None


# Feriados: Mantenemos como estaba (ya era patch)
class FeriadoUpdate(BaseModel):
    fecha: Optional[date] = None
    descripcion: Optional[str] = None


# ... (código anterior de schemas) ...


# --- ESQUEMA DE RESPUESTA PARA BÚSQUEDA POR ID ---
# Devuelve los datos puros de la tabla Asistencia (sin joins)
class AsistenciaDetalle(BaseModel):
    id: int
    empleado_id: int
    turno_id: int
    fecha: date
    estado: str
    # created_at y updated_at si las quieres mostrar, son opcionales aquí

    class Config:
        from_attributes = True


# --- ESQUEMAS PARA HORAS EXTRAS ---
class HorasExtrasSchema(BaseModel):
    id: int
    empleado_id: int
    fecha: date
    cantidad_horas: float

    class Config:
        from_attributes = True


# --- ESQUEMA DE RESPUESTA PARA CONSULTAS POR EMPLEADO O FECHA ---
class AsistenciaConHorasExtras(BaseModel):
    asistencias: list[AsistenciaSchema]
    horas_extras_diurnas: list[HorasExtrasSchema]
    horas_extras_nocturnas: list[HorasExtrasSchema]

    class Config:
        from_attributes = True


# --- ESQUEMAS PARA REPORTES SEMANALES ---
class AsistenciaDiaria(BaseModel):
    """Representa la asistencia de un día específico"""

    fecha: date
    estado: str
    turno: Optional[str] = None
    horas_extras_diurnas: float = 0.0
    horas_extras_nocturnas: float = 0.0
    es_feriado: Optional[str] = None
    descripcion_feriado: Optional[str] = None

    class Config:
        from_attributes = True


class ReporteSemanalEmpleado(BaseModel):
    """Reporte semanal de un empleado específico"""

    empleado_id: int
    codigo: str
    nombre: str
    apellido: str
    cargo: Optional[str] = None

    # Asistencias por día
    lunes: Optional[AsistenciaDiaria] = None
    martes: Optional[AsistenciaDiaria] = None
    miercoles: Optional[AsistenciaDiaria] = None
    jueves: Optional[AsistenciaDiaria] = None
    viernes: Optional[AsistenciaDiaria] = None
    sabado: Optional[AsistenciaDiaria] = None
    domingo: Optional[AsistenciaDiaria] = None

    # Totales de la semana
    total_horas_extras_diurnas: float = 0.0
    total_horas_extras_nocturnas: float = 0.0
    total_asistencias: int = 0
    total_faltas: int = 0
    total_feriados_trabajados: int = 0
    total_horas_extras_acumuladas: float = 0.0

    class Config:
        from_attributes = True


class ReporteSemanalResponse(BaseModel):
    """Respuesta con reportes semanales de múltiples empleados"""

    success: bool = True
    fecha_inicio: date  # Lunes de la semana
    fecha_fin: date  # Domingo de la semana
    total_empleados: int
    reportes: list[ReporteSemanalEmpleado]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "fecha_inicio": "2024-01-15",
                "fecha_fin": "2024-01-21",
                "total_empleados": 10,
                "reportes": [],
            }
        }


# --- SCHEMAS PARA REPORTE DE NÓMINA DETALLADO (SENIOR APPROACH) ---
class ReporteDetalleDia(BaseModel):
    fecha: date
    dia_semana: str  # Lunes, Martes...
    estado: str  # V, X, S/R
    horas_extras_diurnas: float
    horas_extras_nocturnas: float
    es_feriado: bool
    descripcion_feriado: Optional[str] = None

    class Config:
        from_attributes = True


class ReporteNominaEmpleado(BaseModel):
    empleado_id: int
    codigo: str
    nombre_completo: str
    cargo: str

    # Detalle día a día
    detalles: List[ReporteDetalleDia]

    # Totales acumulados
    total_horas_extras_diurnas: float
    total_horas_extras_nocturnas: float
    total_horas_extras_global: float  # Suma de ambas
    total_dias_trabajados: int
    total_feriados_trabajados: int

    class Config:
        from_attributes = True


class ReporteNominaResponse(BaseModel):
    success: bool
    fecha_inicio: date
    fecha_fin: date
    total_registros: int
    data: List[ReporteNominaEmpleado]
