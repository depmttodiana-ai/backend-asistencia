from typing import Optional
from datetime import date
from sqlalchemy import Column, Integer, String, Date
from app.core.database import Base


class Empleado(Base):
    """
    Modelo de Empleado del Departamento de Mantenimiento

    Representa la información de un empleado incluyendo
    datos personales y laborales.

    Nota: Este modelo se alinea con la tabla 'empleados' existente en la base de datos.
    """

    __tablename__ = "empleados"
    __table_args__ = {"extend_existing": True}

    # Identificadores
    id: int = Column(Integer, primary_key=True, index=True)
    codigo: str = Column(String, comment="Código único del empleado")

    # Datos Personales
    nombre: str = Column(String, comment="Nombre del empleado")
    apellido: str = Column(String, comment="Apellido del empleado")

    # Datos Laborales
    cargo: str = Column(String, comment="Cargo o posición del empleado")
    estado: str = Column(
        String, comment="Estado del empleado: activo, inactivo, vacaciones, licencia"
    )
    fecha_ingreso: Optional[date] = Column(
        Date, nullable=True, comment="Fecha de ingreso a la empresa"
    )

    # Relaciones (para futuras extensiones)
    # asistencias = relationship("Asistencia", back_populates="empleado")
    # horas_extras_diurnas = relationship("HorasExtrasDiurnas", back_populates="empleado")
    # horas_extras_nocturnas = relationship("HorasExtrasNocturnas", back_populates="empleado")

    def __repr__(self):
        return f"<Empleado(id={self.id}, codigo='{self.codigo}', nombre='{self.nombre} {self.apellido}', cargo='{self.cargo}', estado='{self.estado}')>"

    def nombre_completo(self) -> str:
        """Retorna el nombre completo del empleado"""
        return f"{self.nombre} {self.apellido}"

    def is_activo(self) -> bool:
        """Verifica si el empleado está activo"""
        return self.estado.lower() == "activo"
