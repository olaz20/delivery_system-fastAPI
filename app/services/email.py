from app.core.config import settings
import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from jinja2 import Environment, FileSystemLoader
from fastapi import BackgroundTasks


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

async def send_order_confirmation_email(email: str, customer_name: str, order_id: str):
    template = env.get_template("order_verification.html")
    html_content = template.render(customer_name=customer_name, order_id=order_id)

    message = MessageSchema(
        subject="Order Confirmation",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_payment_success_email(email: str, customer_name: str, order_id: str, driver_name: str = None, driver_email: str = None):
    template = env.get_template("payment_verification.html")
    html_content = template.render(
        customer_name=customer_name,
        order_id=order_id,
        driver_name=driver_name,
        driver_email=driver_email,
        driver_assigned=bool(driver_name and driver_email)
    )
    message = MessageSchema(
        subject="Payment Received - Order Confirmed",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_driver_assignment_email(email: str, driver_name: str, order_id: str):
    template = env.get_template("driver_assignment.html")
    html_content = template.render(driver_name=driver_name, order_id=order_id)
    message = MessageSchema(
        subject="New Order Assignment",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)