from app.core.config import settings
import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from jinja2 import Environment, FileSystemLoader



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "..", "templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


conf =  ConnectionConfig(
    MAIL_USERNAME=settings.email_host_user,
    MAIL_PASSWORD=settings.email_host_password,
    MAIL_FROM=settings.default_from_email,
    MAIL_PORT=int(settings.email_port),
    MAIL_SERVER="smtp.gmail.com", 
    MAIL_FROM_NAME="Logistics Team",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

async def send_confirmation_email(email: str, token: str):
    verification_url = f"http://127.0.0.1:8000/users/verify?token={token}"
    template = env.get_template("email_verification.html")
    html_content = template.render(verification_url=verification_url)
    message = MessageSchema(
        subject="Email Verification",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
