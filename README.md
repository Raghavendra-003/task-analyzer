# Smart Task Analyzer

A mini-application that scores and prioritizes tasks using a configurable algorithm balancing urgency, importance, effort, and dependencies. Built with Django (backend) and vanilla HTML/CSS/JS (frontend).

## Setup instructions

### Backend
1. **Create venv and install:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt

## frontend running 
   python -m http.server 800 --bind 127.0.0.1 

## backend running
   python manage.py runserver
