import logging
import os
from typing import Any

from emails.template import JinjaTemplate
from config import env

import emails

from etc.local_error import HandledError


logger = logging.getLogger("uvicorn.info")


def send_email(
    recipient: str,
    subject: str,
    html_content: str,
    text_content: str | None = None,
) -> bool:
    message = emails.Message(
        subject=subject,
        html=html_content,
        text=text_content or html_content.replace("<br>", "\n"),
        mail_from=(env.SENDER_NAME, env.SENDER_EMAIL),
    )

    response = message.send(
        to=recipient,
        smtp={
            "host": env.SMTP_HOST,
            "port": env.SMTP_PORT,
            "user": env.SMTP_USER,
            "password": env.SMTP_PASSWORD,
            "tls": True,
        },
    )

    logger.info(f"Sending email to {recipient}")

    return response.status_code == 250


def send_template_email(
    recipients: str,
    subject: str,
    template_name: str,
    template_vars: dict[str, Any],
) -> bool:
    template_path = f"./email_template/{template_name}.html"

    if not os.path.exists(template_path):
        raise HandledError(f"Email template not found: {template_path}")

    with open(template_path, "r") as f:
        template_content = f.read()

    html_content = JinjaTemplate(template_content).render(**template_vars)

    return send_email(
        recipient=recipients,
        subject=subject,
        html_content=html_content,
    )
