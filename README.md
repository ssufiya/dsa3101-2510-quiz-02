A question bank management system for the NUS Department of Statistics & Data Science. Upload, manage, search, and version-control assessment questions with automated backup and restoration.

**Getting Started**

Prerequisites: Docker & Docker Compose installed

In your terminal, run:

	1. git clone git@github.com:ssufiya/dsa3101-2510-quiz-02.git
	
	2. cd path/to/dsa3101-2510-quiz-02
	
	3. docker compose up --build


**To check if your application is running**

<img width="585" height="453" alt="image" src="https://github.com/user-attachments/assets/444222ff-cdd0-42e6-bd38-e360d2446113" />


_Troubleshooting for first time users: if you don't see the above view and database remains empty, run (After _docker compose up_):_

	docker exec -it quizbank-backend bash
	
	python quizbank-db/scripts/init_db.py
	(To exit, type: exit)


**Services you can access:**

Frontend: http://localhost:3000  
Backend: http://localhost:5003  
API docs: http://localhost:5003/docs


_For returning developers:_  
**To restore initial database state (204 questions) after uploading new questions**

Step 1: Delete all backups and new attachments

	rm -f backend/backups/quizbank/*.sql.gz
	
	rm -f backend/backups/assets/*.tgz
	
	rm -f backend/backups/assets/*.manifest.txt
	
	rm -rf backend/quizbank-db/storage/png/*
	
	rm -rf backend/quizbank-db/storage/other/*

Step 2: Rebuild from scratch

	docker compose down -v
	
	docker compose up

