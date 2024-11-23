# Splitwise Clone

## Overview
This is a simple expense-sharing application built with Flask, allowing users to create groups, track expenses, and split bills.

## Features
- User registration and authentication
- Create and manage expense groups
- Add expenses to groups
- Calculate and view group balances
- Track who owes what

## Setup and Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation Steps
1. Clone the repository
```bash
git clone https://github.com/yourusername/splitwise-clone.git
cd splitwise-clone
```

2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Initialize the database
```bash
flask init-db
```

5. Run the application
```bash
flask run
```

## Environment Variables
- `SECRET_KEY`: A secret key for Flask sessions
- `DATABASE_URL`: SQLAlchemy database connection string
- `FLASK_APP`: Set to `app.py`
- `FLASK_ENV`: Development or production

## Technologies Used
- Backend: Flask
- Database: SQLAlchemy
- Authentication: Flask-Login
- Frontend: Bootstrap 5

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License
MIT License
