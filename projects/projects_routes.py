
from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from .projects_model import db, Project

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/')
def index():
    projects = Project.query.all()
    return render_template('projects/projects.html', projects=projects)

@projects_bp.route('/add', methods=['POST'])
def add_project():
    name = request.form.get('name')
    short_description = request.form.get('short_description')
    background = request.form.get('background')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    project = Project(
        name=name,
        short_description=short_description,
        background=background,
        start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else None,
        end_date=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    )

    db.session.add(project)
    db.session.commit()

    return redirect(url_for('projects.index'))
