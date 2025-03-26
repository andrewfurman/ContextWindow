
from flask import Blueprint, render_template
from .users_model import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
def list_users():
    users = User.query.all()
    return render_template('users/users.html', users=users)
