# main.py

import os
from flask import Flask, url_for, current_app # Added current_app for potential later use
from flask_mail import Mail
from flask_security import Security, hash_password, SQLAlchemyUserDatastore
from projects.projects_routes import projects_bp
# Ensure db is imported before User/Role if they depend on it implicitly
from projects.projects_model import db
from users.users_model import User, Role

mail = Mail()
security = Security() # Initialize Security object

app = Flask(__name__)

# --- Database Configuration ---
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("FATAL ERROR: DATABASE_URL environment variable not set.")
    # Exit or raise an error if the DB URL is critical for startup
    exit("Database URL is required.") # Or handle more gracefully

print(f"DEBUG: Original DATABASE_URL: {database_url}")
if '.us-east-2' in database_url and '-pooler' not in database_url:
    # Modify the URL to use connection pooling - ensure this logic is correct for your provider
    database_url = database_url.replace('.us-east-2', '-pooler.us-east-2')
    print(f"DEBUG: Modified DATABASE_URL for pooling: {database_url}")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'pool_recycle': 280,
    'pool_timeout': 20,
    'pool_pre_ping': True
}

# --- Secret Key ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
     print("WARNING: SECRET_KEY environment variable not set. Using default (insecure).")
     app.config['SECRET_KEY'] = 'super-secret-default-key-CHANGE-ME' # Use a default only for debugging if absolutely necessary

# --- Mail Settings ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# --- Security Settings ---
# Make sure these are set BEFORE security.init_app()
app.config['SECURITY_REGISTERABLE'] = True  # Or False if you don't want public registration
app.config['SECURITY_CONFIRMABLE'] = True   # Requires email confirmation for registration if not passwordless
app.config['SECURITY_PASSWORDLESS'] = True  # **** THIS IS THE KEY SETTING ****
app.config['SECURITY_LOGIN_WITHOUT_CONFIRMATION'] = False # Good practice if confirmable is True
app.config['SECURITY_EMAIL_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') # Ensure this matches MAIL_DEFAULT_SENDER or is set
app.config['SECURITY_LOGIN_WITHIN'] = '24 hours'  # Login link validity duration
app.config['SECURITY_TOKEN_MAX_AGE'] = 86400  # 24 hours in seconds for tokens (like confirmation, password reset)

# --- Initialize Extensions ---
db.init_app(app)
print("DEBUG: db initialized.")
mail.init_app(app)
print("DEBUG: mail initialized.")

# Initialize Flask-Security Datastore
# Import models just before use if needed, but they were imported above
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
print("DEBUG: user_datastore created.")

# --- Initialize Flask-Security ---
print("\n--- DEBUG: Initializing Flask-Security ---")
print(f"DEBUG: SECURITY_PASSWORDLESS config value: {app.config.get('SECURITY_PASSWORDLESS')}") # Check the value right before init
try:
    security.init_app(app, user_datastore)
    print("DEBUG: security.init_app(app, user_datastore) called.")

    # --- Check for the generator AFTER initialization ---
    if hasattr(security, 'pwdless_login_token_generator'):
        print("DEBUG: SUCCESS! 'pwdless_login_token_generator' FOUND on security object after init.")
    else:
        print("DEBUG: FAILURE! 'pwdless_login_token_generator' NOT FOUND on security object after init.")
        print("DEBUG: Attributes available on security object:", dir(security)) # List attributes

except Exception as e_sec_init:
    print(f"ERROR: Failed during security.init_app: {e_sec_init}")
    print(traceback.format_exc()) # Added traceback import needed if used

print("--- DEBUG: Flask-Security Initialization Complete ---\n")


# Import models before creating tables (good practice, though imports were above)
from projects.projects_model import Project

# --- Database Creation and Default Roles ---
with app.app_context():
    print("DEBUG: Entering app_context for db operations.")
    try:
        print("DEBUG: Attempting db.create_all()...")
        # Create all tables first
        db.create_all()
        print("DEBUG: db.create_all() completed.")

        # Create default roles if they don't exist
        print("DEBUG: Checking/Creating default roles...")
        default_roles = ['admin', 'pending', 'analyst']
        roles_changed = False
        for role_name in default_roles:
            if not Role.query.filter_by(name=role_name).first():
                print(f"DEBUG: Creating role: {role_name}")
                role = Role(name=role_name, description=f"{role_name.capitalize()} role") # Add description maybe
                db.session.add(role)
                roles_changed = True
            else:
                print(f"DEBUG: Role '{role_name}' already exists.")

        if roles_changed:
            db.session.commit()
            print("DEBUG: Committed new roles to database.")
        else:
            print("DEBUG: No new roles needed.")

    except Exception as e:
        print(f"ERROR: Exception during db.create_all() or role creation: {e}")
        db.session.rollback()
        print(traceback.format_exc()) # Added traceback import needed if used
    finally:
        print("DEBUG: Exiting app_context for db operations.")


# --- Register Blueprints ---
from users.users_routes import users_bp

app.register_blueprint(projects_bp)
print("DEBUG: Registered projects_bp.")
app.register_blueprint(users_bp)
print("DEBUG: Registered users_bp.")


# --- Run Application ---
if __name__ == '__main__':
    print("DEBUG: Starting Flask development server.")
    # Consider using waitress or gunicorn for production instead of app.run
    app.run(host='0.0.0.0', port=5000, debug=True) # Added debug=True for development server logs