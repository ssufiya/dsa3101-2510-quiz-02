import os
import pandas as pd
from app import create_app, db
from app.models import Question, Course

app = create_app()
app.app_context().push()

def sync_csv_to_db(csv_path = "data/master_questions.csv"):
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    existing = {q.question_text for q in Question.query.all()}

    for _, row in df.iterrows():
        text = row.get("question_text")
        if not text or text in existing:
            continue

        diff = int(row.get("difficulty")) if pd.notna(row.get("difficulty")) else None
        course_code = row.get("course_code")

        course = Course.query.flter_by(code=course_code).first()
        q = Question(question_text=text, difficulty=diff, course=course)
        db.session.add(q)
        existing.add(text)

    db.session.commit()
    print("CSV synced to DB")

if __name__ == "__main__":
    sync_csv_to_db()