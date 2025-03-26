
from flask import Flask
from projects.projects_routes import projects_bp

app = Flask(__name__)
app.register_blueprint(projects_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
