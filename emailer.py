"""Send leave notification emails via SMTP. Missing config is skipped, not fatal."""

import os
import smtplib
from email.message import EmailMessage

from flask import current_app


def _smtp_ready():
    return bool(os.environ.get("MAIL_SERVER") and os.environ.get("MAIL_USERNAME"))


def send_email(to_address, subject, body):
    if not to_address:
        return False
    if not _smtp_ready():
        current_app.logger.info("Email skipped (SMTP not configured): %s -> %s", subject, to_address)
        return False

    msg = EmailMessage()
    sender = os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get("MAIL_USERNAME")
    msg["From"] = sender
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    host = os.environ["MAIL_SERVER"]
    port = int(os.environ.get("MAIL_PORT", "587"))
    use_tls = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    username = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD", "")

    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(msg)
        return True
    except OSError as exc:
        current_app.logger.warning("Email failed: %s", exc)
        return False


def notify_admin_of_request(request, staff):
    admin_email = os.environ.get("NOTIFY_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
    send_email(
        admin_email,
        f"Leave request from {staff.name}",
        (
            f"{staff.name} has requested annual leave.\n\n"
            f"Dates: {request.start_date.isoformat()} to {request.end_date.isoformat()} "
            f"({request.day_count()} day(s))\n"
            f"Note: {request.staff_note or '(none)'}\n\n"
            "Log in to the admin dashboard to approve or reject this request."
        ),
    )


def notify_staff_of_decision(request, staff):
    send_email(
        staff.email,
        f"Your leave request was {request.status}",
        (
            f"Hello {staff.name},\n\n"
            f"Your annual leave request from {request.start_date.isoformat()} "
            f"to {request.end_date.isoformat()} is now: {request.status.upper()}.\n"
            f"Admin note: {request.admin_note or '(none)'}\n"
        ),
    )
