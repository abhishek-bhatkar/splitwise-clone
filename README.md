# Splitwise Clone

## Overview
A comprehensive expense-sharing application built with Flask that helps users manage shared expenses within groups. This application allows users to create groups, add members, track expenses with both equal and custom splits, and provides detailed balance calculations and settlement plans.

## Features

### User Management
- User registration and authentication
- Secure password hashing with Flask-Bcrypt
- User profile management

### Group Management
- Create and manage expense groups
- Add/remove group members
- Group creator privileges
- Member access control

### Expense Tracking
- Add expenses with descriptions and amounts
- Support for both equal and custom splits
- Real-time split calculations
- Track payment status
- Multiple split options:
  - Equal split among all members
  - Custom split with individual amounts

### Balance Tracking
- Detailed balance calculations
- Per-user summary showing:
  - Total amount paid
  - Total amount owed
  - Net balance
- Detailed breakdown of:
  - Who owes whom
  - Individual transaction history
  - Settlement suggestions

### User Interface
- Clean, modern Bootstrap 5 design
- Responsive layout for mobile and desktop
- Interactive forms with real-time validation
- Clear visual indicators for balances
- Intuitive navigation

## Setup and Installation

### Prerequisites
- Python 3.10+
- pip (Python package manager)
- SQLite (included with Python)

### Installation Steps
1. Clone the repository
```bash
git clone https://github.com/abhishek-bhatkar/splitwise-clone.git
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

4. Set up environment variables
Create a `.env` file in the project root with:
```
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///instance/database.db
FLASK_APP=app.py
FLASK_ENV=development
```

5. Initialize the database
```bash
python3 init_database.py
```

6. Run the application
```bash
python3 app.py
```

The application will be available at `http://localhost:5001`

## Technologies Used
- **Backend Framework**: Flask
- **Database**: SQLAlchemy with SQLite
- **Authentication**: Flask-Login
- **Password Hashing**: Flask-Bcrypt
- **Frontend**: Bootstrap 5
- **Environment Management**: python-dotenv

## Project Structure
```
splitwise/
├── app.py              # Main application file
├── init_database.py    # Database initialization script
├── requirements.txt    # Project dependencies
├── instance/          # SQLite database location
└── templates/         # HTML templates
    ├── base.html
    ├── index.html
    ├── register.html
    ├── login.html
    ├── dashboard.html
    ├── create_group.html
    ├── group_details.html
    ├── add_members.html
    ├── add_expense.html
    └── group_balances.html
```

## Database Schema
- **User**: Stores user information and authentication details
- **Group**: Manages expense groups and their creators
- **Expense**: Tracks individual expenses and their details
- **ExpenseShare**: Manages individual shares of expenses
- **UserGroups**: Manages many-to-many relationship between users and groups

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Future Enhancements
- Currency support
- Expense categories
- Recurring expenses
- Email notifications
- Export to PDF/CSV
- Mobile app integration
- Real-time updates
- Advanced analytics

## License
MIT License - See LICENSE file for details
