from email.mime.multipart import MIMEMultipart
import smtplib
from typing import Annotated
from emails.utils import MIMEText
from fastapi import APIRouter, Depends
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.db_session import get_session
from dtos.request.account import AccountCreateDto
from services import account as acc_sv
from datetime import datetime
from etc import smtp
from config import env
import auth

Permission = Annotated[bool, Depends(auth.manager_permission)]

router = APIRouter(prefix="/dev", tags=["Dev"])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.post("/create", response_model=None)
async def create(account: AccountCreateDto, session: Session) -> dict[str, str]:
    token = await acc_sv.create_account(account, session)
    return {"access_token": token}


@router.get("/cors_test")
async def cors() -> str:
    return "CORS"


@router.post("/mail/test")
async def email_test(receiver: list[EmailStr]):
    return smtp.send_template_email(
        receiver,
        "Test",
        "test",
        {
            "name": "sus",
            "year": datetime.now().year,
        },
    )


@router.get("/mail/smtp/test")
def test_smtp_connection():
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = env.SMTP_USER
    smtp_password = env.SMTP_PASSWORD

    print(f"Connecting to {smtp_host}:{smtp_port}")
    print(f"Using credentials: {smtp_user} / {'*' * 8}")

    try:
        # Create server connection
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.set_debuglevel(1)  # Enable verbose debug output
        server.ehlo()
        server.starttls()
        server.ehlo()

        # Login
        print("Attempting login...")
        server.login(smtp_user, smtp_password)
        print("Login successful!")

        # Send test email
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = smtp_user  # Send to yourself for testing
        msg["Subject"] = "Test Email - Debug"

        body = "This is a test email to debug the email functionality."
        msg.attach(MIMEText(body, "plain"))

        print("Sending email...")
        server.send_message(msg)
        print("Email sent successfully!")

        server.quit()
        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        return False
