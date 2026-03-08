"""
Modelo de Órdenes de Trabajo Diarias

Este modelo maneja hasta 5 trabajos realizados por día, con:
- Trabajo a realizar
- Labor realizado
- Control de fecha y usuario
"""

from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, Text, DateTime
from app.core.database import Base


class OrdenTrabajoDiario(Base):
    """
    Tabla para almacenar órdenes de trabajo diarias.
    Permite registrar hasta 5 trabajos por día con su descripción
    de lo que se debe realizar y lo que efectivamente se realizó.
    """

    __tablename__ = "ordenes_trabajo_diario"
    __table_args__ = {"extend_existing": True}

    # Identificador único
    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Fecha del trabajo
    fecha: date = Column(Date, nullable=False, index=True)

    # ==================== TRABAJO 1 ====================
    trabajo_1_a_realizar: str = Column(Text, nullable=True)
    trabajo_1_realizado: str = Column(Text, nullable=True)

    # ==================== TRABAJO 2 ====================
    trabajo_2_a_realizar: str = Column(Text, nullable=True)
    trabajo_2_realizado: str = Column(Text, nullable=True)

    # ==================== TRABAJO 3 ====================
    trabajo_3_a_realizar: str = Column(Text, nullable=True)
    trabajo_3_realizado: str = Column(Text, nullable=True)

    # ==================== TRABAJO 4 ====================
    trabajo_4_a_realizar: str = Column(Text, nullable=True)
    trabajo_4_realizado: str = Column(Text, nullable=True)

    # ==================== TRABAJO 5 ====================
    trabajo_5_a_realizar: str = Column(Text, nullable=True)
    trabajo_5_realizado: str = Column(Text, nullable=True)

    # ==================== METADATA ====================
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<OrdenTrabajoDiario(id={self.id}, fecha={self.fecha})>"
