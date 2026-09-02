from app import app, db, User, Pharmacy
from werkzeug.security import generate_password_hash

def init_db():
    print("Starting database initialization...")
    
    with app.app_context():
        db.create_all()
        
        # ============================================
        # 1. CREATE YOUR PRESIDENT ACCOUNT
        # ============================================
        president = User.query.filter_by(email='rishabh3005@hotmail.com').first()
        if not president:
            print("Creating President account (Rishabh)...")
            president = User(
                name='Rishabh',
                email='rishabh3005@hotmail.com',
                password_hash=generate_password_hash('Finally_therapture'),
                role='president',
                is_active=True,
                annual_allowance=0
            )
            db.session.add(president)
            db.session.commit()
            print("✅ President account created!")
        else:
            print("ℹ️ President account already exists.")
        
        # ============================================
        # 2. CREATE DAD'S PHARMACY
        # ============================================
        pharmacy = Pharmacy.query.filter_by(name="Dad's Pharmacy").first()
        if not pharmacy:
            print("Creating Dad's Pharmacy...")
            pharmacy = Pharmacy(name="Dad's Pharmacy")
            db.session.add(pharmacy)
            db.session.commit()
            print("✅ Pharmacy created!")
        else:
            print("ℹ️ Dad's Pharmacy already exists.")
        
        # ============================================
        # 3. CREATE DAD AS PHARMACY ADMIN
        # ============================================
        dad_admin = User.query.filter_by(email='dad@pharmacy.com').first()
        if not dad_admin:
            print("Creating Dad's admin account...")
            dad_admin = User(
                name='Dad',
                email='dad@pharmacy.com',
                password_hash=generate_password_hash('dadpassword123'),
                role='pharmacy_admin',
                pharmacy_id=pharmacy.id,
                is_active=True,
                annual_allowance=0
            )
            db.session.add(dad_admin)
            db.session.commit()
            print("✅ Dad's admin account created!")
        else:
            print("ℹ️ Dad's admin account already exists.")
        
        # ============================================
        # 4. CREATE DEMO STAFF (Belongs to Dad's Pharmacy)
        # ============================================
        staff_data = [
            {'pin': '1001', 'name': 'Aisha Khan'},
            {'pin': '1002', 'name': 'James Patel'},
            {'pin': '1003', 'name': 'Mei Chen'},
        ]
        
        for staff_info in staff_data:
            # Check if staff with this PIN already exists in THIS pharmacy
            existing_staff = User.query.filter_by(
                pin=staff_info['pin'],
                pharmacy_id=pharmacy.id
            ).first()
            
            if not existing_staff:
                print(f"Creating staff {staff_info['name']} (PIN: {staff_info['pin']})...")
                staff = User(
                    name=staff_info['name'],
                    pin=staff_info['pin'],
                    role='staff',
                    pharmacy_id=pharmacy.id,
                    is_active=True,
                    annual_allowance=28
                )
                db.session.add(staff)
                db.session.commit()
                print(f"✅ Staff {staff_info['pin']} created!")
            else:
                print(f"ℹ️ Staff PIN {staff_info['pin']} already exists in this pharmacy.")
        
        print("\n" + "="*50)
        print("🎉 DATABASE INITIALIZATION COMPLETE!")
        print("="*50)
        print("\n📋 LOGIN DETAILS:")
        print("-"*30)
        print("👑 PRESIDENT (You):")
        print("   Email: rishabh3005@hotmail.com")
        print("   Password: Finally_therapture")
        print("   Role: president (can see all pharmacies)")
        print("")
        print("🏪 PHARMACY ADMIN (Dad):")
        print("   Email: dad@pharmacy.com")
        print("   Password: dadpassword123")
        print("   Role: pharmacy_admin (can only see Dad's Pharmacy)")
        print("")
        print("👥 STAFF (Demo):")
        print("   Pharmacy: Dad's Pharmacy")
        print("   PIN 1001: Aisha Khan")
        print("   PIN 1002: James Patel")
        print("   PIN 1003: Mei Chen")
        print("="*50)

if __name__ == "__main__":
    init_db()