A question bank management system for the NUS Department of Statistics & Data Science. Upload, manage, search, and version-control assessment questions with automated backup and restoration.


**Getting Started**

Prerequisites: Docker & Docker Compose installed

For returning users: Run _docker compose down -v_ first to clean up

In your terminal, run:
1. git clone git@github.com:ssufiya/dsa3101-2510-quiz-02.git
2. cd path/to/dsa3101-2510-quiz-02
3. docker compose up --build


**To check if your application is running**
<img width="585" height="453" alt="image" src="https://github.com/user-attachments/assets/444222ff-cdd0-42e6-bd38-e360d2446113" />




**Services you can access:**

Frontend: https://localhost:3000

Backend: https://localhost:5003

API docs: https://localhost:5003/docs



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

