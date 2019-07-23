# -*- coding: utf-8 -*-
""" Init """
import json
import string
import random
import os
import unicodedata
import datetime

from base64 import b64encode
from threading import Lock
from flask_qrcode import QRcode
from flask import Flask, render_template, session, \
	redirect, url_for, request, flash, abort, send_file
from flask_login import login_required, \
	login_user, logout_user, LoginManager, UserMixin, current_user
from flask_socketio import SocketIO, emit, \
	join_room, leave_room, close_room, rooms, disconnect
import pymysql.cursors


#import de las clases creadas
from user import User
from util.mapeobd import MapeoBD
from util.nocache import nocache
from forms.userzeroform import UserZeroForm
from forms.phoneform import PhoneForm
from forms.missionform import MissionForm


# Set this variable to "THREADing", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the APPlication to choose
# the best option based on installed packages.
ASYN_MODE = None

#diccionario para la creacion de usuario, mantiene todos los usuarios creados segun ID
STORED_USERS = {}


APP = Flask(__name__)
APP.debug = True
APP.secret_key = 'James Bond'
APP.config['SECRET_KEY'] = 'secret!'
SOCKETIO = SocketIO(APP, async_mode=ASYN_MODE)
THREAD = None
THREAD_LOCK = Lock()


#config flask-login
LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)
LOGIN_MANAGER.login_view = "login"

#enviroment config db
APP.config['HOST_DB'] = 'localhost'
APP.config['NAME_DB'] = 'DB_MOA'

#esto hay que reemplazarlo por el ingreso en la consola
#APP.config['USER_DB'] = os.environ.get('USER_DB')
#APP.config['PASSWORD_DB'] = os.environ.get('PASSWORD_DB')
APP.config['USER_DB'] = 'bustamante'
APP.config['PASSWORD_DB'] = 'usach1234'


#inicializacion para la base de datos y las consultas
MAPPTOBD = MapeoBD(APP.config['HOST_DB'], APP.config['USER_DB'], APP.config['PASSWORD_DB'], APP.config['NAME_DB'])


#iniciazion del plugin para generar codigos QR
QRCODE = QRcode(APP)


def elimina_tildes(cadena):
	"""function for delete accent mark"""
	s_return = ''.join((c for c in unicodedata.normalize('NFD', unicode(cadena))if unicodedata.category(c) != 'Mn'))
	return s_return.decode()


@APP.route('/')
@APP.route('/index')
@login_required
def main():
	"""main function"""
	labels = ["Mavick Air", "Phantom 4", "Phantom 4 Pro", "Inspire", "Inspire 2", "Otro", "Otro 2", "Otro 3"]
	values = [10, 9, 8, 7, 6, 4, 3, 2]
	labels2 = ["January", "February", "March", "April", "May", "June", "July", "August"]
	values2 = [10, 9, 8, 7, 6, 4, 7, 8]
	return render_template('dashboard.html', values=values, labels=labels, values2=values2, labels2=labels2)

@APP.route('/login', methods=['POST', 'GET'])
def login():
	"""function for do login in the app"""
	#si estamos haciendo un POST de la informacion
	if request.method == 'POST':
		_name = request.form['inputEmail']
		_pass = request.form['inputPassword']
		result = MAPPTOBD.login_user(_name, _pass)
		#si es que result tiene algo, o sea, si es que las credenciales son correctas y puede ingresar en la plataforma
		if result != None:
			user = User(result)
			STORED_USERS[result['ID_USER']] = user
			#checkbox presionado, por lo tanto quiere ser recordado
			if request.form.get('remember-me'):
				login_user(user, remember=True)
			#no esta activado el checkbox, por lo que no quiere ser recordado
			else:
				login_user(user)
			#retornamos a la pagina solicitada o la principal
			return redirect(request.args.get('next') or url_for('main'))
		#si no puede ingresar a la plataforma o tiene algun parámetro incorrecto
		else:
			flash(u'Error al ingresar las credenciales de acceso. Inténtelo de nuevo.', 'message')
			return render_template('login.html')
			#return abort(401)
	#si estamos haciendo un GET de la informacion
	else:
		#renderizamos el template
		return render_template('login.html')


@APP.route('/profile', methods=['GET'])
@login_required
def profile():
	"""function for profile"""
	image = None
	#si tiene imagen de perfil, entonces
	if current_user.get_data().get('picture') != None:
		image = b64encode(current_user.get_data().get("picture"))
	#si no tiene imagen de perfil, entonces cargamos la de defecto
	else:
		none_image = MAPPTOBD.get_profile_image('none')
		image = b64encode(none_image['PIC_USER'])
	return render_template('profile.html', image=image)


@APP.route('/logout')
@login_required
def logout():
	"""function for logout"""
	logout_user()
	return redirect('/')


@APP.route('/superadmin', methods=['POST', 'GET'])
@login_required
def create_user():
	"""function for create user"""
	if request.method == 'POST':
		data = {}
		data['name'] = request.form['name']
		data['last1'] = request.form['lastname1']
		data['last2'] = request.form['lastname2']
		data['city'] = request.form['city']
		data['state'] = request.form['state']
		data['country'] = request.form['country']
		data['email'] = request.form['email']
		data['phone'] = request.form['phone']
		data['password'] = "1234abcd"
		data['username'] = MAPPTOBD.create_username(elimina_tildes(data['name'].lower()), elimina_tildes(data['last1'].lower()), elimina_tildes(data['last2'].lower()), 0)
		data['status'] = 1
		data['admin'] = 1
		if MAPPTOBD.store_new_user(data):
			flash('Usuario agregado correctamente.', 'success')
		else:
			#mensaje de que hubo un problema
			flash('Error al ingresar el nuevo usuario.', 'error')
		return render_template('superadmin.html')
	else:
		if current_user.get_data().get('admin') == 999:
			return render_template('superadmin.html')
		else:
			return abort(403)

def flash_errors(form):
	"""function for show flash errors"""
	for field, errors in form.errors.items():
		for error in errors:
			flash(u'Error en el campo %s - %s' % (getattr(form, field).label.text, error))


@APP.route('/addnewuser', methods=['POST', 'GET'])
@login_required
def add_new_user():
	"""function for add new user"""
	form = UserZeroForm(secret_key='James Bond')
	if request.method == 'POST':
		if not form.validate():
			flash_errors(form)
			return render_template('adduser.html', form=form)
		else:
			data_user = {}
			data_user['name'] = form.name.data
			data_user['last1'] = form.lastname1.data
			data_user['last2'] = form.lastname2.data
			data_user['city'] = form.city.data
			data_user['state'] = form.state.data
			data_user['country'] = form.country.data
			data_user['email'] = form.email.data
			data_user['phone'] = form.phone.data
			data_user['password'] = "1234abcd"
			data_user['username'] = MAPPTOBD.create_username(elimina_tildes(data_user['name'].lower()), elimina_tildes(data_user['last1'].lower()), elimina_tildes(data_user['last2'].lower()), 0)
			data_user['status'] = 1
			data_user['admin'] = 0
			if MAPPTOBD.store_new_user(data_user):
				flash('Usuario agregado correctamente.', 'success')
				return redirect(url_for('add_new_user'))
			else:
				#mensaje de que hubo un problema
				flash('Error al ingresar el nuevo usuario.', 'message')
				return render_template('adduser.html', form=form)
	else:
		return render_template('adduser.html', form=form)


@APP.route('/QRCODE', methods=['GET'])
@login_required
def get_qrcode():
	"""function for get a qr code"""
	data = request.args.get('data', '')
	return send_file(QRCODE(data, mode='raw'), mimetype='image/png')


@APP.route('/addnewphone', methods=['POST', 'GET'])
@login_required
def add_new_phone():
	"""function for add new phone"""
	form = PhoneForm(secret_key='James Bond')
	list_user = []
	for user in MAPPTOBD.get_list_user(0):
		list_user.append(user['NAME_USER']+" "+user['LASTNAME1_USER']+" "+user['LASTNAME2_USER'])
	if request.method == 'POST':
		if form.validate():
			#get data from form
			data_phone = {}
			data_phone['model'] = form.model.data
			data_phone['imei'] = form.imei.data
			data_phone['active'] = 1 #si registramos, entonces es porque esta activo
			if MAPPTOBD.store_new_phone(data_phone):
				print request.form.get('users')
				flash(u'Dispositivo móvil agregado correctamente.', 'success')
				if MAPPTOBD.relate_user_phone(request.form.get('users'), data_phone['imei']):
					return redirect(url_for('allow_phone', imei=data_phone['imei']))
				else:
					flash(u'Error al relacionar al usuario con el dispositivo móvil.', 'message')
					return render_template('addphone.html', form=form, list_user=list_user)
				#return render_template('allowphone.html')
			else:
				flash(u'Error al ingresar el nuevo dispositivo móvil.', 'message')
				return render_template('addphone.html', form=form, list_user=list_user)
		else:
			flash_errors(form)
			return render_template('addphone.html', form=form, list_user=list_user)
	else:
		return render_template('addphone.html', form=form, list_user=list_user)

@APP.route('/allowphone', methods=['POST', 'GET'])
@login_required
def allow_phone():
	"""function for allow new phone"""
	alphabet = string.ascii_letters + string.digits
	token = ''.join(random.choice(alphabet) for i in range(125))
	MAPPTOBD.store_token(token)
	if request.method == 'POST':
		if MAPPTOBD.check_allow_phone(request.args.get('imei')):
			flash(u'Teléfono aceptado por el sistema.', 'message')
			return redirect(url_for('main'))
		else:
			flash(u'Teléfono no aceptado por el sistema, vuelva a intentar.')
			return render_template('allowphone.html', toke=token)
	else:
		MAPPTOBD.relate_phone_token(token, request.args.get('imei')) #aca es necesario verificar que se haga el cruce de informacion entre el phone y el token creado
		return render_template('allowphone.html', token=token)

@APP.route('/missions', methods=['GET'])
@login_required
@nocache
def missions():
	"""function for control missions view"""
	active_missions = None
	active_missions = MAPPTOBD.get_active_missions(current_user.get_data().get('username'))
	return render_template('missions.html', active_missions=active_missions)

@APP.route('/createmission', methods=['POST', 'GET'])
@login_required
def create_mission():
	"""function for create new mission"""
	form = MissionForm(secret_key='James Bond')
	list_maps = []
	list_id_maps = []
	for element in MAPPTOBD.get_maps():
		list_maps.append(element['NAME_MAP'])
		list_id_maps.append(element['ID_MAP'])
	if request.method == 'POST':
		if form.validate():
			if MAPPTOBD.check_name_mission(request.form.get('maps')):
				flash(u'Error en el nombre de la misión, recuerde que este debe ser único.', 'message')
				return render_template('createmission.html', form=form, list_maps=list_maps)
			else:
				data_mission = {}
				data_mission['name_mission'] = form.name_mission.data
				data_mission['description'] = form.description_mission.data
				data_mission['id_map'] = list_id_maps[list_maps.index(request.form.get('maps'))]
				if MAPPTOBD.store_new_mission(data_mission):
					if MAPPTOBD.relate_user_mission(current_user.get_data().get('username'), data_mission['name_mission']):
						flash(u'Misión creada correctamente.', 'success')
						return redirect(url_for('missions'))
						#redirigir a la plantilla de la misión
					else:
						flash(u'Error al crear la misión, intente nuevamente.', 'message')
						return render_template('createmission.html', form=form, list_maps=list_maps)
				else:
					flash(u'Error al crear la misión, intente nuevamente.', 'message')
					return render_template('createmission.html', form=form, list_maps=list_maps)
		else:
			flash_errors(form)
			return render_template('createmission.html', form=form, list_maps=list_maps)
	else:
		return render_template('createmission.html', form=form, list_maps=list_maps)


@APP.route('/mission/<string:name_mission>', methods=['GET'])
@login_required
def mission(name_mission):
	"""function for mission"""
	data_mission = MAPPTOBD.get_data_mission(name_mission)
	data_mission['NAME_MAP'] = MAPPTOBD.get_name_map(data_mission['ID_MAP_MISSION'])['NAME_MAP']
	data_mission['LIST_PARTICIPANT'] = MAPPTOBD.get_participant_of_mission(name_mission)
	if data_mission:
		return render_template('mission.html', data_mission=data_mission)
	else:
		flash(u'Error al cargar los datos de la misión, porfavor reintente más tarde.', 'message')
		return redirect(url_for('missions'))

@APP.route('/mission/<string:name_mission>/deactivate', methods=['GET'])
@login_required
def deactivate(name_mission):
	"""function for deactivate a mission"""
	if MAPPTOBD.deactivate_mission(name_mission):
		if MAPPTOBD.release_user_mission(name_mission):
			flash(u'Misión desactivada correctamente.', 'success')
			return redirect(url_for('missions'))
		else:
			flash(u'Error al liberar a los usuarios de la misión actual.', 'message')
			return redirect(url_for('missions'))
	else:
		flash(u'Error al desactivar la misión.', 'message')
		return redirect(url_for('missions'))

@APP.route('/mission/<string:name_mission>/activate', methods=['GET'])
@login_required
def activate(name_mission):
	"""function for activate a mission"""
	if MAPPTOBD.activate_mission(name_mission):
		flash(u'Misión activada correctamente.', 'success')
		return redirect(url_for('missions'))
	else:
		flash(u'Error al desactivar la misión.', 'message')
		return redirect(url_for('missions'))

@APP.route('/mission/<string:name_mission>/delete', methods=['GET'])
@login_required
def delete_mission(name_mission):
	"""function for delete a mission"""
	if MAPPTOBD.delete_mission(name_mission, current_user.get_data().get('username')):
		if MAPPTOBD.release_user_mission(name_mission):
			flash(u'Misión borrada correctamente.', 'success')
			return redirect(url_for('missions'))
		else:
			flash(u'Error al liberar a los usuarios de la misión actual.', 'message')
			return redirect(url_for('missions'))
	else:
		flash(u'Error al borrar la misión solicitada.', 'message')
		return redirect(url_for('missions'))

@APP.route('/mission/<string:name_mission>/addparticipant', methods=['POST', 'GET'])
@login_required
def add_participant_mission(name_mission):
	"""function for add a user to mission"""
	list_participant = MAPPTOBD.get_participant_free()
	if request.method == 'POST':
		id_mission = MAPPTOBD.get_id_mission(name_mission)['ID_MISSION']
		if MAPPTOBD.set_active_mission_user(id_mission, request.form.getlist('participante')):
			return redirect(url_for('missions'))
		else:
			flash(u'Error al asignar la misión a los participantes, vuelva a intentar.', 'message')
			return render_template('addparticipant.html', list_participant=list_participant)
	else:
		return render_template('addparticipant.html', list_participant=list_participant)

#SOCKET FOR ACTIVE MISSIONS
@SOCKETIO.on('joined', namespace='/start')
def joined(message):
	"""Sent by clients when they enter a room.
	A status message is broadcast to all people in the room."""
	room = session.get('room')
	join_room(room)
	emit('status', {'msg': session.get('name') + ' ha entrado al chat'}, room=room)


@SOCKETIO.on('join', namespace='/start')
def join(roomate, name):
	"""Sent by clients when they enter a room.
	A status message is broadcast to all people in the room."""
	room = roomate
	join_room(room)
	emit('status', {'msg': name + ' ha entrado al chat'}, room=room)


@SOCKETIO.on('text', namespace='/start')
def text(message):
	"""Sent by a client when the user entered a new message.
	The message is sent to all people in the room."""
	room = session.get('room')
	emit('message', {'msg': session.get('name') + ' # ' + message['msg']}, room=room)

@SOCKETIO.on('textMobile', namespace='/start')
def text(message, roomName):
	"""Sent by a client when the user entered a new message.
	The message is sent to all people in the room."""
	emit('message', {'msg': message['msg']}, room=roomName)


@SOCKETIO.on('left', namespace='/start')
def left(message):
	"""Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
	room = session.get('room')
	leave_room(room)
	emit('status', {'msg': session.get('name') + ' ha dejado el chat'}, room=room)


@APP.route('/start')
@login_required
def start_mission():
	""" function for start a new mission """
	#se obtienen los valores para la room y el name del usuario
	#la sala de chat se llama igual que la mision
	#el nombre de usario en el chat, es el mismo que se utiliza en la plataforma
	name = current_user.get_data().get('username')
	room = request.args.get('name_mission')
	session['name'] = name
	session['room'] = room
	list_participant = MAPPTOBD.get_participant_of_mission(room)
	return render_template('startmission.html', name=name, room=room, list_participant=list_participant)

@APP.route('/setsession')
def set_session():
	""" function for set session on specific user """
	try:
		session['name'] = request.args.get('name')
		session['room'] = request.args.get('room')
		return "true"
	except ValueError:
		return "false"

@LOGIN_MANAGER.user_loader
def load_user(id_user):
	""" function for load """
	return STORED_USERS.get(int(id_user))


if __name__ == '__main__':
	SOCKETIO.run(APP, host='0.0.0.0', port=4000)
