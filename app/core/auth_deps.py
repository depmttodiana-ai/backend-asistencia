from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.models import User
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if not user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario no tiene un rol asignado",
            )

        user_role = user.role.lower().strip()

        # Bypass para admin
        if user_role == "admin":
            return user

        if user_role not in [r.lower() for r in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos suficientes para realizar esta acción. Requerido uno de: {self.allowed_roles}",
            )
        return user


# Definición de permisos por rol según requerimiento
# admin: todo (manejado por RoleChecker)
# coordinador: empleados (create, edit, delete), asistencia (create), horas extras (edit), reportes (generate)
# supervisor: asistencia (all), horas extras (all)

# Dependencias rápidas
admin_only = RoleChecker(["admin"])
coordinador_or_admin = RoleChecker(["admin", "coordinador"])
supervisor_or_admin = RoleChecker(["admin", "supervisor"])
any_auth = RoleChecker(["admin", "coordinador", "supervisor"])
