"""Database models for the pharmacy annual leave app."""

from datetime import date, datetime, timedelta

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

STAFF_COLOURS = [
    "#2563eb",
    "#059669",
    "#d97706",
    "#dc2626",
    "#7c3aed",
    "#0891b2",
    "#db2777",
    "#4f46e5",
    "#0f766e",
    "#b45309",
]


class Pharmacy(db.Model):
    """A pharmacy that uses the system. Each pharmacy has its own staff and leave data."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to users
    users = db.relationship('User', backref='pharmacy', lazy=True)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")  # president | pharmacy_admin | staff
    pin = db.Column(db.String(4), unique=False, nullable=True)  # staff login (only unique within a pharmacy)
    email = db.Column(db.String(120), unique=True, nullable=True)  # admin/president login
    password_hash = db.Column(db.String(255), nullable=True)  # admin/president login
    annual_allowance = db.Column(db.Integer, nullable=False, default=28)
    colour = db.Column(db.String(7), nullable=False, default="#2563eb")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key to Pharmacy
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=True)
    # Note: pharmacy_id is nullable=True so President account doesn't need to belong to a pharmacy

    leave_requests = db.relationship(
        "LeaveRequest",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def booked_days(self, year=None):
        """Approved leave days in a calendar year (inclusive date range)."""
        year = year or date.today().year
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        total = 0
        for req in self.leave_requests:
            if req.status != "approved":
                continue
            overlap_start = max(req.start_date, year_start)
            overlap_end = min(req.end_date, year_end)
            if overlap_start <= overlap_end:
                total += (overlap_end - overlap_start).days + 1
        return total

    def remaining_days(self, year=None):
        return max(0, self.annual_allowance - self.booked_days(year))


class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    staff_note = db.Column(db.Text, nullable=True)
    admin_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def day_count(self):
        return (self.end_date - self.start_date).days + 1

    def overlaps(self, start, end):
        return self.start_date <= end and self.end_date >= start

    def as_calendar_event(self, include_staff=False):
        """FullCalendar uses exclusive end dates, so add one day."""
        title = f"{self.user.name} ({self.status})" if include_staff else self.status.title()
        colour = self.user.colour
        if self.status == "pending":
            colour = "#ca8a04"
        elif self.status == "rejected":
            colour = "#9ca3af"
        elif self.status == "cancelled":
            colour = "#6b7280"
        return {
            "id": self.id,
            "title": title,
            "start": self.start_date.isoformat(),
            "end": (self.end_date + timedelta(days=1)).isoformat(),
            "backgroundColor": colour,
            "borderColor": colour,
            "extendedProps": {
                "status": self.status,
                "userId": self.user_id,
                "staffName": self.user.name,
                "staffNote": self.staff_note or "",
                "adminNote": self.admin_note or "",
                "dayCount": self.day_count(),
            },
        }