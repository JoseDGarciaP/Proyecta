"""Envío de correos por SMTP.

Sin SMTP_HOST configurado no se envía nada: el mensaje se escribe en la consola de la API
(útil en desarrollo) y queda en `enviados`, que las pruebas revisan.
"""

import html
import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import get_settings

log = logging.getLogger("proyecta.correo")


@dataclass
class Correo:
    para: str
    asunto: str
    texto: str
    html: str


enviados: list[Correo] = []


def enviar(correo: Correo) -> None:
    settings = get_settings()
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
