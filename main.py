
import os
from flask import Flask, url_for
from flask_mail import Mail
from projects.projects_routes import projects_bp
from projects.projects_model import db

mail = Mail()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail settings
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

db.init_app(app)
mail.init_app(app)

# Import models before creating tables
from users.users_model import Role, User
from projects.projects_model import Project

with app.app_context():
    # Create all tables first
    db.create_all()
    
    try:
        # Create default roles if they don't exist
        default_roles = ['admin', 'pending', 'analyst']
        for role_name in default_roles:
            if not Role.query.filter_by(name=role_name).first():
                role = Role(name=role_name)
                db.session.add(role)
        db.session.commit()
    except Exception as e:
        print(f"Error creating roles: {e}")
        db.session.rollback()

from users.users_routes import users_bp

app.register_blueprint(projects_bp)
app.register_blueprint(users_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
