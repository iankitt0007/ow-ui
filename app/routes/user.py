from flask import Blueprint, render_template, redirect, url_for, request
from app.forms.user_forms import UserForm
from app.models.user import User
from flask_login import login_required

bp = Blueprint('user', __name__)

@bp.route('/user/add', methods=['GET', 'POST'])
@login_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('user.manage_users'))
    return render_template('add_user.html', form=form)

@bp.route('/user/manage')
@login_required
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        db.session.commit()
        return redirect(url_for('user.manage_users'))
    return render_template('edit_user.html', form=form, user=user)
