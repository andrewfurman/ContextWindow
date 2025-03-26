
import os
from flask import Flask, url_for
from projects.projects_routes import projects_bp
from projects.projects_model import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    
    # Create default roles if they don't exist
    from users.users_model import Role
    default_roles = ['admin', 'pending', 'analyst']
    for role_name in default_roles:
        if not Role.query.filter_by(name=role_name).first():
            role = Role(name=role_name)
            db.session.add(role)
    db.session.commit()

app.register_blueprint(projects_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
