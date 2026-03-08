from sqlalchemy.orm import Query
from app.models.models_empleados import Empleado


class Administrativo(Empleado):
    """
    Modelo de Administrativo - Extiende de Empleado

    Representa empleados con cargos administrativos (Coordinador, Supervisor)
    del área de mantenimiento. Este modelo filtra y gestiona específicamente
    a los empleados con roles de liderazgo.

    Usa la misma tabla 'empleados' pero con lógica de negocio específica.
    """

    # Cargos administrativos permitidos
    CARGOS_ADMINISTRATIVOS = [
        "coordinador",
        "supervisor",
        "Coordinador",
        "Supervisor",
        "Coordinador de Mantenimiento",
        "Supervisor de Mantenimiento",
    ]

    @classmethod
    def query_administrativos(cls, session) -> Query:
        """
        Query helper que filtra solo empleados con cargos administrativos

        Args:
            session: Sesión de SQLAlchemy

        Returns:
            Query filtrada solo para administrativos
        """
        from sqlalchemy import or_

        filters = [
            Empleado.cargo.ilike(f"%{cargo}%")
            for cargo in ["coordinador", "supervisor"]
        ]

        return session.query(Empleado).filter(or_(*filters))

    @classmethod
    def es_cargo_administrativo(cls, cargo: str) -> bool:
        """
        Verifica si un cargo es considerado administrativo

        Args:
            cargo: Nombre del cargo a verificar

        Returns:
            True si es un cargo administrativo, False en caso contrario
        """
        cargo_lower = cargo.lower().strip()
        return any(keyword in cargo_lower for keyword in ["coordinador", "supervisor"])

    @classmethod
    def validar_cargo_administrativo(cls, cargo: str) -> str:
        """
        Valida y normaliza un cargo administrativo

        Args:
            cargo: Cargo a validar

        Returns:
            Cargo normalizado

        Raises:
            ValueError: Si el cargo no es administrativo
        """
        if not cls.es_cargo_administrativo(cargo):
            raise ValueError(
                f"El cargo '{cargo}' no es administrativo. "
                "Debe contener 'Coordinador' o 'Supervisor'"
            )
        return cargo.strip().title()

    def tiene_permisos_especiales(self) -> bool:
        """Verifica si el administrativo tiene permisos especiales"""
        return "coordinador" in self.cargo.lower()

    def __repr__(self):
        return (
            f"<Administrativo(id={self.id}, codigo='{self.codigo}', "
            f"nombre='{self.nombre} {self.apellido}', cargo='{self.cargo}')>"
        )
