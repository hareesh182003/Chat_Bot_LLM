# E-Commerce Django Project

This project is a full-stack e-commerce application built with Django (backend) and with simple frontend

## Features
- User authentication and management
- Product, category, supplier, inventory, order, review, payment, and shipping management
- RESTful API endpoints
- React-based chatbot UI

## Setup Instructions

### Backend (Django)
1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Start the server:
   ```bash
   python manage.py runserver
   ```

## Project Structure
- `app/` - Django app with models, views, serializers
- `chatbot-ui/` - React frontend
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation

## License
MIT
