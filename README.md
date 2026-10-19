Mini Learn - Mini Digital Learning Platform

Setup

1. Create a virtualenv and install requirements:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Initialize database:

```
python init_db.py
```

3. Run app:

```
python app.py
```

Demo credentials: admin@mini.local / adminpass

Testing

- Register as student, enroll in course, take quiz.
- Create instructor account via admin, login as instructor, create course and lessons.

Files
- app.py: app factory and runner
- models.py: SQLAlchemy models
- blueprints/: route modules
- templates/: Jinja2 templates
- static/: CSS
- init_db.py: creates DB and admin user
- schema.sql: raw SQL schema
