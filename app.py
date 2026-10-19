from flask import Flask, render_template
from sqlalchemy import text
from config import Config
from extensions import db

from blueprints.auth.routes import auth_bp
from blueprints.admin.routes import admin_bp
from blueprints.instructor.routes import instr_bp
from blueprints.student.routes import student_bp
from blueprints.courses.routes import courses_bp


def apply_database_migrations(app):
    with app.app_context():
        db.create_all()
        conn = db.engine.connect()
        try:
            result = conn.execute(text("PRAGMA table_info(quiz_results)"))
            columns = {row[1] for row in result}
            if 'date' not in columns:
                conn.execute(text("ALTER TABLE quiz_results ADD COLUMN date TEXT"))

            course_columns = conn.execute(text("PRAGMA table_info(courses)"))
            course_column_names = {row[1] for row in course_columns}
            if 'duration' not in course_column_names:
                conn.execute(text("ALTER TABLE courses ADD COLUMN duration TEXT"))
            if 'level' not in course_column_names:
                conn.execute(text("ALTER TABLE courses ADD COLUMN level TEXT"))

            lesson_columns = conn.execute(text("PRAGMA table_info(lessons)"))
            lesson_column_names = {row[1] for row in lesson_columns}
            if 'lesson_order' not in lesson_column_names:
                conn.execute(text("ALTER TABLE lessons ADD COLUMN lesson_order INTEGER NOT NULL DEFAULT 0"))
        finally:
            conn.close()


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)
    db.init_app(app)
    apply_database_migrations(app)

    # register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp)
    app.register_blueprint(instr_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(courses_bp)

    @app.route('/')
    def index():
        return render_template('base_home.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
