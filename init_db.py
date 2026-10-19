from sqlalchemy import text
from app import create_app
from extensions import db
from models import User, Course, Lesson, Quiz

app = create_app()

with app.app_context():
    db.create_all()
    conn = db.engine.connect()
    try:
        result = conn.execute(text("PRAGMA table_info(quiz_results)"))
        columns = {row[1] for row in result}
        if 'date' not in columns:
            conn.execute(text("ALTER TABLE quiz_results ADD COLUMN date TEXT"))
    finally:
        conn.close()

    if not User.query.filter_by(email='admin@mini.local').first():
        admin = User(name='Administrator', email='admin@mini.local', role='admin')
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()
    print('Database initialized and admin user created (admin@mini.local / adminpass)')
