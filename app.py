from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    groups = db.relationship('Group', secondary='user_groups', back_populates='members')
    expenses = db.relationship('Expense', back_populates='payer')

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    members = db.relationship('User', secondary='user_groups', back_populates='groups')
    expenses = db.relationship('Expense', back_populates='group')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    payer = db.relationship('User', back_populates='expenses')
    group = db.relationship('Group', back_populates='expenses')

# Association tables
user_groups = db.Table('user_groups',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create new user
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful!')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        group_name = request.form['group_name']
        new_group = Group(name=group_name)
        new_group.members.append(current_user)
        db.session.add(new_group)
        db.session.commit()
        
        flash('Group created successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('create_group.html')

@app.route('/add_expense/<int:group_id>', methods=['GET', 'POST'])
@login_required
def add_expense(group_id):
    group = Group.query.get_or_404(group_id)
    
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        
        new_expense = Expense(
            description=description, 
            amount=amount, 
            payer=current_user, 
            group=group
        )
        db.session.add(new_expense)
        db.session.commit()
        
        flash('Expense added successfully!')
        return redirect(url_for('group_details', group_id=group_id))
    
    return render_template('add_expense.html', group=group)

@app.route('/group/<int:group_id>')
@login_required
def group_details(group_id):
    group = Group.query.get_or_404(group_id)
    expenses = group.expenses
    
    return render_template('group_details.html', group=group, expenses=expenses)

# Utility function to calculate balances
def calculate_group_balances(group):
    balances = {}
    total_expenses = {}
    
    # Calculate total expenses per user
    for expense in group.expenses:
        payer = expense.payer
        if payer.id not in total_expenses:
            total_expenses[payer.id] = 0
        total_expenses[payer.id] += expense.amount
    
    # Calculate each member's share
    total_group_expense = sum(total_expenses.values())
    members_count = len(group.members)
    per_person_share = total_group_expense / members_count
    
    # Calculate individual balances
    for member in group.members:
        member_total_paid = total_expenses.get(member.id, 0)
        balance = member_total_paid - per_person_share
        balances[member.username] = round(balance, 2)
    
    return balances

@app.route('/group/<int:group_id>/balances')
@login_required
def group_balances(group_id):
    group = Group.query.get_or_404(group_id)
    balances = calculate_group_balances(group)
    
    return render_template('group_balances.html', group=group, balances=balances)

# Initialize database
@app.cli.command('init-db')
def init_db():
    db.create_all()
    print('Database initialized!')

if __name__ == '__main__':
    app.run(host='localhost', port=5001, debug=True)
