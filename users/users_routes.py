# users/users_routes.py

import traceback
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from flask_mail import Message
# Import only login_user from utils, as generate/verify aren't there
from flask_security.utils import login_user
# Import itsdangerous exceptions for verification
from itsdangerous import SignatureExpired, BadSignature
from .users_model import User, Role, db
# Import mail and security objects initialized in main.py
from main import mail, security, user_datastore # Import user_datastore here too

users_bp = Blueprint('users', __name__)

@users_bp.route('/users_login')
def login():
    current_app.logger.info("Rendering login page")
    print("DEBUG: Rendering login page (users/users_login.html)")
    return render_template('users/users_login.html')

@users_bp.route('/send-login-link', methods=['POST'])
def send_login_link():
    print("\n--- DEBUG: Entered send_login_link route ---")
    user = None
    try:
        email = request.form.get('email')
        print(f"DEBUG: Received email from form: {email}")
        if not email:
            print("ERROR: No email provided in form.")
            return "Email is required.", 400

        # Ensure necessary objects are available
        if not user_datastore:
             print("ERROR: user_datastore not available.")
             return "Server configuration error (datastore).", 500
        if not security:
             print("ERROR: security object not available.")
             return "Server configuration error (security object).", 500
        if not hasattr(security, 'login_serializer'):
             print("ERROR: security object missing 'login_serializer'. Check Flask-Security setup.")
             return "Server configuration error (login serializer missing).", 500
        print("DEBUG: user_datastore, security object, and login_serializer available.")

        print(f"DEBUG: Querying for user with email: {email}")
        user = user_datastore.find_user(email=email)

        if not user:
            print(f"DEBUG: User not found for email {email}. Attempting to create user.")
            try:
                user = user_datastore.create_user(
                    email=email,
                    name=email.split('@')[0]
                )
                db.session.commit()
                print(f"DEBUG: Successfully created new user: {user}")
                print("DEBUG: db.session.commit() called after user creation.")

            except Exception as e_create:
                db.session.rollback()
                print(f"ERROR: Failed to create user for email {email}.")
                print(traceback.format_exc())
                return f"Failed to process user: {e_create}", 500
        else:
            print(f"DEBUG: Found existing user: {user}")

        if not user or not hasattr(user, 'get_id'): # Check for get_id method
             print(f"ERROR: User object is invalid or missing get_id method: {user}")
             return "Failed to retrieve or create user properly.", 500

        print(f"DEBUG: Attempting to generate login token for user: {user.email} (ID: {user.get_id()}) using login_serializer.dumps()")
        token = None
        try:
            # --- THIS IS THE FIX for Generation ---
            # Use the serializer's dumps() method directly. It typically serializes the user ID.
            # Use user.get_id() as Flask-Login does.
            user_id_to_serialize = user.get_id()
            print(f"DEBUG: User ID to serialize: {user_id_to_serialize}")
            if user_id_to_serialize is None:
                raise ValueError("User ID is None, cannot generate token.")
            token = security.login_serializer.dumps(user_id_to_serialize)
            # --- END FIX ---

            if not token:
                 print("ERROR: login_serializer.dumps() returned None or empty value.")
                 print(f"DEBUG: User details: ID={user.get_id()}, Email={user.email}, Active={getattr(user, 'active', 'N/A')}, FS_Uniquifier={getattr(user, 'fs_uniquifier', 'N/A')}")
                 return "Failed to generate login token.", 500
            print(f"DEBUG: Successfully generated login token: {token[:10]}...") # Token is usually bytes, but slicing works
        except Exception as e_token:
            print("ERROR: Failed during call to login_serializer.dumps().")
            print(traceback.format_exc())
            return f"Failed to generate login token: {e_token}", 500

        # --- Generate URL and Send Email (Code remains the same) ---
        print(f"DEBUG: Attempting to generate login URL with token: {token[:10]}...")
        login_link = None
        try:
            login_link = url_for('users.login_with_token', token=token, _external=True)
            if not login_link:
                 print("ERROR: url_for returned None or empty value for login_with_token.")
                 return "Failed to construct login URL.", 500
            print(f"DEBUG: Successfully generated login link: {login_link}")
        except Exception as e_url:
            print("ERROR: Failed to generate login link URL.")
            print(traceback.format_exc())
            return f"Failed to construct login URL: {e_url}", 500

        print(f"DEBUG: Attempting to create email message for: {email}")
        msg = None
        try:
            sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('SECURITY_EMAIL_SENDER')
            if not sender:
                print("ERROR: MAIL_DEFAULT_SENDER or SECURITY_EMAIL_SENDER not configured.")
                return "Email sender not configured.", 500
            print(f"DEBUG: Using sender: {sender}")

            msg = Message(
                "Your Login Link",
                sender=sender,
                recipients=[email],
                body=f"Click this link to log in (valid for {current_app.config.get('SECURITY_LOGIN_WITHIN', '24 hours')}): {login_link}"
            )
            print("DEBUG: Successfully created email message object.")
        except Exception as e_msg:
             print("ERROR: Failed to create email message object.")
             print(traceback.format_exc())
             return f"Failed to create email message: {e_msg}", 500


        print(f"DEBUG: Attempting to send email to: {email}")
        try:
            mail.send(msg)
            print("DEBUG: Successfully sent email.")
        except Exception as e_send:
            print("ERROR: Failed to send email.")
            print(traceback.format_exc())
            return f"Failed to send login email. Please check server logs and mail configuration. Error: {e_send}", 500

        print("--- DEBUG: Successfully finished send_login_link ---")
        return "Login link has been sent to your email", 200
    # --- End Generate/Send ---

    except Exception as e_main:
        print(f"ERROR: An unexpected error occurred in send_login_link for email {request.form.get('email')}.")
        print(traceback.format_exc())
        user_info = f"User: {getattr(user, 'email', 'N/A')} (ID: {getattr(user, 'id', 'N/A')})"
        print(f"DEBUG: State at time of error: {user_info}")
        return f"An unexpected error occurred: {e_main}", 500


@users_bp.route('/login/<token>')
def login_with_token(token):
    print(f"\n--- DEBUG: Entered login_with_token route with token: {token[:10]}... ---")
    user = None
    try:
        if not security:
             print("ERROR: security object not available.")
             return "Server configuration error (security object).", 500
        if not hasattr(security, 'login_serializer'):
             print("ERROR: security object missing 'login_serializer'.")
             return "Server configuration error (login serializer missing).", 500
        if not user_datastore:
             print("ERROR: user_datastore not available.")
             return "Server configuration error (datastore).", 500
        print("DEBUG: Security object, login_serializer, and user_datastore available.")

        print(f"DEBUG: Attempting to verify token using login_serializer.loads()")
        # --- THIS IS THE FIX for Verification ---
        max_age = current_app.config.get("SECURITY_TOKEN_MAX_AGE", 86400) # Use configured max age
        print(f"DEBUG: Using max_age: {max_age} seconds")

        try:
            # Use the serializer's loads() method directly.
            # It raises SignatureExpired or BadSignature on failure.
            # It should return the original data (the user ID) on success.
            user_id = security.login_serializer.loads(token, max_age=max_age)
            print(f"DEBUG: Token loaded successfully. User ID: {user_id}")

        except SignatureExpired:
            print("ERROR: Token verification failed (SignatureExpired).")
            return "Login link has expired.", 400
        except BadSignature as e:
            print(f"ERROR: Token verification failed (BadSignature): {e}")
            return "Invalid login link.", 400
        except Exception as e_loads:
            print(f"ERROR: Unexpected error during login_serializer.loads(): {e_loads}")
            print(traceback.format_exc())
            return "Invalid login link (verification error).", 400
        # --- END FIX ---

        if user_id:
            # Convert ID to integer, just in case loads returns it as string sometimes
            try:
                user_id_int = int(user_id)
                print(f"DEBUG: Attempting to find user with ID: {user_id_int}")
                user = user_datastore.get_user(user_id_int)
            except ValueError:
                print(f"ERROR: User ID '{user_id}' from token is not a valid integer.")
                return "Invalid login link (user ID format error)", 400
            except Exception as e_get_user:
                print(f"ERROR: Error during user_datastore.get_user: {e_get_user}")
                print(traceback.format_exc())
                return "Error retrieving user information.", 500


            if user:
                print(f"DEBUG: Found user: {user.email} from token ID.")
                # Log the user in
                logged_in = login_user(user)
                if logged_in:
                    print(f"DEBUG: User {user.email} logged in successfully via token. Redirecting...")
                    db.session.commit() # Commit session changes like last_login_at
                    return redirect(url_for('projects.index'))
                else:
                     print(f"ERROR: login_user failed for user {user.email}. User might be inactive.")
                     # db.session.rollback() # Optional rollback
                     return "Login failed (user inactive or other issue?)", 400
            else:
                print(f"ERROR: User ID {user_id_int} from token not found in database.")
                return "Invalid login link (user not found)", 400
        else:
            # This case shouldn't happen if loads() succeeded without error, but included for safety
            print("ERROR: User ID not found in token after successful load (unexpected).")
            return "Invalid login link (internal error).", 500

    except Exception as e_main:
        print("ERROR: An unexpected error occurred during token login.")
        print(traceback.format_exc())
        return f"An error occurred during login: {e_main}", 500


# (Keep the list_users and create_user functions as they were)
@users_bp.route('/users')
def list_users():
    # (Code from previous version)
    print("\n--- DEBUG: Entered list_users route ---")
    try:
        users = User.query.all()
        roles = Role.query.all()
        print(f"DEBUG: Found {len(users)} users and {len(roles)} roles.")
        return render_template('users/users.html', users=users, roles=roles)
    except Exception as e:
        print("ERROR: Failed to list users.")
        print(traceback.format_exc())
        return f"Failed to load users page: {e}", 500

@users_bp.route('/users/create', methods=['POST'])
def create_user():
    # (Code from previous version)
    print("\n--- DEBUG: Entered create_user route ---")
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        role_id = request.form.get('role_id')
        print(f"DEBUG: Received data - Name: {name}, Email: {email}, Role ID: {role_id}")

        if not all([name, email, role_id]):
             print("ERROR: Missing data for user creation.")
             return "Missing required fields for user creation.", 400

        # from main import user_datastore # Already imported at top
        print("DEBUG: Finding role by ID.")
        role = Role.query.get(role_id)
        if role:
            print(f"DEBUG: Found role: {role.name}. Attempting to create user.")
            existing_user = user_datastore.find_user(email=email)
            if existing_user:
                print(f"ERROR: User with email {email} already exists.")
                return redirect(url_for('users.list_users'))

            user = user_datastore.create_user(
                email=email,
                name=name,
                roles=[role]
            )
            db.session.commit()
            print(f"DEBUG: Successfully created user {email} with role {role.name}.")
        else:
            print(f"ERROR: Role with ID {role_id} not found.")

        return redirect(url_for('users.list_users'))
    except Exception as e:
        db.session.rollback()
        print("ERROR: Failed to create user.")
        print(traceback.format_exc())
        return redirect(url_for('users.list_users'))