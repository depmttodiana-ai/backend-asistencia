from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.auth_deps import coordinador_or_admin, any_auth

from sqlalchemy import or_
from typing import Optional

from app.core.database import get_db
from app.models.models_empleados import Empleado
from app.models.models_administrativos import Administrativo
from app.schemas.schemas_administrativos import (
    AdministrativoSchema,
    AdministrativoCreate,
    AdministrativoUpdate,
    AdministrativoPatch,
    AdministrativoResponse,
    AdministrativoListResponse,
    AdministrativosEstadisticas,
    EstadoAdministrativo,
)


router = APIRouter(
    prefix="/administrativos",
    tags=["Administrativos"],
    responses={404: {"description": "Administrativo no encontrado"}},
)


# ==================== RUTAS GET ====================


@router.get(
    "/",
    response_model=AdministrativoListResponse,
    summary="Listar todos los administrativos",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_administrativos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(
        100, ge=1, le=1000, description="Número máximo de registros a retornar"
    ),
    estado: Optional[EstadoAdministrativo] = Query(
        None, description="Filtrar por estado"
    ),
    tipo_cargo: Optional[str] = Query(
        None, description="Filtrar por 'coordinador' o 'supervisor'"
    ),
    search: Optional[str] = Query(
        None, description="Buscar por código, nombre o apellido"
    ),
    db: Session = Depends(get_db),
):
    """
    Obtiene la lista de administrativos (Coordinadores y Supervisores) con paginación y filtros.

    - **skip**: Número de registros a omitir (para paginación)
    - **limit**: Número máximo de registros a retornar
    - **estado**: Filtrar por estado del administrativo
    - **tipo_cargo**: Filtrar por 'coordinador' o 'supervisor'
    - **search**: Búsqueda por código, nombre o apellido
    """
    # Base query: solo empleados con cargos administrativos
    query = Administrativo.query_administrativos(db)

    # Aplicar filtros
    if estado:
        query = query.filter(Empleado.estado == estado.value)

    if tipo_cargo:
        query = query.filter(Empleado.cargo.ilike(f"%{tipo_cargo}%"))

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
    administrativos = (
        query.order_by(Empleado.cargo, Empleado.apellido)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return AdministrativoListResponse(success=True, total=total, data=administrativos)


@router.get(
    "/coordinadores",
    response_model=AdministrativoListResponse,
    summary="Listar solo coordinadores",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_coordinadores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    estado: Optional[EstadoAdministrativo] = Query(
        None, description="Filtrar por estado"
    ),
    db: Session = Depends(get_db),
):
    """
    Obtiene solo los empleados con cargo de Coordinador.
    """
    query = db.query(Empleado).filter(Empleado.cargo.ilike("%coordinador%"))

    if estado:
        query = query.filter(Empleado.estado == estado.value)

    total = query.count()
    coordinadores = (
        query.order_by(Empleado.apellido, Empleado.nombre)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return AdministrativoListResponse(success=True, total=total, data=coordinadores)


@router.get(
    "/supervisores",
    response_model=AdministrativoListResponse,
    summary="Listar solo supervisores",
    dependencies=[Depends(any_auth)],
)
def get_supervisores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    estado: Optional[EstadoAdministrativo] = Query(
        None, description="Filtrar por estado"
    ),
    db: Session = Depends(get_db),
):
    """
    Obtiene solo los empleados con cargo de Supervisor.
    """
    query = db.query(Empleado).filter(Empleado.cargo.ilike("%supervisor%"))

    if estado:
        query = query.filter(Empleado.estado == estado.value)

    total = query.count()
    supervisores = (
        query.order_by(Empleado.apellido, Empleado.nombre)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return AdministrativoListResponse(success=True, total=total, data=supervisores)


@router.get(
    "/activos",
    response_model=AdministrativoListResponse,
    summary="Listar administrativos activos",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_administrativos_activos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Obtiene solo los administrativos con estado 'activo'.
    """
    query = Administrativo.query_administrativos(db).filter(
        Empleado.estado == EstadoAdministrativo.ACTIVO.value
    )

    total = query.count()
    administrativos = (
        query.order_by(Empleado.cargo, Empleado.apellido)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return AdministrativoListResponse(success=True, total=total, data=administrativos)


@router.get(
    "/{administrativo_id}",
    response_model=AdministrativoSchema,
    summary="Obtener administrativo por ID",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_administrativo_by_id(
    administrativo_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un administrativo específico por su ID.

    - **administrativo_id**: ID único del administrativo
    """
    administrativo = (
        Administrativo.query_administrativos(db)
        .filter(Empleado.id == administrativo_id)
        .first()
    )

    if not administrativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrativo con ID {administrativo_id} no encontrado o no tiene cargo administrativo",
        )

    return administrativo


@router.get(
    "/codigo/{codigo}",
    response_model=AdministrativoSchema,
    summary="Obtener administrativo por código",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_administrativo_by_codigo(
    codigo: str,
    db: Session = Depends(get_db),
):
    """
    Obtiene un administrativo específico por su código único.

    - **codigo**: Código único del administrativo
    """
    administrativo = (
        Administrativo.query_administrativos(db)
        .filter(Empleado.codigo == codigo.upper())
        .first()
    )

    if not administrativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrativo con código {codigo} no encontrado o no tiene cargo administrativo",
        )

    return administrativo


# ==================== RUTAS POST ====================


@router.post(
    "/",
    response_model=AdministrativoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo administrativo",
    dependencies=[Depends(coordinador_or_admin)],
)
def crear_administrativo(
    administrativo: AdministrativoCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo administrativo en el sistema.

    Validaciones:
    - El código debe ser único
    - El cargo debe ser administrativo (Coordinador o Supervisor)
    - Todos los campos requeridos deben estar presentes
    """
    # Validar que el cargo sea administrativo
    try:
        Administrativo.validar_cargo_administrativo(administrativo.cargo)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Verificar si el código ya existe
    existe_codigo = (
        db.query(Empleado)
        .filter(Empleado.codigo == administrativo.codigo.upper())
        .first()
    )
    if existe_codigo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un empleado con el código {administrativo.codigo}",
        )

    # Crear el nuevo administrativo (se guarda en la tabla empleados)
    db_administrativo = Empleado(**administrativo.model_dump())

    try:
        db.add(db_administrativo)
        db.commit()
        db.refresh(db_administrativo)

        return AdministrativoResponse(
            success=True,
            message="Administrativo creado exitosamente",
            data=db_administrativo,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear administrativo: {str(e)}",
        )


# ==================== RUTAS PUT ====================


@router.put(
    "/{administrativo_id}",
    response_model=AdministrativoResponse,
    summary="Actualizar administrativo (completo)",
    dependencies=[Depends(coordinador_or_admin)],
)
def actualizar_administrativo_completo(
    administrativo_id: int,
    administrativo_data: AdministrativoUpdate,
    db: Session = Depends(get_db),
):
    """
    Actualiza TODOS los campos de un administrativo existente (PUT).
    Todos los campos son requeridos.

    - **administrativo_id**: ID del administrativo a actualizar
    """
    # Validar que el cargo sea administrativo
    try:
        Administrativo.validar_cargo_administrativo(administrativo_data.cargo)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Buscar el administrativo
    administrativo = (
        Administrativo.query_administrativos(db)
        .filter(Empleado.id == administrativo_id)
        .first()
    )

    if not administrativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrativo con ID {administrativo_id} no encontrado",
        )

    # Verificar unicidad de código (si cambió)
    if administrativo_data.codigo.upper() != administrativo.codigo:
        existe_codigo = (
            db.query(Empleado)
            .filter(
                Empleado.codigo == administrativo_data.codigo.upper(),
                Empleado.id != administrativo_id,
            )
            .first()
        )
        if existe_codigo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe otro empleado con el código {administrativo_data.codigo}",
            )

    # Actualizar todos los campos
    for key, value in administrativo_data.model_dump().items():
        setattr(administrativo, key, value)

    try:
        db.commit()
        db.refresh(administrativo)

        return AdministrativoResponse(
            success=True,
            message="Administrativo actualizado exitosamente",
            data=administrativo,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar administrativo: {str(e)}",
        )


# ==================== RUTAS PATCH ====================


@router.patch(
    "/{administrativo_id}",
    response_model=AdministrativoResponse,
    summary="Actualizar administrativo (parcial)",
    dependencies=[Depends(coordinador_or_admin)],
)
def actualizar_administrativo_parcial(
    administrativo_id: int,
    administrativo_data: AdministrativoPatch,
    db: Session = Depends(get_db),
):
    """
    Actualiza solo los campos especificados de un administrativo (PATCH).
    Solo los campos enviados serán actualizados.

    - **administrativo_id**: ID del administrativo a actualizar
    """
    # Buscar el administrativo
    administrativo = (
        Administrativo.query_administrativos(db)
        .filter(Empleado.id == administrativo_id)
        .first()
    )

    if not administrativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrativo con ID {administrativo_id} no encontrado",
        )

    # Obtener solo los campos que fueron enviados
    update_data = administrativo_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos para actualizar",
        )

    # Validar cargo si se está actualizando
    if "cargo" in update_data:
        try:
            Administrativo.validar_cargo_administrativo(update_data["cargo"])
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    # Verificar unicidad de código (si se está actualizando)
    if (
        "codigo" in update_data
        and update_data["codigo"].upper() != administrativo.codigo
    ):
        existe_codigo = (
            db.query(Empleado)
            .filter(
                Empleado.codigo == update_data["codigo"].upper(),
                Empleado.id != administrativo_id,
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
        setattr(administrativo, key, value)

    try:
        db.commit()
        db.refresh(administrativo)

        return AdministrativoResponse(
            success=True,
            message=f"Administrativo actualizado parcialmente. Campos actualizados: {', '.join(update_data.keys())}",
            data=administrativo,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar administrativo: {str(e)}",
        )


# ==================== RUTAS DELETE ====================


@router.delete(
    "/{administrativo_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar administrativo",
    dependencies=[Depends(coordinador_or_admin)],
)
def eliminar_administrativo(
    administrativo_id: int,
    db: Session = Depends(get_db),
):
    """
    Elimina un administrativo del sistema.

    ADVERTENCIA: Esta operación es irreversible.
    Considera usar PATCH para cambiar el estado a 'inactivo' en lugar de eliminar.

    - **administrativo_id**: ID del administrativo a eliminar
    """
    # Buscar el administrativo
    administrativo = (
        Administrativo.query_administrativos(db)
        .filter(Empleado.id == administrativo_id)
        .first()
    )

    if not administrativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrativo con ID {administrativo_id} no encontrado",
        )

    # Guardar información para el mensaje de respuesta
    administrativo_info = f"{administrativo.codigo} - {administrativo.nombre} {administrativo.apellido} ({administrativo.cargo})"

    try:
        db.delete(administrativo)
        db.commit()

        return {
            "success": True,
            "message": f"Administrativo {administrativo_info} eliminado exitosamente",
            "deleted_id": administrativo_id,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar administrativo: {str(e)}. Puede que existan registros relacionados.",
        )


# ==================== RUTAS ADICIONALES ====================


@router.patch(
    "/{administrativo_id}/estado",
    response_model=AdministrativoResponse,
    summary="Cambiar estado del administrativo",
    dependencies=[Depends(coordinador_or_admin)],
)
def cambiar_estado_administrativo(
    administrativo_id: int,
    nuevo_estado: EstadoAdministrativo,
    db: Session = Depends(get_db),
):
    """
    Cambia el estado de un administrativo de forma rápida.

    - **administrativo_id**: ID del administrativo
    - **nuevo_estado**: Nuevo estado a asignar
    """
    administrativo = (
        Administrativo.query_administrativos(db)
        .filter(Empleado.id == administrativo_id)
        .first()
    )

    if not administrativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrativo con ID {administrativo_id} no encontrado",
        )

    estado_anterior = administrativo.estado
    administrativo.estado = nuevo_estado.value

    try:
        db.commit()
        db.refresh(administrativo)

        return AdministrativoResponse(
            success=True,
            message=f"Estado cambiado de '{estado_anterior}' a '{nuevo_estado.value}'",
            data=administrativo,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar estado: {str(e)}",
        )


@router.get(
    "/estadisticas/resumen",
    response_model=AdministrativosEstadisticas,
    summary="Obtener estadísticas de administrativos",
    dependencies=[Depends(any_auth)],
)
def get_estadisticas_administrativos(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas generales de los administrativos.

    Retorna:
    - Total de administrativos
    - Total de coordinadores
    - Total de supervisores
    - Administrativos por estado
    - Total de activos e inactivos
    """
    # Total de administrativos
    total = Administrativo.query_administrativos(db).count()

    # Total de coordinadores
    total_coordinadores = (
        db.query(Empleado).filter(Empleado.cargo.ilike("%coordinador%")).count()
    )

    # Total de supervisores
    total_supervisores = (
        db.query(Empleado).filter(Empleado.cargo.ilike("%supervisor%")).count()
    )

    # Contar por estado
    por_estado = {}
    for estado in EstadoAdministrativo:
        count = (
            Administrativo.query_administrativos(db)
            .filter(Empleado.estado == estado.value)
            .count()
        )
        por_estado[estado.value] = count

    # Activos e inactivos
    activos = por_estado.get("activo", 0)
    inactivos = total - activos

    return AdministrativosEstadisticas(
        total_administrativos=total,
        total_coordinadores=total_coordinadores,
        total_supervisores=total_supervisores,
        por_estado=por_estado,
        activos=activos,
        inactivos=inactivos,
    )


@router.get(
    "/jerarquia/estructura",
    summary="Obtener estructura jerárquica",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_estructura_jerarquica(db: Session = Depends(get_db)):
    """
    Obtiene la estructura jerárquica del área de mantenimiento.

    Retorna coordinadores y sus supervisores asociados.
    """
    coordinadores = (
        db.query(Empleado)
        .filter(Empleado.cargo.ilike("%coordinador%"), Empleado.estado == "activo")
        .order_by(Empleado.nombre)
        .all()
    )

    supervisores = (
        db.query(Empleado)
        .filter(Empleado.cargo.ilike("%supervisor%"), Empleado.estado == "activo")
        .order_by(Empleado.nombre)
        .all()
    )

    return {
        "success": True,
        "estructura": {
            "coordinadores": [
                {
                    "id": c.id,
                    "codigo": c.codigo,
                    "nombre_completo": f"{c.nombre} {c.apellido}",
                    "cargo": c.cargo,
                }
                for c in coordinadores
            ],
            "supervisores": [
                {
                    "id": s.id,
                    "codigo": s.codigo,
                    "nombre_completo": f"{s.nombre} {s.apellido}",
                    "cargo": s.cargo,
                }
                for s in supervisores
            ],
        },
    }
