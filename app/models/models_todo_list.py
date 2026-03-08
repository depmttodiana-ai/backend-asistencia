from typing import Optional
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class TodoList(Base):
    """
    Modelo para la lista de tareas (To-Do List) de mantenimiento.
    Permite establecer actividades diarias y su estado de ejecución.
    """

    __tablename__ = "todo_list"
    __table_args__ = {"extend_existing": True}

    id: int = Column(Integer, primary_key=True, index=True)
    fecha: date = Column(Date, nullable=False, index=True, default=date.today)
    trabajo: str = Column(Text, nullable=False)
    estado: str = Column(
        String(50), nullable=False, default="en espera"
    )  # en espera, pausado, completado
    
    # Nuevo: Turno y Supervisor
    turno: Optional[str] = Column(String(50), nullable=True)
    supervisor_encargado: Optional[str] = Column(String(100), nullable=True)

    # Nuevas fechas solicitadas
    fecha_inscripcion: date = Column(Date, nullable=False, default=date.today)
    fecha_inicio_trabajo: Optional[date] = Column(Date, nullable=True)
    fecha_finalizacion: Optional[date] = Column(Date, nullable=True)

    # Observaciones (Reducido a 3)
    observacion_1: str = Column(Text, nullable=True)
    observacion_2: str = Column(Text, nullable=True)
    observacion_3: str = Column(Text, nullable=True)

    # Fotografías asociadas (Rutas de Cloudinary o servidor)
    foto_1: str = Column(String(500), nullable=True)
    foto_2: str = Column(String(500), nullable=True)
    foto_3: str = Column(String(500), nullable=True)

    # Timestamps para auditoría
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )

    def __repr__(self):
        return f"<TodoList(id={self.id}, fecha={self.fecha}, estado={self.estado})>"
