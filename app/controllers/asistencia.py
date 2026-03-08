from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.auth_deps import any_auth, coordinador_or_admin, supervisor_or_admin
from sqlalchemy import or_
from typing import List
from datetime import date, timedelta

from app.core.database import get_db
from app.models import models
from app.schemas.schemas import (
    AsistenciaSchema,
    AsistenciaCreate,
    AsistenciaUpdate,
    HorasExtrasCreate,
    HorasExtrasUpdate,
    FeriadoCreate,
    FeriadoUpdate,
    AsistenciaConHorasExtras,
    ReporteNominaEmpleado,
    ReporteNominaResponse,
    ReporteDetalleDia,
)


router = APIRouter(prefix="/asistencia")


# --- RUTA GET: Buscar por empleado_id y Fecha (Versión Enriquecida) ---
@router.get(
    "/detalle/{empleado_id}",
    response_model=AsistenciaSchema,
    dependencies=[Depends(any_auth)],
)
def get_asistencia_por_empleado_fecha(
    empleado_id: int, fecha: date, db: Session = Depends(get_db)
):
    """
    Busca un registro específico y devuelve TODOS los detalles
    (Nombre, Apellido, Cargo, etc.) usando la Vista.
    """
    # Usamos models.ReporteAsistencia (La Vista) en lugar de models.Asistencia
    registro = (
        db.query(models.ReporteAsistencia)
        .filter(
            models.ReporteAsistencia.id_empleado == empleado_id,
            models.ReporteAsistencia.fecha == fecha,
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail="Registro no encontrado: El empleado_id y la Fecha no coinciden.",
        )

    return registro


# --- RUTAS GET ---
@router.get(
    "/", response_model=List[AsistenciaSchema], dependencies=[Depends(any_auth)]
)
def get_reporte_completo(db: Session = Depends(get_db)):
    return db.query(models.ReporteAsistencia).all()


# --- RUTA GET: Consultar por empleado_id ---
@router.get(
    "/empleado/{empleado_id}",
    response_model=AsistenciaConHorasExtras,
    dependencies=[Depends(any_auth)],
)
def get_asistencias_por_empleado(empleado_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todas las asistencias y horas extras (diurnas y nocturnas) de un empleado específico.
    """
    # Obtener asistencias del empleado
    asistencias = (
        db.query(models.ReporteAsistencia)
        .filter(models.ReporteAsistencia.id_empleado == empleado_id)
        .all()
    )

    # Obtener horas extras diurnas
    horas_diurnas = (
        db.query(models.HorasExtrasDiurnas)
        .filter(models.HorasExtrasDiurnas.empleado_id == empleado_id)
        .all()
    )

    # Obtener horas extras nocturnas
    horas_nocturnas = (
        db.query(models.HorasExtrasNocturnas)
        .filter(models.HorasExtrasNocturnas.empleado_id == empleado_id)
        .all()
    )

    return AsistenciaConHorasExtras(
        asistencias=asistencias,
        horas_extras_diurnas=horas_diurnas,
        horas_extras_nocturnas=horas_nocturnas,
    )


# --- RUTA GET: Consultar por fecha ---
@router.get(
    "/fecha/{fecha}",
    response_model=AsistenciaConHorasExtras,
    dependencies=[Depends(any_auth)],
)
def get_asistencias_por_fecha(fecha: date, db: Session = Depends(get_db)):
    """
    Obtiene todas las asistencias y horas extras (diurnas y nocturnas) de una fecha específica.
    """
    # Obtener asistencias de la fecha
    asistencias = (
        db.query(models.ReporteAsistencia)
        .filter(models.ReporteAsistencia.fecha == fecha)
        .all()
    )

    # Obtener horas extras diurnas de la fecha
    horas_diurnas = (
        db.query(models.HorasExtrasDiurnas)
        .filter(models.HorasExtrasDiurnas.fecha == fecha)
        .all()
    )

    # Obtener horas extras nocturnas de la fecha
    horas_nocturnas = (
        db.query(models.HorasExtrasNocturnas)
        .filter(models.HorasExtrasNocturnas.fecha == fecha)
        .all()
    )

    return AsistenciaConHorasExtras(
        asistencias=asistencias,
        horas_extras_diurnas=horas_diurnas,
        horas_extras_nocturnas=horas_nocturnas,
    )


# --- RUTAS POST (Crear) ---
@router.post("/", dependencies=[Depends(any_auth)])
def crear_asistencia(asistencia: AsistenciaCreate, db: Session = Depends(get_db)):
    # Extraer campos que no pertenecen al modelo base de Asistencia
    data = asistencia.model_dump()
    he_diurnas = data.pop("he_diurnas", 0)
    he_nocturnas = data.pop("he_nocturnas", 0)
    es_feriado = data.pop("es_feriado", False)

    try:
        # Buscar si ya existe la asistencia para ese empleado y día
        db_asistencia = (
            db.query(models.Asistencia)
            .filter(
                models.Asistencia.empleado_id == asistencia.empleado_id,
                models.Asistencia.fecha == asistencia.fecha,
            )
            .first()
        )

        if db_asistencia:
            # Actualizar existente
            for key, value in data.items():
                setattr(db_asistencia, key, value)
        else:
            # Crear nuevo
            db_asistencia = models.Asistencia(**data)
            db.add(db_asistencia)

        # Manejo de Horas Extras Diurnas (Upsert)
        db_he_diurna = (
            db.query(models.HorasExtrasDiurnas)
            .filter(
                models.HorasExtrasDiurnas.empleado_id == asistencia.empleado_id,
                models.HorasExtrasDiurnas.fecha == asistencia.fecha,
            )
            .first()
        )
        if (he_diurnas or 0) > 0:
            if db_he_diurna:
                db_he_diurna.cantidad_horas = he_diurnas
            else:
                db_he_diurna = models.HorasExtrasDiurnas(
                    empleado_id=asistencia.empleado_id,
                    fecha=asistencia.fecha,
                    cantidad_horas=he_diurnas,
                )
                db.add(db_he_diurna)
        elif db_he_diurna:
            db.delete(db_he_diurna)

        # Manejo de Horas Extras Nocturnas (Upsert)
        db_he_nocturna = (
            db.query(models.HorasExtrasNocturnas)
            .filter(
                models.HorasExtrasNocturnas.empleado_id == asistencia.empleado_id,
                models.HorasExtrasNocturnas.fecha == asistencia.fecha,
            )
            .first()
        )
        if (he_nocturnas or 0) > 0:
            if db_he_nocturna:
                db_he_nocturna.cantidad_horas = he_nocturnas
            else:
                db_he_nocturna = models.HorasExtrasNocturnas(
                    empleado_id=asistencia.empleado_id,
                    fecha=asistencia.fecha,
                    cantidad_horas=he_nocturnas,
                )
                db.add(db_he_nocturna)
        elif db_he_nocturna:
            db.delete(db_he_nocturna)

        # Registrar feriado si se marcó el check
        if es_feriado:
            existe_feriado = (
                db.query(models.Feriado)
                .filter(models.Feriado.fecha == asistencia.fecha)
                .first()
            )
            if not existe_feriado:
                db_feriado = models.Feriado(
                    fecha=asistencia.fecha,
                    descripcion=asistencia.observacion or "Feriado",
                )
                db.add(db_feriado)

        db.commit()
        db.refresh(db_asistencia)
        return {
            "message": "Asistencia y novedades procesadas exitosamente",
            "id": db_asistencia.id,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/horas-extras", dependencies=[Depends(any_auth)])
def crear_horas_extras(extra: HorasExtrasCreate, db: Session = Depends(get_db)):
    try:
        if extra.tipo == "diurna":
            db_extra = models.HorasExtrasDiurnas(
                empleado_id=extra.empleado_id,
                fecha=extra.fecha,
                cantidad_horas=extra.cantidad_horas,
            )
        else:  # nocturna
            db_extra = models.HorasExtrasNocturnas(
                empleado_id=extra.empleado_id,
                fecha=extra.fecha,
                cantidad_horas=extra.cantidad_horas,
            )
        db.add(db_extra)
        db.commit()
        return {"message": f"Horas {extra.tipo}s registradas"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/feriados", dependencies=[Depends(coordinador_or_admin)])
def crear_feriado(feriado: FeriadoCreate, db: Session = Depends(get_db)):
    existe = (
        db.query(models.Feriado).filter(models.Feriado.fecha == feriado.fecha).first()
    )
    if existe:
        raise HTTPException(
            status_code=400, detail="Ya existe un feriado registrado para esa fecha."
        )

    db_feriado = models.Feriado(**feriado.model_dump())
    try:
        db.add(db_feriado)
        db.commit()
        return {"message": "Feriado registrado exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# --- NUEVAS RUTAS: PATCH (Actualización Parcial) ---


# 1. PATCH Asistencia (Búsqueda por empleado_id y fecha)
@router.patch("/{empleado_id}", dependencies=[Depends(any_auth)])
def actualizar_asistencia(
    empleado_id: int,
    fecha: date,
    datos: AsistenciaUpdate,
    db: Session = Depends(get_db),
):
    # Buscamos el registro por empleado_id y FECHA
    registro = (
        db.query(models.Asistencia)
        .filter(
            models.Asistencia.empleado_id == empleado_id,
            models.Asistencia.fecha == fecha,
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail="Registro no encontrado: El empleado_id y la Fecha no coinciden.",
        )

    # Validación de unicidad si intentas cambiar empleado o fecha
    update_data = datos.model_dump(exclude_unset=True)

    # Si se intenta cambiar fecha o empleado, verificar conflictos con OTROS registros
    new_fecha = update_data.get("fecha")
    new_emp = update_data.get("empleado_id")

    if new_fecha or new_emp:
        # Usamos los valores actuales si no se están actualizando
        search_fecha = new_fecha if new_fecha else registro.fecha
        search_emp = new_emp if new_emp else registro.empleado_id

        conflicto = (
            db.query(models.Asistencia)
            .filter(
                models.Asistencia.empleado_id == search_emp,
                models.Asistencia.fecha == search_fecha,
                models.Asistencia.id != registro.id,
            )
            .first()
        )

        if conflicto:
            raise HTTPException(
                status_code=400,
                detail=f"Conflictos: Ya existe registro para el empleado {search_emp} en la fecha {search_fecha}.",
            )

    # Actualizamos solo los campos enviados (Lógica PATCH)
    for key, value in update_data.items():
        setattr(registro, key, value)

    try:
        db.commit()
        return {"message": "Asistencia actualizada parcialmente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# 2. PATCH Horas Diurnas (Búsqueda por empleado_id y fecha)
@router.patch("/horas-extras/diurnas/{empleado_id}", dependencies=[Depends(any_auth)])
def actualizar_horas_diurnas(
    empleado_id: int,
    fecha: date,
    datos: HorasExtrasUpdate,
    db: Session = Depends(get_db),
):
    registro = (
        db.query(models.HorasExtrasDiurnas)
        .filter(
            models.HorasExtrasDiurnas.empleado_id == empleado_id,
            models.HorasExtrasDiurnas.fecha == fecha,
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail="Registro no encontrado: El empleado_id y la Fecha no coinciden.",
        )

    update_data = datos.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(registro, key, value)

    try:
        db.commit()
        return {"message": "Horas diurnas actualizadas parcialmente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# 3. PATCH Horas Nocturnas (Búsqueda por empleado_id y fecha)
@router.patch("/horas-extras/nocturnas/{empleado_id}", dependencies=[Depends(any_auth)])
def actualizar_horas_nocturnas(
    empleado_id: int,
    fecha: date,
    datos: HorasExtrasUpdate,
    db: Session = Depends(get_db),
):
    registro = (
        db.query(models.HorasExtrasNocturnas)
        .filter(
            models.HorasExtrasNocturnas.empleado_id == empleado_id,
            models.HorasExtrasNocturnas.fecha == fecha,
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail="Registro no encontrado: El empleado_id y la Fecha no coinciden.",
        )

    update_data = datos.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(registro, key, value)

    try:
        db.commit()
        return {"message": "Horas nocturnas actualizadas parcialmente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# 4. PATCH Feriados (Búsqueda solo por fecha, ya que fecha es única)
@router.patch("/feriados/{fecha}", dependencies=[Depends(coordinador_or_admin)])
def actualizar_feriado(
    fecha: date, datos: FeriadoUpdate, db: Session = Depends(get_db)
):
    registro = db.query(models.Feriado).filter(models.Feriado.fecha == fecha).first()

    if not registro:
        raise HTTPException(
            status_code=404,
            detail="Feriado no encontrado: La Fecha no coincide.",
        )

    update_data = datos.model_dump(exclude_unset=True)

    # Si cambias la fecha, validar que la nueva fecha no exista
    if "fecha" in update_data:
        conflicto = (
            db.query(models.Feriado)
            .filter(
                models.Feriado.fecha == update_data["fecha"],
                models.Feriado.id != registro.id,
            )
            .first()
        )
        if conflicto:
            raise HTTPException(
                status_code=400, detail="Ya existe un feriado en esa nueva fecha."
            )

    for key, value in update_data.items():
        setattr(registro, key, value)

    try:
        db.commit()
        return {"message": "Feriado actualizado parcialmente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# --- NUEVAS RUTAS: DELETE (Eliminación con Fecha) ---


# Asistencia DELETE (Búsqueda por empleado_id y fecha)
@router.delete("/{empleado_id}", dependencies=[Depends(supervisor_or_admin)])
def eliminar_asistencia(empleado_id: int, fecha: date, db: Session = Depends(get_db)):
    registro = (
        db.query(models.Asistencia)
        .filter(
            models.Asistencia.empleado_id == empleado_id,
            models.Asistencia.fecha == fecha,
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail="Registro no encontrado: El empleado_id y la Fecha no coinciden.",
        )

    try:
        db.delete(registro)
        db.commit()
        return {"message": "Registro de asistencia eliminado"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# Horas Diurnas DELETE (Búsqueda por empleado_id y fecha)
@router.delete(
    "/horas-extras/diurnas/{empleado_id}", dependencies=[Depends(supervisor_or_admin)]
)
def eliminar_horas_diurnas(
    empleado_id: int, fecha: date, db: Session = Depends(get_db)
):
    registro = (
        db.query(models.HorasExtrasDiurnas)
        .filter(
            models.HorasExtrasDiurnas.empleado_id == empleado_id,
            models.HorasExtrasDiurnas.fecha == fecha,
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail="Registro no encontrado: El empleado_id y la Fecha no coinciden.",
        )

    try:
        db.delete(registro)
        db.commit()
        return {"message": "Registro eliminado"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# Horas Nocturnas DELETE (Búsqueda por empleado_id y fecha)
@router.delete(
    "/horas-extras/nocturnas/{empleado_id}",
    dependencies=[Depends(supervisor_or_admin)],
)
def eliminar_horas_nocturnas(
    empleado_id: int, fecha: date, db: Session = Depends(get_db)
):
    registro = (
        db.query(models.HorasExtrasNocturnas)
        .filter(
            models.HorasExtrasNocturnas.empleado_id == empleado_id,
            models.HorasExtrasNocturnas.fecha == fecha,
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail="Registro no encontrado: El empleado_id y la Fecha no coinciden.",
        )

    try:
        db.delete(registro)
        db.commit()
        return {"message": "Registro eliminado"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# Feriados DELETE (Búsqueda solo por fecha, ya que fecha es única)
@router.delete("/feriados/{fecha}", dependencies=[Depends(coordinador_or_admin)])
def eliminar_feriado(fecha: date, db: Session = Depends(get_db)):
    registro = db.query(models.Feriado).filter(models.Feriado.fecha == fecha).first()

    if not registro:
        raise HTTPException(
            status_code=404,
            detail="Feriado no encontrado: La Fecha no coincide.",
        )

    try:
        db.delete(registro)
        db.commit()
        return {"message": "Registro eliminado"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ==================== RUTAS REPORTES NÓMINA DETALLADA ====================


@router.get(
    "/reporte-rango/empleado/{empleado_id}",
    response_model=ReporteNominaResponse,
    summary="Reporte de nómina detallado para un empleado específico",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_reporte_nomina_empleado(
    empleado_id: int,
    fecha_desde: date = Query(
        ..., description="Fecha de inicio del rango (YYYY-MM-DD)"
    ),
    fecha_hasta: date = Query(..., description="Fecha de fin del rango (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Obtiene el reporte detallado (Nómina) de un empleado específico en un rango de fechas.
    Genera automáticamente los días faltantes en el calendario.
    """
    if fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=400,
            detail="La fecha de inicio no puede ser mayor a la fecha de fin",
        )

    # 1. Buscar empleado
    from app.models.models_empleados import Empleado as EmpleadoReal

    emp = db.query(EmpleadoReal).filter(EmpleadoReal.id == empleado_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    # Autorización para el reporte
    # (Ya manejada por la dependencia a nivel de router si se prefiere,
    # pero aquí la pondré por endpoint)

    # 2. Generar el calendario
    dias_totales = (fecha_hasta - fecha_desde).days + 1
    rango_fechas = [fecha_desde + timedelta(days=i) for i in range(dias_totales)]
    nombres_dias = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]

    # 3. Consultar datos (Solo para este empleado)

    # Asistencias
    raw_asistencias = (
        db.query(models.ReporteAsistencia)
        .filter(
            models.ReporteAsistencia.id_empleado == empleado_id,
            models.ReporteAsistencia.fecha >= fecha_desde,
            models.ReporteAsistencia.fecha <= fecha_hasta,
        )
        .all()
    )
    # Mapeo por fecha (string)
    mapa_asistencia = {str(a.fecha): a for a in raw_asistencias}

    # Horas Extras Diurnas
    raw_he_diurnas = (
        db.query(models.HorasExtrasDiurnas)
        .filter(
            models.HorasExtrasDiurnas.empleado_id == empleado_id,
            models.HorasExtrasDiurnas.fecha >= fecha_desde,
            models.HorasExtrasDiurnas.fecha <= fecha_hasta,
        )
        .all()
    )
    mapa_he_diurnas = {str(he.fecha): float(he.cantidad_horas) for he in raw_he_diurnas}

    # Horas Extras Nocturnas
    raw_he_nocturnas = (
        db.query(models.HorasExtrasNocturnas)
        .filter(
            models.HorasExtrasNocturnas.empleado_id == empleado_id,
            models.HorasExtrasNocturnas.fecha >= fecha_desde,
            models.HorasExtrasNocturnas.fecha <= fecha_hasta,
        )
        .all()
    )
    mapa_he_nocturnas = {
        str(he.fecha): float(he.cantidad_horas) for he in raw_he_nocturnas
    }

    # Feriados (Globales)
    raw_feriados = (
        db.query(models.Feriado)
        .filter(
            models.Feriado.fecha >= fecha_desde, models.Feriado.fecha <= fecha_hasta
        )
        .all()
    )
    mapa_feriados = {str(f.fecha): f.descripcion for f in raw_feriados}

    # 4. Construir Reporte
    detalles_empleado = []
    sum_diurnas = 0.0
    sum_nocturnas = 0.0
    count_dias_trabajados = 0
    count_feriados_trabajados = 0

    for fecha_obj in rango_fechas:
        fecha_str = str(fecha_obj)

        # Recuperar datos
        asistencia = mapa_asistencia.get(fecha_str)
        he_diurna = mapa_he_diurnas.get(fecha_str, 0.0)
        he_nocturna = mapa_he_nocturnas.get(fecha_str, 0.0)
        es_feriado_global = fecha_str in mapa_feriados
        desc_feriado = mapa_feriados.get(fecha_str)

        # Lógica de estados
        estado_final = "S/R"
        if asistencia:
            estado_final = asistencia.estado
        elif es_feriado_global:
            estado_final = "Feriado"
        elif fecha_obj.weekday() == 6:  # Domingo
            estado_final = "Descanso"

        # Normalización de textos
        if estado_final.lower() in ["x", "asistió"]:  # 'x' es asistencia ahora
            estado_descrip = "Presente"
        elif estado_final.lower() in ["pvc", "falta"]:  # 'pvc' es falta
            estado_descrip = "Falta"
        elif estado_final.lower() in ["v", "vacaciones"]:
            estado_descrip = "Vacaciones"
        elif estado_final in ["S/R"] and (he_diurna > 0 or he_nocturna > 0):
            estado_descrip = "Presente (Solo HE)"
        else:
            estado_descrip = estado_final

        # Agregar detalle
        detalles_empleado.append(
            ReporteDetalleDia(
                fecha=fecha_obj,
                dia_semana=nombres_dias[fecha_obj.weekday()],
                estado=estado_descrip,
                horas_extras_diurnas=he_diurna,
                horas_extras_nocturnas=he_nocturna,
                es_feriado=es_feriado_global,
                descripcion_feriado=desc_feriado,
            )
        )

        # Sumar Totales
        sum_diurnas += he_diurna
        sum_nocturnas += he_nocturna

        # Conteo días trabajados ('x' o 'presente' o tiene horas extras)
        if (
            estado_descrip in ["Presente", "Presente (Solo HE)"]
            or he_diurna > 0
            or he_nocturna > 0
        ):
            count_dias_trabajados += 1
            if es_feriado_global:
                count_feriados_trabajados += 1

    # Empaquetar respuesta
    reporte_emp = ReporteNominaEmpleado(
        empleado_id=emp.id,
        codigo=emp.codigo,
        nombre_completo=f"{emp.nombre} {emp.apellido}",
        cargo=emp.cargo or "Sin Cargo",
        detalles=detalles_empleado,
        total_horas_extras_diurnas=sum_diurnas,
        total_horas_extras_nocturnas=sum_nocturnas,
        total_horas_extras_global=sum_diurnas + sum_nocturnas,
        total_dias_trabajados=count_dias_trabajados,
        total_feriados_trabajados=count_feriados_trabajados,
    )

    return ReporteNominaResponse(
        success=True,
        fecha_inicio=fecha_desde,
        fecha_fin=fecha_hasta,
        total_registros=1,
        data=[reporte_emp],
    )


@router.get(
    "/reporte-rango/general",
    response_model=ReporteNominaResponse,
    summary="Reporte detallado de nómina por rango de fechas (Todos los empleados)",
    dependencies=[Depends(any_auth)],
)
def get_reporte_nomina_general(
    fecha_desde: date = Query(
        ..., description="Fecha de inicio del rango (YYYY-MM-DD)"
    ),
    fecha_hasta: date = Query(..., description="Fecha de fin del rango (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Reporte General de Nómina: Todos los empleados.
    Maneja estados: 'x' (Asistencia), 'pvc' (Falta), 'v' (Vacaciones).
    """
    from app.models.models_empleados import Empleado as EmpleadoReal

    # Obtener TODOS los empleados
    todos_empleados = db.query(EmpleadoReal).order_by(EmpleadoReal.apellido).all()

    return generar_reporte_nomina_comun(fecha_desde, fecha_hasta, todos_empleados, db)


@router.get(
    "/reporte-rango/coordinadores",
    response_model=ReporteNominaResponse,
    summary="Reporte detallado de nómina (Solo Coordinadores y Supervisores)",
    dependencies=[Depends(coordinador_or_admin)],
)
def get_reporte_nomina_coordinadores(
    fecha_desde: date = Query(
        ..., description="Fecha de inicio del rango (YYYY-MM-DD)"
    ),
    fecha_hasta: date = Query(..., description="Fecha de fin del rango (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Reporte de Nómina filtrado para Coordinadores y Supervisores.
    """
    from app.models.models_empleados import Empleado as EmpleadoReal

    # Filtro por cargo
    empleados_filtrados = (
        db.query(EmpleadoReal)
        .filter(
            or_(
                EmpleadoReal.cargo.ilike("%coordinador%"),
                EmpleadoReal.cargo.ilike("%supervisor%"),
            )
        )
        .order_by(EmpleadoReal.apellido)
        .all()
    )

    return generar_reporte_nomina_comun(
        fecha_desde, fecha_hasta, empleados_filtrados, db
    )


def generar_reporte_nomina_comun(
    fecha_desde: date, fecha_hasta: date, empleados: list, db: Session
) -> ReporteNominaResponse:
    """
    Función helper que contiene la lógica CORE de la generación de la nómina.
    Evita duplicar código entre los endpoints.
    """
    if fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=400,
            detail="La fecha de inicio no puede ser mayor a la fecha de fin",
        )

    # 1. Generar la línea de tiempo
    dias_totales = (fecha_hasta - fecha_desde).days + 1
    rango_fechas = [fecha_desde + timedelta(days=i) for i in range(dias_totales)]
    nombres_dias = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]

    # 2. BULK FETCH: Traer datos masivos del rango
    # Convertimos todo a string para evitar problemas de tipos

    # Asistencias
    raw_asistencias = (
        db.query(models.ReporteAsistencia)
        .filter(
            models.ReporteAsistencia.fecha >= fecha_desde,
            models.ReporteAsistencia.fecha <= fecha_hasta,
        )
        .all()
    )
    mapa_asistencia = {(a.id_empleado, str(a.fecha)): a for a in raw_asistencias}

    # HE Diurnas
    raw_he_diurnas = (
        db.query(models.HorasExtrasDiurnas)
        .filter(
            models.HorasExtrasDiurnas.fecha >= fecha_desde,
            models.HorasExtrasDiurnas.fecha <= fecha_hasta,
        )
        .all()
    )
    mapa_he_diurnas = {
        (he.empleado_id, str(he.fecha)): float(he.cantidad_horas)
        for he in raw_he_diurnas
    }

    # HE Nocturnas
    raw_he_nocturnas = (
        db.query(models.HorasExtrasNocturnas)
        .filter(
            models.HorasExtrasNocturnas.fecha >= fecha_desde,
            models.HorasExtrasNocturnas.fecha <= fecha_hasta,
        )
        .all()
    )
    mapa_he_nocturnas = {
        (he.empleado_id, str(he.fecha)): float(he.cantidad_horas)
        for he in raw_he_nocturnas
    }

    # Feriados
    raw_feriados = (
        db.query(models.Feriado)
        .filter(
            models.Feriado.fecha >= fecha_desde, models.Feriado.fecha <= fecha_hasta
        )
        .all()
    )
    mapa_feriados = {str(f.fecha): f.descripcion for f in raw_feriados}

    # 3. Construcción del Reporte
    reportes_finales = []

    for emp in empleados:
        detalles_empleado = []

        sum_diurnas = 0.0
        sum_nocturnas = 0.0
        count_dias_trabajados = 0
        count_feriados_trabajados = 0

        for fecha_obj in rango_fechas:
            fecha_str = str(fecha_obj)

            # Recuperar datos (O(1))
            asistencia = mapa_asistencia.get((emp.id, fecha_str))
            he_diurna = mapa_he_diurnas.get((emp.id, fecha_str), 0.0)
            he_nocturna = mapa_he_nocturnas.get((emp.id, fecha_str), 0.0)
            # Lógica de Feriados (BD + Sábados automáticos)
            es_sabado = fecha_obj.weekday() == 5
            es_feriado_bd = fecha_str in mapa_feriados

            # Es feriado si está en BD O es sábado
            es_feriado_global = es_feriado_bd or es_sabado

            desc_feriado = mapa_feriados.get(fecha_str)
            if es_sabado and not desc_feriado:
                desc_feriado = "Sábado (Descanso/Feriado)"

            # Lógica de estados principales
            estado_original = "S/R"
            if asistencia:
                estado_original = asistencia.estado
            elif es_feriado_global:
                estado_original = "Feriado"
            elif fecha_obj.weekday() == 6:  # Domingo
                estado_original = "Descanso"

            # Normalización
            estado_lower = estado_original.lower()

            if estado_lower in ["x", "asistió", "presente"]:
                estado_descrip = "Presente"
            elif estado_lower in ["pvc", "falta"]:
                estado_descrip = "Falta"
            elif estado_lower in ["v", "vacaciones"]:
                estado_descrip = "Vacaciones"
            elif estado_original == "S/R" and (he_diurna > 0 or he_nocturna > 0):
                estado_descrip = "Presente (Solo HE)"
            else:
                estado_descrip = estado_original

            # Objeto Detalle
            detalles_empleado.append(
                ReporteDetalleDia(
                    fecha=fecha_obj,
                    dia_semana=nombres_dias[fecha_obj.weekday()],
                    estado=estado_descrip,
                    horas_extras_diurnas=he_diurna,
                    horas_extras_nocturnas=he_nocturna,
                    es_feriado=es_feriado_global,
                    descripcion_feriado=desc_feriado,
                )
            )

            # Contadores
            sum_diurnas += he_diurna
            sum_nocturnas += he_nocturna

            if (
                estado_descrip in ["Presente", "Presente (Solo HE)"]
                or he_diurna > 0
                or he_nocturna > 0
            ):
                count_dias_trabajados += 1
                if es_feriado_global:
                    count_feriados_trabajados += 1

        reportes_finales.append(
            ReporteNominaEmpleado(
                empleado_id=emp.id,
                codigo=emp.codigo,
                nombre_completo=f"{emp.nombre} {emp.apellido}",
                cargo=emp.cargo or "Sin Cargo",
                detalles=detalles_empleado,
                total_horas_extras_diurnas=sum_diurnas,
                total_horas_extras_nocturnas=sum_nocturnas,
                total_horas_extras_global=sum_diurnas + sum_nocturnas,
                total_dias_trabajados=count_dias_trabajados,
                total_feriados_trabajados=count_feriados_trabajados,
            )
        )

    return ReporteNominaResponse(
        success=True,
        fecha_inicio=fecha_desde,
        fecha_fin=fecha_hasta,
        total_registros=len(reportes_finales),
        data=reportes_finales,
    )
