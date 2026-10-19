from functools import wraps
from flask import session, redirect, url_for, flash
from extensions import db
from models import LessonCompletion, Progress, QuizResult, Lesson, Quiz, Enrollment, Course
from datetime import datetime

DATE_FORMAT = '%B %d, %Y'

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            role = session.get('role')
            if role not in roles:
                flash('Access denied', 'danger')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated
    return decorator

def format_date(date_value):
    if not date_value:
        return ''
    if isinstance(date_value, datetime):
        return date_value.strftime(DATE_FORMAT)
    try:
        parsed = datetime.fromisoformat(date_value)
        return parsed.strftime(DATE_FORMAT)
    except Exception:
        return str(date_value)


def course_metadata(course):
    lessons = course.lessons or []
    total = len(lessons)
    if hasattr(course, 'duration') and course.duration:
        duration = course.duration
    else:
        duration = f"{max(1, total * 12)} min"

    if hasattr(course, 'level') and course.level:
        level = course.level
    else:
        category = (course.category or '').strip()
        if not category or any(term in category.lower() for term in ['intro', 'beginner', 'foundation']):
            level = 'Beginner'
        elif any(term in category.lower() for term in ['advanced', 'expert', 'master']):
            level = 'Advanced'
        else:
            level = 'Intermediate'

    instructor_name = course.instructor.name if hasattr(course, 'instructor') and course.instructor else 'Staff'
    return {
        'total_lessons': total,
        'duration': duration,
        'difficulty': level,
        'instructor_name': instructor_name,
    }


def delete_course_content(course):
    lesson_ids = [lesson.id for lesson in Lesson.query.with_entities(Lesson.id).filter_by(course_id=course.id).all()]
    if lesson_ids:
        quiz_ids = [quiz.id for quiz in Quiz.query.with_entities(Quiz.id).filter(Quiz.lesson_id.in_(lesson_ids)).all()]
        Quiz.query.filter(Quiz.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        if quiz_ids:
            QuizResult.query.filter(QuizResult.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
    LessonCompletion.query.filter_by(course_id=course.id).delete(synchronize_session=False)
    Lesson.query.filter_by(course_id=course.id).delete(synchronize_session=False)
    Enrollment.query.filter_by(course_id=course.id).delete(synchronize_session=False)
    Progress.query.filter_by(course_id=course.id).delete(synchronize_session=False)
    db.session.delete(course)
    db.session.commit()

def ordered_lessons(course):
    lessons = course.lessons or []
    return sorted(lessons, key=lambda l: ((l.lesson_order or 0), l.id))

def embed_video_url(video_url):
    if not video_url:
        return None
    if 'youtube.com/watch' in video_url or 'youtu.be/' in video_url:
        import re
        match = re.search(r'(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})', video_url)
        if match:
            return f"https://www.youtube.com/embed/{match.group(1)}"
    if 'embed' in video_url:
        return video_url
    return video_url

def get_course_progress(user_id, course):
    lessons = ordered_lessons(course)
    total_lessons = len(lessons)
    completed_lessons = LessonCompletion.query.filter_by(user_id=user_id, course_id=course.id).count()
    lesson_ratio = (completed_lessons / total_lessons) if total_lessons else 0

    quiz_ids = [quiz.id for lesson in lessons for quiz in lesson.quizzes]
    total_quizzes = len(quiz_ids)
    completed_quizzes = 0
    if total_quizzes:
        completed_quizzes = (QuizResult.query
            .filter(QuizResult.user_id == user_id, QuizResult.quiz_id.in_(quiz_ids))
            .with_entities(QuizResult.quiz_id)
            .distinct()
            .count())
    quiz_ratio = (completed_quizzes / total_quizzes) if total_quizzes else 1

    if total_lessons > 0 and total_quizzes > 0:
        percent = int(round(lesson_ratio * 70 + quiz_ratio * 30))
    elif total_lessons > 0:
        percent = int(round(lesson_ratio * 100))
    else:
        percent = int(round(quiz_ratio * 100))

    is_complete = total_lessons > 0 and completed_lessons == total_lessons and completed_quizzes == total_quizzes
    return {
        'percent': min(100, percent),
        'completed_lessons': completed_lessons,
        'total_lessons': total_lessons,
        'completed_quizzes': completed_quizzes,
        'total_quizzes': total_quizzes,
        'is_complete': is_complete,
        'status': 'complete' if is_complete else 'incomplete',
    }

def update_course_progress(user_id, course):
    progress = Progress.query.filter_by(user_id=user_id, course_id=course.id).first()
    course_data = get_course_progress(user_id, course)
    if progress:
        progress.completion_percent = course_data['percent']
        progress.status = course_data['status']
    else:
        progress = Progress(
            user_id=user_id,
            course_id=course.id,
            completion_percent=course_data['percent'],
            status=course_data['status'],
        )
        db.session.add(progress)
    db.session.commit()
    return course_data
