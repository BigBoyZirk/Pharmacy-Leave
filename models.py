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
    annual_allowance = db.Column(db.Float, nullable=False, default=210.0)  # Annual leave allowance in HOURS
    colour = db.Column(db.String(7), nullable=False, default="#2563eb")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key to Pharmacy
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=True)

    leave_requests = db.relationship(
        "LeaveRequest",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def booked_hours(self, year=None):
        """Total approved leave hours in a calendar year."""
        year = year or date.today().year
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        total = 0.0
        for req in self.leave_requests:
            if req.status != "approved":
                continue
            overlap_start = max(req.start_date, year_start)
            overlap_end = min(req.end_date, year_end)
            if overlap_start <= overlap_end:
                days = (overlap_end - overlap_start).days + 1
                total += days * req.calculate_hours()
        return total

    def remaining_hours(self, year=None):
        """Remaining annual leave hours in a calendar year."""
        return max(0.0, self.annual_allowance - self.booked_hours(year))


class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(5), nullable=False, default="09:00")  # HH:MM format
    end_time = db.Column(db.String(5), nullable=False, default="17:00")    # HH:MM format
    status = db.Column(db.String(20), nullable=False, default="pending")
    staff_note = db.Column(db.Text, nullable=True)
    admin_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_hours(self):
        """Calculate hours between start_time and end_time."""
        start = datetime.strptime(self.start_time, "%H:%M")
        end = datetime.strptime(self.end_time, "%H:%M")
        return (end - start).seconds / 3600.0

    def day_count(self):
        """Number of days in the range (inclusive)."""
        return (self.end_date - self.start_date).days + 1

    def total_hours(self):
        """Total hours for the entire leave request (days × hours per day)."""
        return self.day_count() * self.calculate_hours()

    def overlaps(self, start, end):
        """Check if this request overlaps with a given date range."""
        return self.start_date <= end and self.end_date >= start

    def as_calendar_event(self, include_staff=False):
        """FullCalendar uses exclusive end dates, so add one day."""
        time_display = f"{self.start_time}–{self.end_time}"
        if include_staff:
            title = f"{self.user.name} ({time_display})"
        else:
            title = time_display
        
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
                "startTime": self.start_time,
                "endTime": self.end_time,
                "hours": self.calculate_hours(),
                "totalHours": self.total_hours(),
            },
        }