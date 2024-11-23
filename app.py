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

# Add abs filter for Jinja2 templates
@app.template_filter('abs')
def abs_filter(number):
    return abs(number)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
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
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref='created_groups')
    members = db.relationship('User', secondary='user_groups', back_populates='groups')
    expenses = db.relationship('Expense', back_populates='group')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    split_type = db.Column(db.String(20), nullable=False, default='equal')  # 'equal' or 'custom'
    payer = db.relationship('User', back_populates='expenses')
    group = db.relationship('Group', back_populates='expenses')
    shares = db.relationship('ExpenseShare', back_populates='expense', cascade='all, delete-orphan')

class ExpenseShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    share_amount = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    expense = db.relationship('Expense', back_populates='shares')
    user = db.relationship('User')

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
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
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
        new_group = Group(name=group_name, creator=current_user)
        new_group.members.append(current_user)
        db.session.add(new_group)
        db.session.commit()
        
        flash('Group created successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('create_group.html')

@app.route('/group/<int:group_id>/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense(group_id):
    group = Group.query.get_or_404(group_id)
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        split_type = request.form.get('split_type', 'equal')
        
        # Create the expense
        expense = Expense(
            description=description,
            amount=amount,
            payer=current_user,
            group=group,
            split_type=split_type
        )
        db.session.add(expense)
        
        # Calculate and create shares
        if split_type == 'equal':
            per_person_share = amount / len(group.members)
            for member in group.members:
                share = ExpenseShare(
                    expense=expense,
                    user=member,
                    share_amount=per_person_share,
                    paid=(member == current_user)  # Payer's share is marked as paid
                )
                db.session.add(share)
        else:
            # Handle custom splits
            for member in group.members:
                share_amount = float(request.form.get(f'share_{member.id}', 0))
                if share_amount > 0:
                    share = ExpenseShare(
                        expense=expense,
                        user=member,
                        share_amount=share_amount,
                        paid=(member == current_user)
                    )
                    db.session.add(share)
        
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('group_details', group_id=group_id))
    
    return render_template('add_expense.html', group=group)

@app.route('/group/<int:group_id>')
@login_required
def group_details(group_id):
    group = Group.query.get_or_404(group_id)
    expenses = group.expenses
    
    return render_template('group_details.html', group=group, expenses=expenses)

@app.route('/group/<int:group_id>/members', methods=['GET', 'POST'])
@login_required
def manage_members(group_id):
    group = Group.query.get_or_404(group_id)
    
    # Check if user is group creator
    if group.creator != current_user:
        flash('Only the group creator can add members.', 'danger')
        return redirect(url_for('group_details', group_id=group_id))
    
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please provide an email address.', 'danger')
            return redirect(url_for('manage_members', group_id=group_id))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No user found with that email address.', 'danger')
            return redirect(url_for('manage_members', group_id=group_id))
        
        if user in group.members:
            flash('User is already a member of this group.', 'warning')
            return redirect(url_for('manage_members', group_id=group_id))
        
        group.members.append(user)
        db.session.commit()
        flash(f'{user.email} has been added to the group.', 'success')
        return redirect(url_for('manage_members', group_id=group_id))
    
    return render_template('add_members.html', group=group)

@app.route('/group/<int:group_id>/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_member(group_id, user_id):
    group = Group.query.get_or_404(group_id)
    
    # Check if user is group creator
    if group.creator != current_user:
        flash('Only the group creator can remove members.', 'danger')
        return redirect(url_for('group_details', group_id=group_id))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent removing the creator
    if user == group.creator:
        flash('Cannot remove the group creator.', 'danger')
        return redirect(url_for('manage_members', group_id=group_id))
    
    if user not in group.members:
        flash('User is not a member of this group.', 'danger')
        return redirect(url_for('manage_members', group_id=group_id))
    
    group.members.remove(user)
    db.session.commit()
    flash(f'{user.email} has been removed from the group.', 'success')
    return redirect(url_for('manage_members', group_id=group_id))

# Utility function to calculate balances
def calculate_group_balances(group):
    balances = {}
    
    # Initialize balances for all members
    for member in group.members:
        balances[member.username] = {
            'paid': 0,      # Total amount paid by this user
            'owed': 0,      # Total amount this user owes to others
            'owed_by': {},  # Detailed breakdown of who owes this user
            'owes_to': {}   # Detailed breakdown of whom this user owes
        }
    
    # Calculate balances from expense shares
    for expense in group.expenses:
        payer = expense.payer
        payer_username = payer.username
        
        # Add to total paid amount for the payer
        balances[payer_username]['paid'] += expense.amount
        
        # Process each share
        for share in expense.shares:
            user = share.user
            username = user.username
            
            if user != payer:
                # Update amount owed to payer
                if payer_username not in balances[username]['owes_to']:
                    balances[username]['owes_to'][payer_username] = 0
                balances[username]['owes_to'][payer_username] += share.share_amount
                
                # Update amount owed by others to payer
                if username not in balances[payer_username]['owed_by']:
                    balances[payer_username]['owed_by'][username] = 0
                balances[payer_username]['owed_by'][username] += share.share_amount
                
                # Update total owed amounts
                balances[username]['owed'] += share.share_amount
    
    # Calculate net balance for each user
    for username in balances:
        balances[username]['net'] = round(
            balances[username]['paid'] - balances[username]['owed'], 
            2
        )
        
        # Round all the detailed amounts
        for other_user in balances[username]['owes_to']:
            balances[username]['owes_to'][other_user] = round(
                balances[username]['owes_to'][other_user], 
                2
            )
        for other_user in balances[username]['owed_by']:
            balances[username]['owed_by'][other_user] = round(
                balances[username]['owed_by'][other_user], 
                2
            )
    
    return balances

@app.route('/group/<int:group_id>/balances')
@login_required
def group_balances(group_id):
    group = Group.query.get_or_404(group_id)
    balances = calculate_group_balances(group)
    
    return render_template('group_balances.html', group=group, balances=balances)

# Initialize database
def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    app.run(host='localhost', port=5001, debug=True)
