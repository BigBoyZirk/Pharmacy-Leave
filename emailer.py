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


def notify_admin_of_request(leave_request, staff):
    """Notify the pharmacy admin when a staff member requests leave."""
    from models import User
    
    # Look up the admin for this staff member's pharmacy
    admin = User.query.filter_by(
        pharmacy_id=staff.pharmacy_id,
        role="pharmacy_admin"
    ).first()
    
    if not admin or not admin.email:
        current_app.logger.info("No admin email found for pharmacy %s", staff.pharmacy_id)
        return False
    
    subject = f"Leave request from {staff.name}"
    body = (
        f"{staff.name} has requested annual leave.\n\n"
        f"Dates: {leave_request.start_date.isoformat()} to {leave_request.end_date.isoformat()} "
        f"({leave_request.day_count()} day(s))\n"
        f"Note: {leave_request.staff_note or '(none)'}\n\n"
        "Log in to the admin dashboard to approve or reject this request.\n"
        f"https://pharmacy-leave.onrender.com/admin"
    )
    
    return send_email(admin.email, subject, body)


def notify_staff_of_decision(leave_request, staff):
    """Notify the staff member when their request is approved or rejected."""
    if not staff.email:
        current_app.logger.info("No email for staff %s", staff.name)
        return False
    
    subject = f"Your leave request was {leave_request.status}"
    body = (
        f"Hello {staff.name},\n\n"
        f"Your annual leave request from {leave_request.start_date.isoformat()} "
        f"to {leave_request.end_date.isoformat()} is now: {leave_request.status.upper()}.\n"
        f"Admin note: {leave_request.admin_note or '(none)'}\n\n"
        "View your requests: https://pharmacy-leave.onrender.com/portal"
    )
    
    return send_email(staff.email, subject, body)