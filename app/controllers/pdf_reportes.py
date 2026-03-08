from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth_deps import coordinador_or_admin
from app.controllers.asistencia import generar_reporte_nomina_comun
from app.models.models_empleados import Empleado as EmpleadoReal
import io
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Image,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

router = APIRouter()

# --- CONSTANTES ---
CARGOS_JEFES = [
    "DIRECTOR AREA DE MANTENIMIENTO",
    "DIRECTOR DE MANTENIMIENTO",
    "SUPERVISOR DE MANTENIMIENTO",
    "COORDINADOR",
]

COLOR_HEADER_AZUL = colors.HexColor("#0070C0")
COLOR_HEADER_AMARILLO = colors.HexColor("#FFCC00")
COLOR_HEADER_GRIS = colors.HexColor("#E7E6E6")
COLOR_ROJO = colors.red


# --- HELPERS DE CLASIFICACIÓN (Reusada) ---
def clasificar_empleados(reporte_data):
    """Helper para separar empleados en listas según cargo/turno"""
    grupos = {"Jefes": [], "Diurno": [], "Nocturno": []}

    for reporte_emp in reporte_data.data:
        # Preparar data plana
        lista_asist = []
        lista_hed = []
        lista_hen = []

        detalles = reporte_emp.detalles[:7]

        # Helper fmt
        def fmt_int(num):
            if isinstance(num, (int, float)) and num > 0:
                return int(round(num))
            return ""

        for det in detalles:
            # Mapeo Visual
            est = det.estado.upper()
            txt = est[:3]
            if "PRESENTE" in est:
                txt = "X"
            elif "FALTA" in est:
                txt = "PVC"
            elif "VACACIONES" in est:
                txt = "V"
            elif "FERIADO" in est:
                txt = "F"
            elif "DESCANSO" in est:
                txt = ""

            lista_asist.append(txt)
            lista_hed.append(fmt_int(det.horas_extras_diurnas))
            lista_hen.append(fmt_int(det.horas_extras_nocturnas))

        # Rellenar
        while len(lista_asist) < 7:
            lista_asist.append("")
            lista_hed.append("")
            lista_hen.append("")

        emp_dict = {
            "Nombre": f"{reporte_emp.nombre_completo}",
            "Codigo": reporte_emp.codigo,
            "Asistencia": lista_asist,
            "HE_Diurna": lista_hed,
            "HE_Nocturna": lista_hen,
            "Feriado": reporte_emp.total_feriados_trabajados
            if reporte_emp.total_feriados_trabajados > 0
            else "",
            "Total_HE": reporte_emp.total_horas_extras_global
            if reporte_emp.total_horas_extras_global > 0
            else "",
        }

        # LÓGICA DE CLASIFICACIÓN
        cargo_up = (reporte_emp.cargo or "").upper()
        es_jefe = any(c in cargo_up for c in CARGOS_JEFES)

        if es_jefe:
            grupos["Jefes"].append(emp_dict)
        else:
            total_noc = reporte_emp.total_horas_extras_nocturnas
            total_diu = reporte_emp.total_horas_extras_diurnas
            if total_noc > 0 and total_noc >= total_diu:
                grupos["Nocturno"].append(emp_dict)
            else:
                grupos["Diurno"].append(emp_dict)

    return grupos


# --- GENERACION PDF ---


def generar_header_pdf(
    elements, logo_bytes, titulo_principal, fecha_desde, fecha_hasta, width
):
    styles = getSampleStyleSheet()

    # -- Logo --
    if logo_bytes:
        try:
            im = Image(io.BytesIO(logo_bytes))
            # Ajustar tamaño logo (mantener relacion de aspecto aprox 1200x200 -> 6:1)
            # En PDF un ancho de 6cm x 1cm seria razonable o mas grande.
            # Ancho disponible ~25cm.
            # Ancho basado en parametro width (aprox 25cm para landscape letter)
            # Restamos un poco de margen si es necesario, o usamos el width directo
            im.drawWidth = width
            im.drawHeight = 1.6 * cm
            im.hAlign = "LEFT"
            elements.append(im)
            elements.append(Spacer(1, 0.2 * cm))
        except:
            pass

    # -- Titulos --
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        alignment=TA_CENTER,
        leading=16,
    )
    subtitle_style = ParagraphStyle(
        "SubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.white,
        backColor=COLOR_HEADER_AZUL,
        leading=14,
        spaceBefore=4,
    )

    elements.append(Paragraph(titulo_principal, title_style))

    fecha_str = f"SEMANA DEL {fecha_desde.strftime('%d/%m/%Y')} AL {fecha_hasta.strftime('%d/%m/%Y')}"
    elements.append(Paragraph(fecha_str, subtitle_style))
    elements.append(Spacer(1, 0.5 * cm))


def crear_tabla_asistencia_pdf(empleados_list, titulo_seccion):
    if not empleados_list:
        return None

    # Columnas: Nombre, Codigo, [7 Asistencia], [7 HE D], [7 HE N], FE, Total
    # Total Cols: 1 + 1 + 7 + 7 + 7 + 1 + 1 = 25 columnas

    # Headers
    headers_row_1 = (
        ["", ""]
        + ["ASISTENCIA"] * 7
        + ["H.E. DIURNAS"] * 7
        + ["H.E. NOCTURNAS"] * 7
        + ["", ""]
    )
    # Dias
    dias = ["L", "M", "M", "J", "V", "S", "D"]
    headers_row_2 = (
        ["Nombre del Trabajador", "Código"] + dias + dias + dias + ["FE", "Total"]
    )

    data = [
        [titulo_seccion],  # Row 0: Section Title
        headers_row_1,  # Row 1: Group Headers
        headers_row_2,  # Row 2: Sub Headers
    ]

    # Data Rows
    for emp in empleados_list:
        row = [emp["Nombre"], emp["Codigo"]]
        row.extend(emp["Asistencia"])
        row.extend(emp["HE_Diurna"])
        row.extend(emp["HE_Nocturna"])
        row.append(emp["Feriado"])
        row.append(emp["Total_HE"])
        data.append(row)

    # Column Widths (Aprox fit in landscape letter ~25cm usable)
    # 25 cols.
    # Name: 4cm, Code: 1.5cm. Rest 23 cols share remaining 19.5cm -> ~0.8cm each
    col_widths = [4.5 * cm, 1.8 * cm] + [0.75 * cm] * 21 + [0.8 * cm, 1.0 * cm]

    t = Table(data, colWidths=col_widths, repeatRows=3)

    # Styles
    base_style = [
        ("GRID", (0, 1), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Section Title (Row 0)
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_AMARILLO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        # Group Headers (Row 1)
        ("SPAN", (0, 1), (1, 1)),  # Blank span
        ("SPAN", (2, 1), (8, 1)),  # Asist
        ("SPAN", (9, 1), (15, 1)),  # HE D
        ("SPAN", (16, 1), (22, 1)),  # HE N
        ("BACKGROUND", (0, 1), (-1, 2), COLOR_HEADER_GRIS),
        ("FONTNAME", (0, 1), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 2), 6),
    ]

    # Conditional formatting for rows
    for i, row_data in enumerate(data[3:], start=3):
        # Asistencia cols (index 2 to 8)
        for c in range(2, 9):
            val = str(row_data[c]).upper().strip()
            if val not in ["X", ""]:
                base_style.append(("TEXTCOLOR", (c, i), (c, i), COLOR_ROJO))
                base_style.append(("FONTNAME", (c, i), (c, i), "Helvetica-Bold"))

        # Feriados col (index 23)
        val_fe = row_data[23]
        if val_fe != "":
            base_style.append(("TEXTCOLOR", (23, i), (23, i), COLOR_ROJO))
            base_style.append(("FONTNAME", (23, i), (23, i), "Helvetica-Bold"))

    t.setStyle(TableStyle(base_style))
    return t


def crear_tabla_resumen_he_pdf(empleados_list, titulo_seccion):
    if not empleados_list:
        return None

    # Columnas: Nombre, Codigo, [7 HE D], [7 HE N], FE, Total
    # Total Cols: 1 + 1 + 7 + 7 + 1 + 1 = 18 Columns

    headers_row_1 = ["", ""] + ["H.E. DIURNAS"] * 7 + ["H.E. NOCTURNAS"] * 7 + ["", ""]
    dias = ["L", "M", "M", "J", "V", "S", "D"]
    headers_row_2 = ["Nombre del Trabajador", "Código"] + dias + dias + ["FE", "Total"]

    data = [[titulo_seccion], headers_row_1, headers_row_2]

    for emp in empleados_list:
        row = [emp["Nombre"], emp["Codigo"]]
        row.extend(emp["HE_Diurna"])
        row.extend(emp["HE_Nocturna"])
        row.append(emp["Feriado"])

        # Calcular Total
        # Calcular Total
        def sum_clean(lista):
            # Asumimos que lista ya contiene enteros o strings vacios por el clasificar_empleados
            # Pero para sumar necesitamos numeros
            s = 0
            for x in lista:
                if isinstance(x, (int, float)):
                    s += x
            return s

        total = sum_clean(emp["HE_Diurna"]) + sum_clean(emp["HE_Nocturna"])
        row.append(int(round(total)) if total > 0 else "")

        data.append(row)

    # Widths
    # 18 cols. Name: 5cm, Code: 2cm. Rest 16 cols share ~18cm -> 1.1cm
    col_widths = [5.5 * cm, 2.0 * cm] + [0.9 * cm] * 14 + [0.9 * cm, 1.2 * cm]

    t = Table(data, colWidths=col_widths, repeatRows=3)

    base_style = [
        ("GRID", (0, 1), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_AMARILLO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("SPAN", (0, 1), (1, 1)),
        ("SPAN", (2, 1), (8, 1)),  # HE D
        ("SPAN", (9, 1), (15, 1)),  # HE N
        ("BACKGROUND", (0, 1), (-1, 2), COLOR_HEADER_GRIS),
        ("FONTNAME", (0, 1), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 2), 6),
    ]

    # Conditional FE Red
    for i, row_data in enumerate(data[3:], start=3):
        val_fe = row_data[16]  # Index 16 is FE
        if val_fe != "":
            base_style.append(("TEXTCOLOR", (16, i), (16, i), COLOR_ROJO))
            base_style.append(("FONTNAME", (16, i), (16, i), "Helvetica-Bold"))

    t.setStyle(TableStyle(base_style))
    return t


def agregar_firma_fernelis(elements):
    elements.append(Spacer(1, 1.5 * cm))
    styles = getSampleStyleSheet()
    firma_style = ParagraphStyle(
        "Firma",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=11,
    )

    elements.append(
        Paragraph("________________________________________________", firma_style)
    )
    elements.append(Paragraph("FERNELIS", firma_style))


def build_pdf_response(filename, elements):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=1 * cm,
        leftMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
    )
    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- ENDPOINTS ---


@router.post(
    "/reporte-pdf/empleados",
    summary="PDF Nómina (Empleados)",
    dependencies=[Depends(coordinador_or_admin)],
)
async def pdf_nomina_empleados(
    fecha_desde: date = Form(...),
    fecha_hasta: date = Form(...),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    todos_empleados = db.query(EmpleadoReal).order_by(EmpleadoReal.apellido).all()
    reporte_data = generar_reporte_nomina_comun(
        fecha_desde, fecha_hasta, todos_empleados, db
    )
    logo_bytes = await logo.read() if logo else None
    grupos = clasificar_empleados(reporte_data)

    elements = []
    # Tamaño del logo solicitado: 30 cm
    logo_width = 24 * cm
    generar_header_pdf(
        elements,
        logo_bytes,
        "REPORTE DE ASISTENCIAS - OPERATIVOS",
        fecha_desde,
        fecha_hasta,
        logo_width,
    )

    if grupos["Diurno"]:
        t = crear_tabla_asistencia_pdf(grupos["Diurno"], "TURNO DIURNO")
        elements.append(t)
        elements.append(Spacer(1, 0.5 * cm))

    if grupos["Nocturno"]:
        t = crear_tabla_asistencia_pdf(grupos["Nocturno"], "TURNO NOCTURNO")
        elements.append(t)
        elements.append(Spacer(1, 0.5 * cm))

    agregar_firma_fernelis(elements)

    return build_pdf_response(f"Reporte_Empleados_{fecha_desde}.pdf", elements)


@router.post(
    "/reporte-pdf/jefes",
    summary="PDF Nómina (Jefes)",
    dependencies=[Depends(coordinador_or_admin)],
)
async def pdf_nomina_jefes(
    fecha_desde: date = Form(...),
    fecha_hasta: date = Form(...),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    todos_empleados = db.query(EmpleadoReal).order_by(EmpleadoReal.apellido).all()
    reporte_data = generar_reporte_nomina_comun(
        fecha_desde, fecha_hasta, todos_empleados, db
    )
    logo_bytes = await logo.read() if logo else None
    grupos = clasificar_empleados(reporte_data)

    elements = []
    # Tamaño del logo solicitado: 30 cm
    logo_width = 30 * cm
    # Usar logo supervisores si existiera, aqui asumimos que llega en 'logo'
    generar_header_pdf(
        elements,
        logo_bytes,
        "REPORTE DE ASISTENCIAS - JEFATURA",
        fecha_desde,
        fecha_hasta,
        logo_width,
    )

    if grupos["Jefes"]:
        t = crear_tabla_asistencia_pdf(
            grupos["Jefes"], "DIRECCIÓN Y SUPERVISIÓN DE MANTENIMIENTO"
        )
        elements.append(t)
        elements.append(Spacer(1, 0.5 * cm))

    agregar_firma_fernelis(elements)

    return build_pdf_response(f"Reporte_Jefes_{fecha_desde}.pdf", elements)


@router.post(
    "/reporte-pdf/resumen-he/empleados",
    summary="PDF Resumen HE (Empleados)",
    dependencies=[Depends(coordinador_or_admin)],
)
async def pdf_resumen_he_empleados(
    fecha_desde: date = Form(...),
    fecha_hasta: date = Form(...),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    todos_empleados = db.query(EmpleadoReal).order_by(EmpleadoReal.apellido).all()
    reporte_data = generar_reporte_nomina_comun(
        fecha_desde, fecha_hasta, todos_empleados, db
    )
    logo_bytes = await logo.read() if logo else None
    grupos = clasificar_empleados(reporte_data)

    elements = []
    # Tamaño del logo solicitado: 30 cm
    logo_width = 30 * cm
    generar_header_pdf(
        elements,
        logo_bytes,
        "RESUMEN HORAS EXTRAS - OPERATIVOS",
        fecha_desde,
        fecha_hasta,
        logo_width,
    )

    if grupos["Diurno"]:
        t = crear_tabla_resumen_he_pdf(grupos["Diurno"], "TURNO DIURNO")
        elements.append(t)
        elements.append(Spacer(1, 0.5 * cm))

    if grupos["Nocturno"]:
        t = crear_tabla_resumen_he_pdf(grupos["Nocturno"], "TURNO NOCTURNO")
        elements.append(t)
        elements.append(Spacer(1, 0.5 * cm))

    agregar_firma_fernelis(elements)

    return build_pdf_response(f"Resumen_HE_Empleados_{fecha_desde}.pdf", elements)


@router.post(
    "/reporte-pdf/resumen-he/jefes",
    summary="PDF Resumen HE (Jefes)",
    dependencies=[Depends(coordinador_or_admin)],
)
async def pdf_resumen_he_jefes(
    fecha_desde: date = Form(...),
    fecha_hasta: date = Form(...),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    todos_empleados = db.query(EmpleadoReal).order_by(EmpleadoReal.apellido).all()
    reporte_data = generar_reporte_nomina_comun(
        fecha_desde, fecha_hasta, todos_empleados, db
    )
    logo_bytes = await logo.read() if logo else None
    grupos = clasificar_empleados(reporte_data)

    elements = []
    # Tamaño del logo solicitado: 30 cm
    logo_width = 30 * cm
    generar_header_pdf(
        elements,
        logo_bytes,
        "RESUMEN HORAS EXTRAS - JEFATURA",
        fecha_desde,
        fecha_hasta,
        logo_width,
    )

    if grupos["Jefes"]:
        t = crear_tabla_resumen_he_pdf(
            grupos["Jefes"], "DIRECCIÓN Y SUPERVISIÓN DE MANTENIMIENTO"
        )
        elements.append(t)
        elements.append(Spacer(1, 0.5 * cm))

    agregar_firma_fernelis(elements)

    return build_pdf_response(f"Resumen_HE_Jefes_{fecha_desde}.pdf", elements)
