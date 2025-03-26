
from flask import Blueprint, render_template, request, redirect, url_for
from .users_model import User, Role, db

users_bp = Blueprint('users', __name__)

@users_bp.route('/login')
def login():
    return render_template('users/login.html')

@users_bp.route('/send-login-link', methods=['POST'])
def send_login_link():
    email = request.form.get('email')
    # TODO: Implement email sending logic
    return "Login link has been sent to your email (not implemented yet)", 200

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
    
    user = User(name=name, email=email, role_id=role_id)
    db.session.add(user)
    db.session.commit()
    
    return redirect(url_for('users.list_users'))
