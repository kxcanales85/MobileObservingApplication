import os

from flask import Flask, jsonify, abort, make_response, request
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_httpauth import HTTPBasicAuth

from util.maptobd import MapToBD

app = Flask(__name__, static_url_path="")
api = Api(app)
auth = HTTPBasicAuth()

#enviroment config db - LOCAL
app.config['HOST_DB'] = 'localhost'
#app.config['USER_DB'] = os.environ.get('USER_DB')
#app.config['PASSWORD_DB'] = os.environ.get('PASSWORD_DB')
app.config['USER_DB'] = 'bustamante'
app.config['PASSWORD_DB'] = 'usach1234'
app.config['NAME_DB'] = 'DB_MOA'

#enviroment config db - HEROKU
#app.config['HOST_DB'] = 'us-cdbr-iron-east-05.cleardb.net'
#app.config['USER_DB'] = os.environ.get('USER_DB')
#app.config['PASSWORD_DB'] = os.environ.get('PASSWORD_DB')
#app.config['USER_DB'] = 'b94fbfba34b49e'
#app.config['PASSWORD_DB'] = '947de613'
#app.config['NAME_DB'] = 'heroku_80e3a8d0952a407'

#inicializacion del mapeo a la base de datos
maptobd = MapToBD(app.config['HOST_DB'], app.config['USER_DB'], app.config['PASSWORD_DB'], app.config['NAME_DB'])

@auth.verify_password
def get_password(username, password):
    if maptobd.check_user_pass(username, password):
        return True
    return False

@app.route('/')
@auth.login_required
def index():
    return "Hello, %s!" % auth.username()

@app.route('/check_status_phone/<string:token>', methods=['GET'])
def check_status_phone(token):
	if maptobd.check_status_phone(token):
		#el telefono esta aceptado en el sistema
		return "true"
	else:
		#el telefono no esta aceptado en el sistema
		return "false"

@app.route('/check_status_token/<string:token>', methods=['GET'])
def check_status_token(token):
	if maptobd.check_validity_token(token):
		#el token es valido
		return "true"
	else:
		#el token no es valido
		return "false"

@app.route('/invalidate_token/<string:token>', methods=['GET'])
def invalidate_token(token):
	if maptobd.invalidate_token(token):
		#el token se ha invalidado correctamente
		return "done"
	else:
		#el token no se ha podido invalidar
		return "not done"

@app.route('/check_token_phone/', methods=['GET'])
def check_token_phone():
	token = request.args.get('token')
	imei = request.args.get('imei')
	if maptobd.check_relation_token_imei(token, imei):
		#existe la relacion en la base de datos
		return "true"
	else:
		#no existe la relacion en la base de datos
		return "false"

@app.route('/doall/', methods=['GET'])
def do_all():
	token = request.args.get('token')
	imei = request.args.get('imei')
	if maptobd.check_and_do_all(token, imei):
		#se realizo todo de forma correcta
		return 'true'
	else:
		#no se pudo realizar
		return 'false'

@app.route('/getmission/<string:username>', methods=['GET'])
def get_mission(username):
	#si get_active_mission retorna algo distinto de nulo
	result = maptobd.get_active_mission(username)
	if result != None:
		#retornamos el id de la mision
		return result['NAME_MISSION']
	else:
		return 'false'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)