from app import app, db, User
from werkzeug.security import generate_password_hash

def init_db():
    print("Starting database initialization...")
    
    with app.app_context():
        # Create all tables
        print("Creating tables if they don't exist...")
        db.create_all()
        
        # Check if admin exists
        admin = User.query.filter_by(email='rishabh3005@hotmail.com').first()
        
        if not admin:
            print("Admin not found. Creating admin user...")
            admin = User(
                email='rishabh3005@hotmail.com',
                password_hash=generate_password_hash('Finally_therapture'),
                name='Rishabh',
                role='admin',  # <-- This is the key change
                annual_allowance=28
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin created successfully!")
        else:
            print("Admin already exists. Skipping creation.")
        
        # Create demo staff if they don't exist
        staff_data = [
            {'pin': '1001', 'name': 'Staff 1'},
            {'pin': '1002', 'name': 'Staff 2'},
            {'pin': '1003', 'name': 'Staff 3'},
        ]
        
        for staff_info in staff_data:
            staff = User.query.filter_by(pin=staff_info['pin']).first()
            if not staff:
                print(f"Creating staff with PIN {staff_info['pin']}...")
                staff = User(
                    pin=staff_info['pin'],
                    name=staff_info['name'],
                    role='staff',  # <-- This is the key change
                    annual_allowance=28
                )
                db.session.add(staff)
                db.session.commit()
                print(f"Staff {staff_info['pin']} created!")
            else:
                print(f"Staff {staff_info['pin']} already exists.")
        
        print("Database initialization complete!")

if __name__ == "__main__":
    init_db()