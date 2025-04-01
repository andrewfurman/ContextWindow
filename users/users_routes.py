
from flask import Blueprint, render_template, request, redirect, url_for
from flask_mail import Message
from .users_model import User, Role, db
from main import mail

users_bp = Blueprint('users', __name__)

@users_bp.route('/users_login')
def login():
    return render_template('users/users_login.html')

@users_bp.route('/send-login-link', methods=['POST'])
def send_login_link():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        from main import user_datastore
        user = user_datastore.create_user(
            email=email,
            name=email.split('@')[0]  # Simple default name from email
        )
        db.session.commit()
    
    from flask_security.utils import hash_password, get_token_status
    from flask_security import login_token_status
    
    # Generate login token
    token = user_datastore.login_token_status(user)
    login_link = url_for('users.login_with_token', token=token, _external=True)
    
    msg = Message(
        "Your Login Link",
        recipients=[email],
        body=f"Click this link to log in (valid for 24 hours): {login_link}"
    )
    mail.send(msg)
    return "Login link has been sent to your email", 200

@users_bp.route('/login/<token>')
def login_with_token(token):
    from main import security
    user = security.login_token_verifier(token)
    if user:
        from flask_security.utils import login_user
        login_user(user)
        return redirect(url_for('projects.index'))
    return "Invalid or expired login link", 400

@users_bp.route('/users')
def list_users():
    users = User.query.all()
    roles = Role.query.all()
    return render_template('users/users.html', users=users, roles=roles)

@users_bp.route('/users/create', methods=['POST'])
def create_user():
    name = request.form.get('name')
    email = request.form.get('email')
    role_id = request.form.get('role_id')
    
    from main import user_datastore
    
    role = Role.query.get(role_id)
    if role:
        user = user_datastore.create_user(
            email=email,
            name=name,
            roles=[role]
        )
        db.session.commit()
    
    return redirect(url_for('users.list_users'))
