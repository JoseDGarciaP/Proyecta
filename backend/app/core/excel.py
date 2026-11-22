"""Hoja de Excel (.xlsx) lista para descargar, con título y fecha de generación (Ep6-Hu3, Ep4-Hu16, Ep4-Hu30)."""

import io
from collections.abc import Iterable, Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Response
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

ZONA = ZoneInfo("America/Bogota")
TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def generado() -> str:
    return datetime.now(ZONA).strftime("%Y-%m-%d %H:%M")


def libro(hojas: Sequence[tuple[str, Sequence[str], Iterable[Sequence]]], titulo: str) -> bytes:
    """Cada hoja: (nombre, encabezados, filas). La primera fila dice qué es y cuándo se generó."""
    wb = Workbook()
    wb.remove(wb.active)
    for nombre, encabezados, filas in hojas:
        ws = wb.create_sheet(nombre[:31])
        ws.append([f"{titulo} · generado el {generado()} (hora de Colombia)"])
        ws["A1"].font = Font(bold=True)
        ws.append([])
        ws.append(list(encabezados))
        for celda in ws[3]:
            celda.font = Font(bold=True)
        anchos = [len(str(e)) for e in encabezados]
        for fila in filas:
            fila = ["" if v is None else v for v in fila]
            ws.append(fila)
            anchos = [max(a, min(60, len(str(v)))) for a, v in zip(anchos, fila)]
        for i, ancho in enumerate(anchos, start=1):
            ws.column_dimensions[get_column_letter(i)].width = ancho + 2
        ws.freeze_panes = "A4"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def respuesta(nombre_archivo: str, contenido: bytes) -> Response:
    return Response(content=contenido, media_type=TIPO_XLSX,
                    headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'})
