from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.auth_deps import coordinador_or_admin, any_auth

from sqlalchemy import or_
from typing import Optional

from app.core.database import get_db
from app.models.models_empleados import Empleado
from app.schemas.schemas_empleados import (
    EmpleadoSchema,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoPatch,
    EmpleadoResponse,
    EmpleadoListResponse,
    EstadoEmpleado,
)


router = APIRouter(
    prefix="/empleados",
    tags=["Empleados"],
    responses={404: {"description": "Empleado no encontrado"}},
)


# ==================== RUTAS GET ====================


@router.get(
    "/",
    response_model=EmpleadoListResponse,
    summary="Listar todos los empleados",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_empleados(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(
        100, ge=1, le=1000, description="Número máximo de registros a retornar"
    ),
    estado: Optional[EstadoEmpleado] = Query(None, description="Filtrar por estado"),
    cargo: Optional[str] = Query(None, description="Filtrar por cargo"),
    search: Optional[str] = Query(
        None, description="Buscar por código, nombre o apellido"
    ),
    db: Session = Depends(get_db),
):
    """
    Obtiene la lista de empleados con paginación y filtros opcionales.

    - **skip**: Número de registros a omitir (para paginación)
    - **limit**: Número máximo de registros a retornar
    - **estado**: Filtrar por estado del empleado
    - **cargo**: Filtrar por cargo
    - **search**: Búsqueda por código, nombre o apellido
    """
    query = db.query(Empleado)

    # Aplicar filtros
    if estado:
        query = query.filter(Empleado.estado == estado.value)

    if cargo:
        query = query.filter(Empleado.cargo.ilike(f"%{cargo}%"))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Empleado.codigo.ilike(search_pattern),
                Empleado.nombre.ilike(search_pattern),
                Empleado.apellido.ilike(search_pattern),
            )
        )

    # Obtener total antes de aplicar paginación
    total = query.count()

    # Aplicar paginación y ordenamiento
    empleados = query.order_by(Empleado.id.desc()).offset(skip).limit(limit).all()

    return EmpleadoListResponse(success=True, total=total, data=empleados)


@router.get(
    "/activos",
    response_model=EmpleadoListResponse,
    summary="Listar empleados activos",
    dependencies=[Depends(any_auth)],
)
def get_empleados_activos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Obtiene solo los empleados con estado 'activo'.
    Útil para listados rápidos de personal disponible.
    """
    query = db.query(Empleado).filter(Empleado.estado == EstadoEmpleado.ACTIVO.value)
    total = query.count()
    empleados = (
        query.order_by(Empleado.apellido, Empleado.nombre)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return EmpleadoListResponse(success=True, total=total, data=empleados)


@router.get(
    "/por-cargo/{cargo}",
    response_model=EmpleadoListResponse,
    summary="Listar empleados por cargo",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_empleados_por_cargo(
    cargo: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Obtiene empleados filtrados por cargo específico.
    La búsqueda es case-insensitive y permite coincidencias parciales.
    """
    query = db.query(Empleado).filter(Empleado.cargo.ilike(f"%{cargo}%"))
    total = query.count()
    empleados = (
        query.order_by(Empleado.apellido, Empleado.nombre)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return EmpleadoListResponse(success=True, total=total, data=empleados)


@router.get(
    "/{empleado_id}",
    response_model=EmpleadoSchema,
    summary="Obtener empleado por ID",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_empleado_by_id(
    empleado_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un empleado específico por su ID.

    - **empleado_id**: ID único del empleado
    """
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()

    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con ID {empleado_id} no encontrado",
        )

    return empleado


@router.get(
    "/codigo/{codigo}",
    response_model=EmpleadoSchema,
    summary="Obtener empleado por código",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_empleado_by_codigo(
    codigo: str,
    db: Session = Depends(get_db),
):
    """
    Obtiene un empleado específico por su código único.

    - **codigo**: Código único del empleado
    """
    empleado = db.query(Empleado).filter(Empleado.codigo == codigo.upper()).first()

    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con código {codigo} no encontrado",
        )

    return empleado


# ==================== RUTAS POST ====================


@router.post(
    "/",
    response_model=EmpleadoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo empleado",
    dependencies=[Depends(coordinador_or_admin)],
)
def crear_empleado(
    empleado: EmpleadoCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo empleado en el sistema.

    Validaciones:
    - El código debe ser único
    - Todos los campos requeridos deben estar presentes
    """
    # Verificar si el código ya existe
    existe_codigo = (
        db.query(Empleado).filter(Empleado.codigo == empleado.codigo.upper()).first()
    )
    if existe_codigo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un empleado con el código {empleado.codigo}",
        )

    # Crear el nuevo empleado
    db_empleado = Empleado(**empleado.model_dump())

    try:
        db.add(db_empleado)
        db.commit()
        db.refresh(db_empleado)

        return EmpleadoResponse(
            success=True, message="Empleado creado exitosamente", data=db_empleado
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear empleado: {str(e)}",
        )


# ==================== RUTAS PUT ====================


@router.put(
    "/{empleado_id}",
    response_model=EmpleadoResponse,
    summary="Actualizar empleado (completo)",
    dependencies=[Depends(coordinador_or_admin)],
)
def actualizar_empleado_completo(
    empleado_id: int,
    empleado_data: EmpleadoUpdate,
    db: Session = Depends(get_db),
):
    """
    Actualiza TODOS los campos de un empleado existente (PUT).
    Todos los campos son requeridos.

    - **empleado_id**: ID del empleado a actualizar
    """
    # Buscar el empleado
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()

    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con ID {empleado_id} no encontrado",
        )

    # Verificar unicidad de código (si cambió)
    if empleado_data.codigo.upper() != empleado.codigo:
        existe_codigo = (
            db.query(Empleado)
            .filter(
                Empleado.codigo == empleado_data.codigo.upper(),
                Empleado.id != empleado_id,
            )
            .first()
        )
        if existe_codigo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe otro empleado con el código {empleado_data.codigo}",
            )

    # Actualizar todos los campos
    for key, value in empleado_data.model_dump().items():
        setattr(empleado, key, value)

    try:
        db.commit()
        db.refresh(empleado)

        return EmpleadoResponse(
            success=True, message="Empleado actualizado exitosamente", data=empleado
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar empleado: {str(e)}",
        )


# ==================== RUTAS PATCH ====================


@router.patch(
    "/{empleado_id}",
    response_model=EmpleadoResponse,
    summary="Actualizar empleado (parcial)",
    dependencies=[Depends(coordinador_or_admin)],
)
def actualizar_empleado_parcial(
    empleado_id: int,
    empleado_data: EmpleadoPatch,
    db: Session = Depends(get_db),
):
    """
    Actualiza solo los campos especificados de un empleado (PATCH).
    Solo los campos enviados serán actualizados.

    - **empleado_id**: ID del empleado a actualizar
    """
    # Buscar el empleado
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()

    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con ID {empleado_id} no encontrado",
        )

    # Obtener solo los campos que fueron enviados
    update_data = empleado_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos para actualizar",
        )

    # Verificar unicidad de código (si se está actualizando)
    if "codigo" in update_data and update_data["codigo"].upper() != empleado.codigo:
        existe_codigo = (
            db.query(Empleado)
            .filter(
                Empleado.codigo == update_data["codigo"].upper(),
                Empleado.id != empleado_id,
            )
            .first()
        )
        if existe_codigo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe otro empleado con el código {update_data['codigo']}",
            )

    # Actualizar solo los campos enviados
    for key, value in update_data.items():
        setattr(empleado, key, value)

    try:
        db.commit()
        db.refresh(empleado)

        return EmpleadoResponse(
            success=True,
            message=f"Empleado actualizado parcialmente. Campos actualizados: {', '.join(update_data.keys())}",
            data=empleado,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar empleado: {str(e)}",
        )


# ==================== RUTAS DELETE ====================


@router.delete(
    "/{empleado_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar empleado",
    dependencies=[Depends(coordinador_or_admin)],
)
def eliminar_empleado(
    empleado_id: int,
    db: Session = Depends(get_db),
):
    """
    Elimina un empleado del sistema.

    ADVERTENCIA: Esta operación es irreversible.
    Considera usar PATCH para cambiar el estado a 'inactivo' en lugar de eliminar.

    - **empleado_id**: ID del empleado a eliminar
    """
    # Buscar el empleado
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()

    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con ID {empleado_id} no encontrado",
        )

    # Guardar información para el mensaje de respuesta
    empleado_info = f"{empleado.codigo} - {empleado.nombre} {empleado.apellido}"

    try:
        db.delete(empleado)
        db.commit()

        return {
            "success": True,
            "message": f"Empleado {empleado_info} eliminado exitosamente",
            "deleted_id": empleado_id,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar empleado: {str(e)}. Puede que existan registros relacionados.",
        )


# ==================== RUTAS ADICIONALES ====================


@router.patch(
    "/{empleado_id}/estado",
    response_model=EmpleadoResponse,
    summary="Cambiar estado del empleado",
    dependencies=[Depends(coordinador_or_admin)],
)
def cambiar_estado_empleado(
    empleado_id: int,
    nuevo_estado: EstadoEmpleado,
    db: Session = Depends(get_db),
):
    """
    Cambia el estado de un empleado de forma rápida.

    - **empleado_id**: ID del empleado
    - **nuevo_estado**: Nuevo estado a asignar
    """
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()

    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con ID {empleado_id} no encontrado",
        )

    estado_anterior = empleado.estado
    empleado.estado = nuevo_estado.value

    try:
        db.commit()
        db.refresh(empleado)

        return EmpleadoResponse(
            success=True,
            message=f"Estado cambiado de '{estado_anterior}' a '{nuevo_estado.value}'",
            data=empleado,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar estado: {str(e)}",
        )


@router.get(
    "/estadisticas/resumen",
    summary="Obtener estadísticas de empleados",
    dependencies=[Depends(any_auth)],
)
def get_estadisticas_empleados(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas generales de los empleados.

    Retorna:
    - Total de empleados
    - Empleados por estado
    - Empleados por cargo
    """
    total = db.query(Empleado).count()

    # Contar por estado
    por_estado = {}
    for estado in EstadoEmpleado:
        count = db.query(Empleado).filter(Empleado.estado == estado.value).count()
        por_estado[estado.value] = count

    # Contar por cargo (top 10)
    from sqlalchemy import func

    por_cargo = (
        db.query(Empleado.cargo, func.count(Empleado.id).label("total"))
        .group_by(Empleado.cargo)
        .order_by(func.count(Empleado.id).desc())
        .limit(10)
        .all()
    )

    return {
        "success": True,
        "total_empleados": total,
        "por_estado": por_estado,
        "top_cargos": [{"cargo": cargo, "total": total} for cargo, total in por_cargo],
    }
