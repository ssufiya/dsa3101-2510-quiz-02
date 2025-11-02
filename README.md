A question bank management system for the NUS Department of Statistics & Data Science. Upload, manage, search, and version-control assessment questions with automated backup and restoration.


**Getting Started**

Prerequisites: Docker & Docker Compose installed

For returning users: Run _docker compose down -v_ first to clean up

In your terminal, run:
1. git clone git@github.com:ssufiya/dsa3101-2510-quiz-02.git
2. cd path/to/dsa3101-2510-quiz-02
3. _docker compose up --build_

Troubleshooting for first time users: 

if the database remains empty, run (After _docker compose up_):

_docker exec -it quizbank-backend bash_

_python quizbank-db/scripts/init_db.py_
(To exit, type: _exit_)


**To check if your application is running**

<img width="585" height="453" alt="image" src="https://github.com/user-attachments/assets/444222ff-cdd0-42e6-bd38-e360d2446113" />





**Services you can access:**

Frontend: http://localhost:3000

Backend: http://localhost:5003

API docs: http://localhost:5003/docs



**To restore initial database state (204 questions) after uploading new questions**

Step 1: Delete all backups and new attachments

_rm -f backend/backups/quizbank/*.sql.gz_

_rm -f backend/backups/assets/*.tgz_

_rm -f backend/backups/assets/*.manifest.txt_

_rm -rf backend/quizbank-db/storage/png/*_

_rm -rf backend/quizbank-db/storage/other/*_

Step 2: Rebuild from scratch

_docker compose down -v_

_docker compose up_

