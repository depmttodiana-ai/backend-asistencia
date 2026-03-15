import smtplib
from email.message import EmailMessage
import os

def send_reset_password_email(to_email: str, token: str):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_url = f"{frontend_url}/reset-password?token={token}"
    
    msg = EmailMessage()
    msg.set_content(
        f"Hola,\n\n"
        f"Alguien ha solicitado el restablecimiento de contraseña para tu cuenta.\n"
        f"Para cambiar tu contraseña, por favor haz clic en el siguiente enlace:\n\n"
        f"{reset_url}\n\n"
        f"Este enlace expirará en 15 minutos.\n"
        f"Si no solicitaste este cambio, simplemente ignora este correo.\n"
    )
    msg['Subject'] = 'Recuperación de contraseña - Palmeras Diana'
    msg['From'] = os.getenv("SMTP_USER", "no-reply@palmerasdiana.com")
    msg['To'] = to_email

    print(f"\n--- [MOCK EMAIL ENVIADO] ---")
    print(f"PARA: {to_email}")
    print(f"ASUNTO: {msg['Subject']}")
    print(f"CUERPO:\n{msg.get_content()}")
    print(f"----------------------------\n")

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", 587)
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    # Si hay credenciales, intenta enviar el correo real
    if smtp_server and smtp_user and smtp_pass:
        try:
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            print("Correo enviado a la red SMTP con éxito.")
        except Exception as e:
            print(f"Error despachando correo SMTP: {e}")
