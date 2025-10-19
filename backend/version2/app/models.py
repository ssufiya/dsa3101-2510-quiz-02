from . import db
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, unique=True)
    name = db.column(db.String)


class Question(db.model):
    __tablename__ = 'questions'
    id = db.Column(db.String)
    difficulty = db.Column(db.Integer)
    course_id = db/Column(db.Integer, db.ForeignKey('courses.id'))
    course = db.relationship('Course', backref='questions')
