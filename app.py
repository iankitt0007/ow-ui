from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from app.config import Config
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

# Initialize the SQLAlchemy object
db.init_app(app)
migrate = Migrate(app, db)

# Automatically create tables if they do not exist
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create a user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


@app.route('/')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print('Handling signup request')
    form = SignupForm()
    if form.validate_on_submit():  # This will handle POST requests
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered!')
            return redirect(url_for('signup'))

        new_user = User(username=form.username.data, email=form.email.data, role="user")
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now log in.')
        return redirect(url_for('login'))
    
    return render_template('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!')
            return redirect(request.args.get('next') or url_for('dashboard'))        
        else:
            flash('Invalid email or password.')
            return redirect(url_for('login'))
    
    return render_template('login.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'Admin':
        users = User.query.all()
        return redirect(url_for('dashboard.html'), users=users)
    return render_template('dashboard.html', username=current_user.username)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

# Add user route (for `add_user.html`)
@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'Admin':
        flash('You do not have permission to access this page.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # This will allow setting role as 'Admin' or 'User'
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists!')
            return redirect(url_for('add_user'))
        
        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully!')
        return redirect(url_for('manage_users'))
    
    return render_template('add_user.html')


# Edit user route (for `edit_user.html`)
@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    
    if current_user.role != 'Admin' and current_user.id != id:
        flash('You do not have permission to edit this user.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        if password:
            user.set_password(password)
        user.role = role
        
        db.session.commit()
        flash('User updated successfully!')
        return redirect(url_for('manage_users'))
    
    return render_template('edit_user.html', user=user)


# Manage users route (for `manage_users.html`)
@app.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'Admin':
        flash('You do not have permission to manage users.')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('manage_users.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)
