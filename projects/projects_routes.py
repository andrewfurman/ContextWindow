
from flask import Blueprint, render_template

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/')
def index():
    return render_template('projects/projects.html')
