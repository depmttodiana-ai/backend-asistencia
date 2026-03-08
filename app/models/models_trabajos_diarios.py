from datetime import date
from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class TrabajoDiario(Base):
    """
    Modelo para registrar los trabajos diarios realizados.
    Incluye información de la fecha, sitio, descripción del trabajo
    y hasta 8 fotografías asociadas.
    """

    __tablename__ = "trabajos_diarios"
    __table_args__ = {"extend_existing": True}

    id: int = Column(Integer, primary_key=True, index=True)
    fecha: date = Column(Date, nullable=False, index=True)
    sitio_trabajo: str = Column(String(255), nullable=False)
    maquinaria_trabajada: str = Column(String(255), nullable=True)
    trabajo_realizado: str = Column(Text, nullable=False)

    # Rutas de las fotografías (almacenaremos las rutas en el servidor)
    foto_1: str = Column(String(500), nullable=True)
    foto_2: str = Column(String(500), nullable=True)
    foto_3: str = Column(String(500), nullable=True)
    foto_4: str = Column(String(500), nullable=True)
    foto_5: str = Column(String(500), nullable=True)
    foto_6: str = Column(String(500), nullable=True)
    foto_7: str = Column(String(500), nullable=True)
    foto_8: str = Column(String(500), nullable=True)

    # Timestamps para auditoría
    created_at: date = Column(Date, default=date.today)
    updated_at: date = Column(Date, default=date.today, onupdate=date.today)

    def __repr__(self):
        return f"<TrabajoDiario(id={self.id}, fecha={self.fecha}, sitio={self.sitio_trabajo})>"
