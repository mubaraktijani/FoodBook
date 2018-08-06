#!/usr/bin/env python
import os
import json
import _thread
import serial
from PIL import Image
from config import config
from flask import Flask, render_template, session, redirect, request, url_for, flash
from forms import LoginForm, MenuItemForm, ChangePasswordForm, UserForm
from threading import Lock
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_script import Manager
from flask_socketio import SocketIO, emit
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from werkzeug.utils import secure_filename

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None
db = SQLAlchemy()
#serial = serial.Serial('/dev/ttyACM0', 9600)
#serial = serial.Serial('COM11', 9600)
bootstrap = Bootstrap()
login_manager = LoginManager()

login_manager.session_protection = 'strong'
login_manager.login_view = 'login'

thread = None
thread_lock = Lock()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)
    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)

    return app

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
socketio = SocketIO(app, async_mode=async_mode)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    username = db.Column(db.Text())
    password = db.Column(db.Text())
    avatar = db.Column(db.Text())
    user_role = db.Column(db.Integer())
    user_status = db.Column(db.Integer())

    def get_id(self):
        return (self.user_id)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@login_required
def welcome():
    
    total_menu = db.engine.execute(
        text("SELECT COUNT(*) AS total_menu FROM menus")).first()

    total_user = db.engine.execute(
        text("SELECT COUNT(*) AS total_user FROM users")).first()
    menus = db.engine.execute(
        text("SELECT menu_id as id, menu_name as name, menu_desc as desc, menu_price as price, menu_photo as photo from menus ORDER BY menu_id ASC LIMIT 100"))

    data = {
        'total_menu': total_menu.total_menu,
        'total_user': total_user.total_user,
        'menus': menus
    }

    return render_template('index.html', auth=current_user, data=data, async_mode=socketio.async_mode)

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data, password=form.password.data).first()

        if user is not None:
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('welcome'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html', form=form)

@app.route('/auth/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('welcome'))

@app.route('/menus')
#@login_required
def menus():
    menus = db.engine.execute(
        text("SELECT menu_id as id, menu_name as name, menu_price as price, menu_photo as photo from menus ORDER BY menu_id ASC LIMIT 100"))
    return render_template('menus.html', auth=current_user, menus=menus, async_mode=socketio.async_mode)

@app.route('/menus/new', methods=['GET', 'POST'])
#@login_required
def new_menu():
    form = MenuItemForm()

    if form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        desc = form.desc.data
        photo = form.photo.data
        photo_name = secure_filename(photo.filename)
        photo_path = os.path.join('static/images/menus', photo_name)
        thumb_path = os.path.join('static/images/menus/thumbs', photo_name)
        thumb_size = 128, 128

        menu = db.engine.execute(
            text("SELECT * FROM menus WHERE menu_name = :name AND menu_price = :price LIMIT 1"), {"name": name, "price": price}).first()
            
        # add new staff if not exists
        if menu is None:
            # save staff photo
            photo.save(photo_path)

            # create thumbnail for staff
            try:
                im = Image.open(photo_path)
                im.thumbnail(thumb_size, Image.ANTIALIAS)
                im.save(thumb_path, "JPEG")
            except IOError:
                flash("cannot create thumbnail for this menu item")

            # save user and the thumbnail name
            insertSql = "INSERT INTO menus (menu_name, menu_price, menu_desc, menu_photo) VALUES (:mname, :mprice, :mdesc, :mphoto)"
            insertParams = {'mname': name, 'mprice': price, 'mdesc': desc, 'mphoto': photo_name}
            db.engine.execute(text(insertSql), insertParams)

            flash('New menu item added successfully.')
            return redirect(url_for('menus'))

        else:
            flash('Menu item already exists.')

    return render_template('new-menu-item.html', auth=current_user, form = form, async_mode=socketio.async_mode)


@app.route('/orders')
@login_required
def orders():
    menus = db.engine.execute(
            text("SELECT \
                m.menu_id as id, m.menu_name as name, m.menu_price as price, \
                m.menu_desc as desc, m.menu_photo as photo, b.booking_status as status  \
            FROM \
                bookings AS b JOIN menus m ON b.menu_id = m.menu_id \
            WHERE \
                b.user_id = :uid \
            ORDER BY b.created_at ASC LIMIT 100"), {
                'uid': current_user.user_id
            })
    
    data = {
        'menus': menus
    }
    return render_template('index.html', auth=current_user, data=data, page='bookings', async_mode=socketio.async_mode)


@app.route('/order/<mid>')
@login_required
def order(mid):
    '''order = db.engine.execute(text("SELECT * FROM bookings WHERE user_id = :uid AND menu_id = :mid"), {
                "uid": current_user.user_id, 
                "mid": mid
            }).first()'''

    #if order is not None:
         # save user and the thumbnail name
    insertSql = "INSERT INTO bookings (user_id, menu_id) VALUES (:uid, :mid)"
    db.engine.execute(text(insertSql), {
        "uid": current_user.user_id, 
        "mid": mid
    })

    flash('Item Book Successfully!.')
        
    return redirect(url_for(request.args.get('next')) or url_for('menus'))


##############################################
## CHANGE PASSWORD ROUTE
##############################################
@app.route('/auth/change-password', methods=['GET', 'POST'])
#@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        old_password = form.password.data
        new_password = form.new_password.data
        cfm_password = form.confirm_password.data

        user = User.query.filter_by(user_id=current_user.user_id, password=old_password).first()

        if user is not None:
            if new_password == cfm_password:
                # update admin password
                insertSql = "UPDATE users SET password = :password WHERE user_id = :id"
                insertParams = {
                    "password": new_password,
                    "id": current_user.user_id
                }
                db.engine.execute(text(insertSql), insertParams)

                flash('Password changed successful!', 'success')
            else:
                flash('New Password and Confirm Password not match!')
        else:
            flash('incorrect password. please try again!')

    return render_template('change-password.html', auth=current_user, form=form, active='password')



##############################################
## STAFF ROUTE
##############################################
@app.route('/users', methods=['GET'])
#@login_required
def users():
    trash = 0
    if 'trash' in request.args:
        trash = 1
        users = db.engine.execute(
            text("SELECT * FROM users WHERE user_status = 0 ORDER BY name DESC LIMIT 100"))
    else:
        users = db.engine.execute(
            text("SELECT * FROM users WHERE user_status != 0 ORDER BY name DESC LIMIT 100"))

    return render_template('users.html', auth=current_user, users=users, trash=trash, active='users')

@app.route('/user/<uid>', methods=['GET'])
@login_required
def user(uid):
    edit = 0
    if 'edit' in request.args:
        edit = request.args['edit']

    if 'status' in request.args:
        status = request.args['status']
        
        # TRASH USER
        if status == '0':
            db.engine.execute(
                text("UPDATE users SET user_status = 0 WHERE user_id = :id"), {"id": uid})
            return redirect(url_for(request.args.get('next')) or url_for('user'))
        
        # ENABLE USER
        if status == '1':
            db.engine.execute(
                text("UPDATE users SET user_status = 1 WHERE user_id = :id"), {"id": uid})
            return redirect(url_for(request.args.get('next')) or url_for('user'))

        # BLOCK USER
        if status == '2':
            db.engine.execute(
                text("UPDATE users SET user_status = 2 WHERE user_id = :id"), {"id": uid})
            return redirect(url_for(request.args.get('next')) or url_for('user'))

    user = db.engine.execute(
        text("SELECT * FROM users WHERE user_id = :id"), {'id': uid}).first()

    return render_template('user.html', auth=current_user, user=user, edit=edit, active='users')
                

@app.route('/user/new', methods=['GET', 'POST'])
#@login_required
def new_user():
    form = UserForm()

    if form.validate_on_submit():
        card_id = form.card_id.data
        fullname = form.fullname.data
        email = form.email.data
        password = form.password.data
        photo = form.photo.data
        
        photo_name = secure_filename(photo.filename)
        photo_path = os.path.join('static/images/users', photo_name)
        thumb_path = os.path.join('static/images/users/thumb', photo_name)
        thumb_size = 128, 128

        staff = db.engine.execute(
            text("SELECT * FROM users WHERE card_id = :id AND email=:email"), {"id": card_id, "email": email}).first()
            
        # add new staff if not exists
        if staff is None:
            # save staff photo
            photo.save(photo_path)

            # create thumbnail for staff
            try:
                im = Image.open(photo_path)
                im.thumbnail(thumb_size, Image.ANTIALIAS)
                im.save(thumb_path, "JPEG")
            except IOError:
                flash("cannot create thumbnail for this user")

            # save user and the thumbnail name
            insertSql = "\
                INSERT INTO users (card_id, name, username, email, password, avatar) \
                VALUES (:card_id, :name, :username, :email, :password, :avatar)"
            insertParams = {
                'card_id': card_id,
                'name': fullname,
                'username': fullname,
                'email': email,
                'password': password,
                'avatar': photo_name
            }
            db.engine.execute(text(insertSql), insertParams)

            flash('User created successfully.')
            return redirect(url_for('users'))

        else:
            flash('User Already Exists.')

    return render_template('new-user.html', form=form, auth=current_user, active='users')


'''
@app.route('/patient/<card_id>')
@login_required
def patientInfo(card_id):
    patient = db.engine.execute(
        text("SELECT p.*, b.blood_group_name from patients as p \
        JOIN blood_groups b on p.blood_group_id = b.blood_group_id \
        WHERE p.card_id=:cardID"), {'cardID': card_id}).first()

    if patient is None:
        return redirect(url_for('add_patient', card_id=card_id))
    return render_template('patient-info.html', auth=current_user, async_mode=socketio.async_mode, patient=patient)
'''
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

'''

def background_thread():
    while True:
        patient = int(serial.readline())
        print(patient)
        socketio.emit('paish', {'data': patient}, namespace='/test')
        socketio.sleep(1)

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


#manager = Manager(app)
'''
if __name__ == '__main__':
    #socketio.run(app, debug=False)
    socketio.run(app)
    #manager.run()
