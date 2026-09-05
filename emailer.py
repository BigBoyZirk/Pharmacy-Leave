"""Send leave notification emails via SMTP."""

import os
import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(to_address, subject, body):
    """Send an email using the configured SMTP server."""
    if not to_address:
        current_app.logger.warning("No email address provided.")
        return False
    
    # Check if SMTP is configured
    if not os.environ.get("MAIL_SERVER") or not os.environ.get("MAIL_USERNAME"):
        current_app.logger.warning("SMTP not configured. Skipping email to %s", to_address)
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
        current_app.logger.info("✅ Email sent to %s: %s", to_address, subject)
        return True
    except Exception as exc:
        current_app.logger.warning("Email failed to %s: %s", to_address, exc)
        return False


def notify_admin_of_request(leave_request, staff):
    """Notify the pharmacy admin when a staff member requests leave."""
    from models import User
    
    admin = User.query.filter_by(
        pharmacy_id=staff.pharmacy_id,
        role="pharmacy_admin"
    ).first()
    
    if not admin or not admin.email:
        current_app.logger.warning("No admin email found for pharmacy %s", staff.pharmacy_id)
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
        current_app.logger.warning("No email for staff %s", staff.name)
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