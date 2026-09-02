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
        # 2. CREATE/RENAME TETTENHALL WOOD PHARMACY
        # ============================================
        old_pharmacy = Pharmacy.query.filter_by(name="Dad's Pharmacy").first()
        if old_pharmacy:
            old_pharmacy.name = "Tettenhall Wood Pharmacy"
            db.session.commit()
            print("✅ Renamed 'Dad's Pharmacy' to 'Tettenhall Wood Pharmacy'")
            pharmacy = old_pharmacy
        else:
            pharmacy = Pharmacy.query.filter_by(name="Tettenhall Wood Pharmacy").first()
            if not pharmacy:
                print("Creating Tettenhall Wood Pharmacy...")
                pharmacy = Pharmacy(name="Tettenhall Wood Pharmacy")
                db.session.add(pharmacy)
                db.session.commit()
                print("✅ Pharmacy created!")
            else:
                print("ℹ️ Tettenhall Wood Pharmacy already exists.")
        
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
        # 4. REMOVE DEMO STAFF (If they exist)
        # ============================================
        demo_pins = ['1001', '1002', '1003']
        deleted = User.query.filter(
            User.pin.in_(demo_pins),
            User.pharmacy_id == pharmacy.id
        ).delete(synchronize_session=False)
        if deleted:
            db.session.commit()
            print(f"✅ Removed {deleted} demo staff members from {pharmacy.name}")
        else:
            print("ℹ️ No demo staff found to remove.")
        
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
        print("   Role: pharmacy_admin (can only see Tettenhall Wood Pharmacy)")
        print("")
        print("👥 STAFF:")
        print("   No demo staff. Add staff via the admin dashboard.")
        print("="*50)

if __name__ == "__main__":
    init_db()