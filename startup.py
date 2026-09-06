from app import app, db, User, Pharmacy
from werkzeug.security import generate_password_hash

def init_db():
    print("Starting database initialization...")
    
    with app.app_context():
        # ============================================
        # FORCE RECREATE TABLES (TEMPORARY FIX)
        # ============================================
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("✅ Tables created with correct schema.")
        
        # ============================================
        # 1. CREATE YOUR PRESIDENT ACCOUNT
        # ============================================
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
        
        # ============================================
        # 2. CREATE TETTENHALL WOOD PHARMACY
        # ============================================
        print("Creating Tettenhall Wood Pharmacy...")
        pharmacy = Pharmacy(name="Tettenhall Wood Pharmacy")
        db.session.add(pharmacy)
        db.session.commit()
        print("✅ Pharmacy created!")
        
        # ============================================
        # 3. CREATE VINAYAK KHANNA AS PHARMACY ADMIN
        # ============================================
        print("Creating Vinayak Khanna's admin account...")
        dad_admin = User(
            name='Vinayak Khanna',
            email='vinayakkhanna@yahoo.co.uk',
            password_hash=generate_password_hash('Ugarte_Ballondor'),
            role='pharmacy_admin',
            pharmacy_id=pharmacy.id,
            is_active=True,
            annual_allowance=0
        )
        db.session.add(dad_admin)
        db.session.commit()
        print("✅ Vinayak Khanna's admin account created!")
        
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
        print("🏪 PHARMACY ADMIN (Vinayak Khanna):")
        print("   Email: vinayakkhanna@yahoo.co.uk")
        print("   Password: Ugarte_Ballondor")
        print("   Role: pharmacy_admin (can only see Tettenhall Wood Pharmacy)")
        print("="*50)

if __name__ == "__main__":
    init_db()