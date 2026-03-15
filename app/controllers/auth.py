from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.models import User

router = APIRouter(prefix="/auth")


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "email": user.email}

from pydantic import BaseModel
import secrets
from datetime import datetime, timedelta
from app.core.auth_deps import get_current_user
from app.core.email import send_reset_password_email
from app.core.security import get_password_hash

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UpdateEmailRequest(BaseModel):
    email: str

@router.post("/change-password")
def change_password(request: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    return {"message": "Contraseña cambiada con éxito."}

@router.post("/update-email")
def update_email(request: UpdateEmailRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verificar si el email ya existe en otro usuario
    existing = db.query(User).filter(User.email == request.email).first()
    if existing and existing.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este correo ya está registrado por otro usuario"
        )
    user.email = request.email
    db.commit()
    return {"message": "Email actualizado con éxito", "email": user.email}

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Responder OK por seguridad (evitar user enumeration)
        return {"message": "Si el correo está registrado, se enviará un mensaje de recuperación."}
    
    token = secrets.token_urlsafe(32)
    user.reset_password_token = token
    user.reset_password_expires = datetime.utcnow() + timedelta(minutes=15)
    
    db.commit()
    send_reset_password_email(user.email, token)
    return {"message": "Si el correo está registrado, se enviará un mensaje de recuperación."}

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_password_token == request.token).first()
    
    if not user or not user.reset_password_expires or user.reset_password_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado"
        )
    
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_password_token = None
    user.reset_password_expires = None
    db.commit()
    
    return {"message": "Contraseña actualizada con éxito."}
