import csv
import io
import os
from datetime import date, datetime
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from emailer import notify_admin_of_request, notify_staff_of_decision
from models import STAFF_COLOURS, LeaveRequest, User, Pharmacy, db

load_dotenv()

login_manager = LoginManager()
login_manager.login_view = "staff_login"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///leave.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        seed_if_empty()

    register_routes(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/admin") or request.path.startswith("/api/admin"):
        return redirect(url_for("admin_login"))
    return redirect(url_for("staff_login"))


def staff_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "staff" or not current_user.is_active:
            flash("Staff login required.", "warning")
            return redirect(url_for("staff_login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            flash("Admin login required.", "warning")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped


def parse_iso_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def overlapping_requests(user_id, start, end, exclude_id=None):
    query = LeaveRequest.query.filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.status.in_(("pending", "approved")),
        LeaveRequest.start_date <= end,
        LeaveRequest.end_date >= start,
    )
    if exclude_id:
        query = query.filter(LeaveRequest.id != exclude_id)
    return query.all()


def seed_if_empty():
    if User.query.filter_by(role="admin").first():
        return

    admin_email = os.environ.get("ADMIN_EMAIL", "rishabh3005@hotmail.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Finally_therapture")
    admin = User(
        name=os.environ.get("ADMIN_NAME", "Rishabh"),
        role="admin",
        email=admin_email,
        password_hash=generate_password_hash(admin_password),
        colour="#111827",
        annual_allowance=0,
    )
    demo = [
        User(name="Aisha Khan", role="staff", pin="1001", email="aisha@example.com", colour=STAFF_COLOURS[0]),
        User(name="James Patel", role="staff", pin="1002", email="james@example.com", colour=STAFF_COLOURS[1]),
        User(name="Mei Chen", role="staff", pin="1003", email="mei@example.com", colour=STAFF_COLOURS[2]),
    ]
    db.session.add(admin)
    db.session.add_all(demo)
    db.session.commit()


def register_routes(app):
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("staff_dashboard"))
        return redirect(url_for("staff_login"))

    @app.route("/login", methods=["GET", "POST"])
    def staff_login():
        if request.method == "POST":
            pin = (request.form.get("pin") or "").strip()
            user = User.query.filter_by(role="staff", pin=pin, is_active=True).first()
            if user:
                login_user(user)
                return redirect(url_for("staff_dashboard"))
            flash("That PIN was not recognised.", "danger")
        return render_template("staff_login.html")

    @app.route("/logout")
    @login_required
    def logout():
        role = current_user.role
        logout_user()
        if role == "admin":
            return redirect(url_for("admin_login"))
        return redirect(url_for("staff_login"))

    @app.route("/portal")
    @staff_required
    def staff_dashboard():
        requests = (
            LeaveRequest.query.filter_by(user_id=current_user.id)
            .order_by(LeaveRequest.start_date.desc())
            .all()
        )
        return render_template(
            "staff_dashboard.html",
            requests=requests,
            booked=current_user.booked_days(),
            remaining=current_user.remaining_days(),
        )

    @app.route("/api/my-leave")
    @staff_required
    def api_my_leave():
        # Get the current user's own requests (all statuses except cancelled)
        my_items = LeaveRequest.query.filter(
            LeaveRequest.user_id == current_user.id,
            LeaveRequest.status != "cancelled",
        ).all()
        
        # Get all approved leave for ALL staff (so everyone can see who is off)
        all_approved = LeaveRequest.query.filter(
            LeaveRequest.status == "approved"
        ).all()
        
        # Combine both lists
        all_items = my_items + all_approved
        
        # Convert to calendar events
        return jsonify([item.as_calendar_event(include_staff=True) for item in all_items])

    @app.route("/api/leave-request", methods=["POST"])
    @staff_required
    def api_leave_request():
        data = request.get_json(silent=True) or {}
        start = parse_iso_date(data.get("start"))
        end = parse_iso_date(data.get("end"))
        note = (data.get("note") or "").strip() or None
        if not start or not end:
            return jsonify({"error": "Choose a start and end date."}), 400
        if end < start:
            return jsonify({"error": "End date cannot be before the start date."}), 400
        if overlapping_requests(current_user.id, start, end):
            return jsonify({"error": "Those dates overlap an existing request."}), 400

        leave = LeaveRequest(
            user_id=current_user.id,
            start_date=start,
            end_date=end,
            status="pending",
            staff_note=note,
        )
        db.session.add(leave)
        db.session.commit()
        notify_admin_of_request(leave, current_user)
        return jsonify({"ok": True, "id": leave.id})

    @app.route("/api/leave/<int:leave_id>/cancel", methods=["POST"])
    @staff_required
    def api_staff_cancel(leave_id):
        leave = LeaveRequest.query.filter_by(id=leave_id, user_id=current_user.id).first_or_404()
        if leave.status != "pending":
            return jsonify({"error": "Only pending requests can be cancelled."}), 400
        leave.status = "cancelled"
        db.session.commit()
        return jsonify({"ok": True})

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            user = User.query.filter_by(role="admin", email=email).first()
            if user and user.password_hash and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for("admin_dashboard"))
            flash("Incorrect email or password.", "danger")
        return render_template("admin_login.html")

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        staff = User.query.filter_by(role="staff", is_active=True).order_by(User.name).all()
        pending = (
            LeaveRequest.query.filter_by(status="pending")
            .order_by(LeaveRequest.created_at.asc())
            .all()
        )
        year = date.today().year
        overview = [
            {
                "staff": member,
                "booked": member.booked_days(year),
                "remaining": member.remaining_days(year),
            }
            for member in staff
        ]
        return render_template(
            "admin_dashboard.html",
            staff=staff,
            pending=pending,
            overview=overview,
            year=year,
        )

    @app.route("/api/admin/leave")
    @admin_required
    def api_admin_leave():
        items = LeaveRequest.query.filter(LeaveRequest.status != "cancelled").all()
        return jsonify([item.as_calendar_event(include_staff=True) for item in items])

    @app.route("/api/admin/leave/<int:leave_id>/decide", methods=["POST"])
    @admin_required
    def api_admin_decide(leave_id):
        data = request.get_json(silent=True) or {}
        decision = data.get("decision")
        if decision not in ("approved", "rejected"):
            return jsonify({"error": "Decision must be approved or rejected."}), 400
        leave = db.session.get(LeaveRequest, leave_id)
        if not leave:
            return jsonify({"error": "Request not found."}), 404
        if leave.status != "pending":
            return jsonify({"error": "Only pending requests can be decided."}), 400
        leave.status = decision
        leave.admin_note = (data.get("note") or "").strip() or None
        db.session.commit()
        notify_staff_of_decision(leave, leave.user)
        return jsonify({"ok": True})

    @app.route("/api/admin/leave/manual", methods=["POST"])
    @admin_required
    def api_admin_manual():
        data = request.get_json(silent=True) or {}
        user = db.session.get(User, data.get("user_id"))
        start = parse_iso_date(data.get("start"))
        end = parse_iso_date(data.get("end"))
        if not user or user.role != "staff":
            return jsonify({"error": "Choose a staff member."}), 400
        if not start or not end or end < start:
            return jsonify({"error": "Choose a valid date range."}), 400
        if overlapping_requests(user.id, start, end):
            return jsonify({"error": "Those dates overlap existing leave for that person."}), 400
        leave = LeaveRequest(
            user_id=user.id,
            start_date=start,
            end_date=end,
            status="approved",
            admin_note=(data.get("note") or "").strip() or "Added by admin",
        )
        db.session.add(leave)
        db.session.commit()
        return jsonify({"ok": True, "id": leave.id})

    @app.route("/api/admin/leave/<int:leave_id>/update", methods=["POST"])
    @admin_required
    def api_admin_update(leave_id):
        data = request.get_json(silent=True) or {}
        leave = db.session.get(LeaveRequest, leave_id)
        if not leave:
            return jsonify({"error": "Leave not found."}), 404
        start = parse_iso_date(data.get("start")) or leave.start_date
        end = parse_iso_date(data.get("end")) or leave.end_date
        if end < start:
            return jsonify({"error": "End date cannot be before the start date."}), 400
        if overlapping_requests(leave.user_id, start, end, exclude_id=leave.id):
            return jsonify({"error": "Those dates overlap other leave for that person."}), 400
        action = data.get("action") or "move"
        leave.start_date = start
        leave.end_date = end
        note = (data.get("note") or "").strip()
        if action == "cancel":
            leave.status = "cancelled"
        leave.admin_note = note or leave.admin_note
        db.session.commit()
        return jsonify({"ok": True})

    @app.route("/admin/staff", methods=["POST"])
    @admin_required
    def admin_add_staff():
        name = (request.form.get("name") or "").strip()
        pin = (request.form.get("pin") or "").strip()
        email = (request.form.get("email") or "").strip().lower() or None
        allowance = request.form.get("annual_allowance") or "28"
        if not name or not pin.isdigit() or len(pin) != 4:
            flash("Name and a 4-digit PIN are required.", "danger")
            return redirect(url_for("admin_dashboard"))
        if User.query.filter_by(pin=pin).first():
            flash("That PIN is already in use.", "danger")
            return redirect(url_for("admin_dashboard"))
        used = {member.colour for member in User.query.filter_by(role="staff").all()}
        colour = next((c for c in STAFF_COLOURS if c not in used), STAFF_COLOURS[0])
        try:
            allowance_int = int(allowance)
        except ValueError:
            allowance_int = 28
        member = User(
            name=name,
            role="staff",
            pin=pin,
            email=email,
            annual_allowance=allowance_int,
            colour=colour,
        )
        db.session.add(member)
        db.session.commit()
        flash(f"{name} added. Their PIN is {pin}.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/export.csv")
    @admin_required
    def admin_export():
        rows = (
            LeaveRequest.query.join(User)
            .order_by(LeaveRequest.start_date, User.name)
            .all()
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Staff",
                "PIN",
                "Email",
                "Start",
                "End",
                "Days",
                "Status",
                "Staff note",
                "Admin note",
            ]
        )
        for item in rows:
            writer.writerow(
                [
                    item.user.name,
                    item.user.pin or "",
                    item.user.email or "",
                    item.start_date.isoformat(),
                    item.end_date.isoformat(),
                    item.day_count(),
                    item.status,
                    item.staff_note or "",
                    item.admin_note or "",
                ]
            )
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=leave-schedule.csv"},
        )


app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)