from typing import Optional
from datetime import date
from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, DateTime

# from sqlalchemy.orm import relationship
from app.core.database import Base

# --- MODELOS DE TABLAS FÍSICAS ---


# 1. MODELO EMPLEADO (ESTABA FALTANDO)
class Empleado(Base):
    __tablename__ = "empleados"
    __table_args__ = {"extend_existing": True}

    id: int = Column(Integer, primary_key=True, index=True)
    codigo: str = Column(String)
    nombre: str = Column(String)
    apellido: str = Column(String)
    cargo: str = Column(String)
    estado: str = Column(String)
    fecha_ingreso: Optional[date] = Column(Date)
    # Puedes agregar created_at y updated_at si los necesitas en la lógica de la app
    # created_at: date = Column(Date)
    # updated_at: date = Column(Date)


# 2. MODELO TURNO
class Turno(Base):
    __tablename__ = "turnos"
    __table_args__ = {"extend_existing": True}

    id: int = Column(Integer, primary_key=True, index=True)
    nombre: str = Column(String(20))


# 3. MODELO ASISTENCIA
class Asistencia(Base):
    __tablename__ = "asistencia"
    __table_args__ = {"extend_existing": True}

    id: int = Column(Integer, primary_key=True, index=True)
    empleado_id: int = Column(
        Integer, ForeignKey("empleados.id")
    )  # Ahora sí encuentra 'empleados'
    turno_id: int = Column(Integer, ForeignKey("turnos.id"))
    fecha: date = Column(Date)
    estado: str = Column(String)
    observacion: Optional[str] = Column(String, nullable=True)


# 4. MODELOS HORAS EXTRAS
class HorasExtrasDiurnas(Base):
    __tablename__ = "horas_extras_diurnas"
    __table_args__ = {"extend_existing": True}

    id: int = Column(Integer, primary_key=True, index=True)
    empleado_id: int = Column(Integer, ForeignKey("empleados.id"))
    fecha: date = Column(Date)
    cantidad_horas: float = Column(Numeric(4, 2))


class HorasExtrasNocturnas(Base):
    __tablename__ = "horas_extras_nocturnas"
    __table_args__ = {"extend_existing": True}

    id: int = Column(Integer, primary_key=True, index=True)
    empleado_id: int = Column(Integer, ForeignKey("empleados.id"))
    fecha: date = Column(Date)
    cantidad_horas: float = Column(Numeric(4, 2))


# 5. MODELO FERIADO
class Feriado(Base):
    __tablename__ = "feriados"
    __table_args__ = {"extend_existing": True}

    id: int = Column(Integer, primary_key=True, index=True)
    fecha: date = Column(Date, unique=True)
    descripcion: str = Column(String)


# --- VISTA (SOLO LECTURA) ---
class ReporteAsistencia(Base):
    __tablename__ = "vw_reporte_asistencia_completo"
    __table_args__ = {"extend_existing": True}

    id: int = Column(Integer, primary_key=True)
    id_empleado: int = Column(Integer, primary_key=True)
    fecha: date = Column(Date, primary_key=True)
    codigo: Optional[str] = Column(String)
    nombre: Optional[str] = Column(String)
    apellido: Optional[str] = Column(String)
    cargo: Optional[str] = Column(String)
    fecha_ingreso: Optional[date] = Column(Date)
    turno: Optional[str] = Column(String)
    estado: Optional[str] = Column(String)
    estado_detalle: Optional[str] = Column(String)
    es_feriado: Optional[str] = Column(String)
    descripcion_feriado: Optional[str] = Column(String)


# 6. MODELO USUARIO (Para Autenticación)
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String, unique=True, index=True)
    hashed_password: str = Column(String)
    role: str = Column(String)  # 'admin', 'coordinador', 'supervisor'
    email: str = Column(String, unique=True, index=True, nullable=True)
    nombre: str = Column(String, nullable=True)
    apellido: str = Column(String, nullable=True)
    reset_password_token: str = Column(String, nullable=True)
    reset_password_expires: str = Column(DateTime, nullable=True)
