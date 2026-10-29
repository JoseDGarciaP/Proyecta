"""Envío de correos por SMTP o por la API HTTPS de Brevo.

Con BREVO_API_KEY se usa Brevo (sirve donde el proveedor bloquea los puertos SMTP, como el plan
gratuito de Render). Sin Brevo ni SMTP_HOST no se envía nada: el mensaje se escribe en la consola de la API
(útil en desarrollo) y queda en `enviados`, que las pruebas revisan.
"""

import html
import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import parseaddr

import httpx

from app.core.config import get_settings

log = logging.getLogger("proyecta.correo")


@dataclass
class Correo:
    para: str
    asunto: str
    texto: str
    html: str


enviados: list[Correo] = []


BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def _enviar_brevo(correo: Correo) -> None:
    settings = get_settings()
    nombre, direccion = parseaddr(settings.smtp_remitente or settings.smtp_usuario)
    try:
        respuesta = httpx.post(
            BREVO_URL,
            headers={"api-key": settings.brevo_api_key, "accept": "application/json"},
            json={
                "sender": {"name": nombre or "Proyecta", "email": direccion},
                "to": [{"email": correo.para}],
                "subject": correo.asunto,
                "textContent": correo.texto,
                "htmlContent": correo.html,
            },
            timeout=20,
        )
        respuesta.raise_for_status()
    except httpx.HTTPError:
        log.exception("No se pudo enviar el correo a %s por Brevo", correo.para)


def enviar(correo: Correo) -> None:
    settings = get_settings()
    if settings.brevo_api_key:
        _enviar_brevo(correo)
        return
    if not settings.smtp_host:
        enviados.append(correo)
        log.warning("SMTP sin configurar. Correo para %s: %s\n%s", correo.para, correo.asunto, correo.texto)
        return
    mensaje = EmailMessage()
    mensaje["From"] = settings.smtp_remitente or settings.smtp_usuario
    mensaje["To"] = correo.para
    mensaje["Subject"] = correo.asunto
    mensaje.set_content(correo.texto)
    mensaje.add_alternative(correo.html, subtype="html")
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            if settings.smtp_usuario:
                smtp.login(settings.smtp_usuario, settings.smtp_password)
            smtp.send_message(mensaje)
    except (OSError, smtplib.SMTPException):
        # Se ejecuta en segundo plano: el registro ya respondió. Se puede pedir otro enlace.
        log.exception("No se pudo enviar el correo a %s", correo.para)


def verificacion(para: str, nombre: str, enlace: str, horas: int) -> Correo:
    texto = (
        f"Hola, {nombre}:\n\nPara activar tu cuenta en Proyecta abre este enlace:\n{enlace}\n\n"
        f"El enlace vence en {horas} horas. Si no creaste la cuenta, ignora este mensaje."
    )
    # El nombre lo escribe quien se registra: se escapa para que no pueda inyectar HTML.
    nombre_html, enlace_html = html.escape(nombre), html.escape(enlace, quote=True)
    cuerpo = (
        f"<p>Hola, {nombre_html}:</p><p>Para activar tu cuenta en <b>Proyecta</b> confirma tu correo:</p>"
        f'<p><a href="{enlace_html}" style="background:#2563eb;color:#fff;padding:10px 18px;border-radius:8px;'
        f'text-decoration:none">Confirmar mi correo</a></p>'
        f"<p style=\"color:#64748b;font-size:13px\">El enlace vence en {horas} horas. "
        f"Si no creaste la cuenta, ignora este mensaje.</p>"
    )
    return Correo(para=para, asunto="Confirma tu correo en Proyecta", texto=texto, html=cuerpo)


def restablecer(para: str, nombre: str, enlace: str, minutos: int) -> Correo:
    texto = (
        f"Hola, {nombre}:\n\nPediste cambiar tu contraseña de Proyecta. Abre este enlace para elegir una nueva:\n"
        f"{enlace}\n\nEl enlace vence en {minutos} minutos y sirve una sola vez. "
        f"Si no lo pediste, ignora este mensaje: tu contraseña sigue igual."
    )
    nombre_html, enlace_html = html.escape(nombre), html.escape(enlace, quote=True)
    cuerpo = (
        f"<p>Hola, {nombre_html}:</p><p>Pediste cambiar tu contraseña de <b>Proyecta</b>.</p>"
        f'<p><a href="{enlace_html}" style="background:#2563eb;color:#fff;padding:10px 18px;border-radius:8px;'
        f'text-decoration:none">Elegir una contraseña nueva</a></p>'
        f"<p style=\"color:#64748b;font-size:13px\">El enlace vence en {minutos} minutos y sirve una sola vez. "
        f"Si no lo pediste, ignora este mensaje: tu contraseña sigue igual.</p>"
    )
    return Correo(para=para, asunto="Restablece tu contraseña de Proyecta", texto=texto, html=cuerpo)


def alerta(para: str, nombre: str, asunto: str, titulo: str, parrafos: list[str], enlace: str, boton: str,
           detalles: list[tuple[str, str]] | None = None, apagable: bool = True) -> Correo:
    """Correo de aviso de la plataforma (solicitudes, respuestas, mensajes, cambios de cuenta).

    `parrafos` y `detalles` pueden traer texto escrito por otras personas (mensajes, motivos): todo se escapa.
    """
    detalles = detalles or []
    pie = (
        "Puedes elegir qué correos recibir en tu perfil de Proyecta (sección «Notificaciones»)."
        if apagable else "Este aviso es sobre tu cuenta y se envía siempre."
    )
    texto = "\n\n".join(
        [f"Hola, {nombre}:", titulo, *parrafos]
        + (["\n".join(f"{k}: {v}" for k, v in detalles)] if detalles else [])
        + [f"{boton}: {enlace}", pie]
    )
    e = html.escape
    filas = "".join(
        f'<tr><td style="padding:4px 12px 4px 0;color:#64748b;vertical-align:top;white-space:nowrap">{e(k)}</td>'
        f'<td style="padding:4px 0;color:#0f172a">{e(v)}</td></tr>'
        for k, v in detalles
    )
    cuerpo = (
        '<div style="font-family:Segoe UI,Arial,sans-serif;max-width:560px;color:#0f172a;line-height:1.5">'
        f"<p>Hola, {e(nombre)}:</p>"
        f'<p style="font-size:17px;font-weight:600;margin:16px 0 8px">{e(titulo)}</p>'
        + "".join(f"<p>{e(p)}</p>" for p in parrafos)
        + (f'<table style="border-collapse:collapse;font-size:14px;margin:12px 0">{filas}</table>' if filas else "")
        + f'<p style="margin:20px 0"><a href="{e(enlace, quote=True)}" style="background:#2563eb;color:#fff;'
        f'padding:10px 18px;border-radius:8px;text-decoration:none">{e(boton)}</a></p>'
        f'<p style="color:#64748b;font-size:12px;border-top:1px solid #e2e8f0;padding-top:12px">{e(pie)}</p>'
        "</div>"
    )
    return Correo(para=para, asunto=asunto, texto=texto, html=cuerpo)


def cuenta_creada(para: str, nombre: str, enlace: str, horas: int) -> Correo:
    texto = (
        f"Hola, {nombre}:\n\nUn administrador te creó una cuenta en Proyecta. Para empezar, elige tu contraseña aquí:\n"
        f"{enlace}\n\nEl enlace vence en {horas} horas. Si vence, usa «¿Olvidaste tu contraseña?» en la página de ingreso."
    )
    nombre_html, enlace_html = html.escape(nombre), html.escape(enlace, quote=True)
    cuerpo = (
        f"<p>Hola, {nombre_html}:</p><p>Un administrador te creó una cuenta en <b>Proyecta</b>.</p>"
        f'<p><a href="{enlace_html}" style="background:#2563eb;color:#fff;padding:10px 18px;border-radius:8px;'
        f'text-decoration:none">Elegir mi contraseña</a></p>'
        f"<p style=\"color:#64748b;font-size:13px\">El enlace vence en {horas} horas. Si vence, usa "
        f"«¿Olvidaste tu contraseña?» en la página de ingreso.</p>"
    )
    return Correo(para=para, asunto="Tu cuenta en Proyecta está lista", texto=texto, html=cuerpo)


def invitacion_proyecto(para: str, quien_invita: str, proyecto: str, detalles: list[tuple[str, str]], enlace: str,
                        dias: int) -> Correo:
    """Invitación a un proyecto para alguien que aún no tiene cuenta en Proyecta."""
    texto = "\n\n".join([
        "Hola:",
        f"{quien_invita} te invitó a hacer parte del equipo del proyecto «{proyecto}» en Proyecta.",
        "\n".join(f"{k}: {v}" for k, v in detalles),
        f"Para ver la invitación y aceptarla (o rechazarla) abre este enlace:\n{enlace}",
        "Si aceptas, crea tu cuenta con este mismo correo y quedarás en el equipo automáticamente.",
        f"El enlace vence en {dias} días. Si no esperabas este mensaje, puedes ignorarlo.",
    ])
    e = html.escape
    filas = "".join(
        f'<tr><td style="padding:4px 12px 4px 0;color:#64748b;vertical-align:top;white-space:nowrap">{e(k)}</td>'
        f'<td style="padding:4px 0;color:#0f172a">{e(v)}</td></tr>'
        for k, v in detalles
    )
    cuerpo = (
        '<div style="font-family:Segoe UI,Arial,sans-serif;max-width:560px;color:#0f172a;line-height:1.5">'
        "<p>Hola:</p>"
        f'<p style="font-size:17px;font-weight:600;margin:16px 0 8px">{e(quien_invita)} te invitó al proyecto '
        f"«{e(proyecto)}» en Proyecta</p>"
        f'<table style="border-collapse:collapse;font-size:14px;margin:12px 0">{filas}</table>'
        f'<p style="margin:20px 0"><a href="{e(enlace, quote=True)}" style="background:#2563eb;color:#fff;'
        'padding:10px 18px;border-radius:8px;text-decoration:none">Ver la invitación</a></p>'
        "<p>Si aceptas, crea tu cuenta con este mismo correo y quedarás en el equipo automáticamente.</p>"
        f'<p style="color:#64748b;font-size:12px;border-top:1px solid #e2e8f0;padding-top:12px">El enlace vence en '
        f"{dias} días. Si no esperabas este mensaje, puedes ignorarlo.</p>"
        "</div>"
    )
    return Correo(para=para, asunto=f"Te invitaron al proyecto «{proyecto}» en Proyecta", texto=texto, html=cuerpo)
