
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
    msg = Message(
        "Login Link",
        recipients=[email],
        body="Here is your login link (implement actual link generation)"
    )
    mail.send(msg)
    return "Login link has been sent to your email", 200

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
