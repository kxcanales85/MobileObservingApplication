# -*- coding: utf-8 -*-
import pymysql.cursors
import socket
import time
import datetime


class MapToBD:

	#que hace: funcion que actua como el contructor de la clase, intenta establecer la conexion hacia la base de datos
	#entradas: el host de la base datos, el nombre de usuario, la contraseña de usuario y el nombre de la base de datos
	#salidas: establecimiento de la conexion a la base de datos
	def __init__(self, host, user, password, db):
		#ciclo para poder reintentar todas las veces que sea necesario o que requiera el usuario
		while True:
			try:
				#conexion hacia la base de datos
				self.connection = pymysql.connect(host=host, user=user, password=password, db=db, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
			
			except Exception as e:
				print "Oooops, no podemos conectarnos a la base de datos."
				dec_input = raw_input("Desea reintentar [Y(es) / N(o)]: ")
				#si responde si, entonces reintentamos
				if dec_input == 'Y' or dec_input == 'Yes' or dec_input == 'yes' or dec_input == 'y' or dec_input == 'YES':
					continue
				#si responde no, entonces iniciamos sin base de datos
				elif dec_input == 'N' or dec_input == 'No' or dec_input == 'no' or dec_input == 'n' or dec_input == 'NO':
					print "Base de datos no conectada. Si desea conectarla, deberá reiniciar el servidor."
					break
				#si escribe cualquier otra cosa, entonces preguntamos de nuevo
				else:
					continue
			#una vez que salimos del try, entonces podemos romper el while
			break

	#que hace: verifica que la password ingresada por el usuario corresponda con la password que se tiene almacenada en la db
	#entradas: el username y la password
	#salidas: un boolean para comprobar el exito o el fallo de la comprobacion
	def check_user_pass(self, username, password):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `USERNAME_USER`, `ADMIN_USER`, `STATUS_USER` FROM `USER` WHERE `USERNAME_USER`=%s AND `USERPASS_USER`=(SELECT PASSWORD(%s))"
				cursor.execute(sql, (username, password, ))
				result = cursor.fetchone()
				#si result tiene algo, entonces es true
				if result:
					#si el user es admin y esta activo, entonces puede entrar
					if result['ADMIN_USER'] == 0 and result['STATUS_USER'] == 1: #revisar si es mejor poner distinto o el igual a algo, pensando en posibles instusiones al sistema
					#actualizamos la ip, por ende el timestamp de la ultima conexion
						with self.connection.cursor() as cursor:
							sql_update = "UPDATE `USER` SET `IP_LAST_CONNECTION_USER`=%s WHERE `USERNAME_USER`= %s"
							cursor.execute(sql_update, (str(socket.gethostbyname(socket.gethostname())), username, ))
							self.connection.commit()
						return True
				else:
					#no es admin o no esta activo, por lo que no puede ingresar el portal de administracion
					return False
		except Exception as e:
			print "Oooops, no podemos comprobar el nombre de usuario o la pass."


	#que hace: comprueba la existencia del nombre de usuario en la base de datos
	#entradas: el nombre de usuario
	#salidas: un boolean con la existencia o no en la base de datos del nombre de usuario
	def check_username(self, username):
		try:
			with self.connection.cursor() as cursor:
				#obtenemos el id del usuario
				sql = "SELECT `ID_USER` FROM `USER` WHERE `USERNAME_USER`=%s"
				cursor.execute(sql, (username, ))
				result = cursor.fetchall()
				#si encontramos algo
				if result:
					return False
				#si no encontramos algo
				else:
					return True
		except Exception as e:
			print "Oooops, no podemos comprobar el nombre de usuario."


	#que hace: crea el nombre de usuario a partir del hombre y los apellidos del usuario
	#entradas: el nombre, el apellido1 y el apellido2
	#salidas: un string con el nombre de usuario creado, debe ser nombre.apellido1
	def create_username(self, name, last1, last2, i):
		#comenzamos con la base del username, nombre.apellido1
		username = name + "." + last1
		#si este nombre de usuario no existe
		if self.check_username(username):
			#lo podemos ocupar
			return username
		#si existe
		else:
			#comenzamos a ocupar letras del segundo apellido
			username = name + "." + last1 + last2[i]
			#si no existe este username
			if self.check_username(username):
				#lo podemos ocupar
				return username
			#si existe este username
			else:
				#hacemos un llamado recursivo aumentando en una letra mas del segundo apellido
				self.create_username(name, last1, last2, i+1)


	#que hace: comprueba el estado del dispositivo movil en la plataforma
	#entradas: el imei
	#salidas: un boolean con el estado dentro del dispositivo movil en la plataforma
	def check_status_phone(self, imei):
		#try:
		with self.connection.cursor() as cursor:
			sql = "SELECT `ALLOWED_PHONE` FROM `PHONE` WHERE `IMEI_PHONE`=%s"
			cursor.execute(sql, (imei))
			result = cursor.fetchone()
			#si encontramos algo
			if result:
				#si está activo
				if result['ALLOWED_PHONE'] == 1:
					return False
				#si no está activo
				else:
					return True
			#si no encontramos algo
			else:
				return False
		#except Exception as e:
		#	print u"Oooops, no podemos comprobar el estatus del teléfono."
		#	return False


	#que hace: invalida el token creado
	#entradas: el token
	#salidas: un boolean con la correcta o incorrecta invalidacion del token
	def invalidate_token(self, token):
		try:
			#obtenemos el datetime actual del servidor
			ts = time.time()
			timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
			with self.connection.cursor() as cursor:
				#hacemos un update del token, se setea como usado y el datetime de cuando fue usado
				sql = "UPDATE `TOKENIZER` SET `USED_TOKEN`=%s, `DATETIME_USED_TOKEN`=%s WHERE `TOKEN`=%s"
				cursor.execute(sql, (1, timestamp, token))
				self.connection.commit()
				return True

		except Exception as e:
			print u"No hemos podido invalidar el token solicitado."
			return False
	

	#que hace: acepta al dispositivo movil en la plataforma
	#entradas: el numero imei del dispositivo movil
	#salidas: un boolean con la aceptacion o no del dispositivo movil
	def allowed_phone(self, imei):
		try:
			with self.connection.cursor() as cursor:
				#hacemos un update al campo que acepta al dispositivo en la plataforma
				sql = "UPDATE `PHONE` SET `ALLOWED_PHONE`=1 WHERE `IMEI_PHONE`=%s"
				cursor.execute(sql, (imei))
				self.connection.commit()
				return True
		
		except Exception as e:
			print u"No hemos podido aceptar al dispositivo móvil en la plataforma."
			return False


	#que hace: comprueba la validez del token creado
	#entradas: el token
	#salidas: un boolean con la validez o invalidez del token
	def check_validity_token(self, token):
		#try:
		with self.connection.cursor() as cursor:
			#obtenemos el campo used_token desde la tabla tokenizer
			sql = "SELECT `USED_TOKEN` FROM `TOKENIZER` WHERE `TOKEN`=%s"
			cursor.execute(sql, (token))
			result = cursor.fetchone()
			#si el token no esta usado
			if result['USED_TOKEN'] == 0:
				return True
			#si esta usado
			else:
				return False
		
		#except Exception as e:
		#	print u"No hemos podido revisar la validéz del token solicitado."
		#	return False


	#que hace: comprueba la relacion entre el dispositivo movil y el token creado previmente
	#entradas: el token y el imei del dispositivo movil
	#salidas: un boolean con la correcta o incorrecta relacion 
	def check_relation_token_imei(self, token, imei):
		try:
			with self.connection.cursor() as cursor:
				#obtenemos el id del token
				sql_token = "SELECT `ID_TOKEN` FROM `TOKENIZER` WHERE `TOKEN`=%s"
				cursor.execute(sql_token, (token))
				result_token = cursor.fetchone()
				#obtenemos el id del dispositivo movil
				sql_imei = "SELECT `ID_PHONE` FROM `PHONE` WHERE `IMEI_PHONE`=%s"
				cursor.execute(sql_imei, (imei))
				result_imei = cursor.fetchone()
				#obtenemos el id de la tabla que relaciona el token con el imei
				sql_final = "SELECT `ID_PHT` FROM `PHONE_HAS_TOKEN` WHERE `ID_PHONE`=%s AND `ID_TOKEN`=%s"
				cursor.execute(sql_final, (result_imei['ID_PHONE'], result_token['ID_TOKEN']))
				result_final = cursor.fetchall()
				#si obtenemos algo
				if result_final:
					#retornamos que la relacion es valida
					return True
				#si no obtenemos algo
				else:
					#entonces retornamos que la relacion no es valida
					return False
		
		except Exception as e:
			print u"No hemos podido revisar la relación entre el token y el IMEI."
			return False
		


	#que hace: realiza todo el flujo necesario para comprobar la validez de la peticion desde el dispositivo movil
	#entradas: el token y el emei obtenido desde el dispositivo movil
	#salidas: el dispositivo aceptado o no en la plataforma, y de ser positiva la aceptacion, la invalidez del token creado
	def check_and_do_all(self, token, imei):
		try:
			#si no está aceptado el dispositivo movil en la app
			if self.check_status_phone(imei):
				#si el token es valido
				if self.check_validity_token(token):
					#si la relacion token-celular es válida
					if self.check_relation_token_imei(token, imei):
						#si podemos aceptar al celular en la plataforma
						if self.allowed_phone(imei):
							#si podemos invalidar el 
							if self.invalidate_token(token):
								return True
							else:
								print "No hemos podido invalidar el token."
								return False
						else:
							print u"No se ha podido aceptar el dispositivo móvil en la plataform."
							return False
					else:
						print u"No hemos podido comprobar la relación entre el token y el dispositivo móvil."
						return False
				else:
					print u"No hemos podido comprobar la validéz del token."
					return False
			else:
				print u"No hemos podido comprobar el estado en la plataforma, del dispositivo móvil."
				return False

		except Exception as e:
			print u"Errores en permitir al dispositivo móvil en la plataforma"
			return False


	#que hace: obtiene la mision activa del usuario
	#entradas: el nombre del usuario
	#salidas: el nombre de la mision si es que tiene, si no, retorna nulo
	def get_active_mission(self, username):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `ID_MISSION_USER` FROM `USER` WHERE `USERNAME_USER`=%s"
				cursor.execute(sql, username)
				result = cursor.fetchone()
				sql_name_mission = "SELECT `NAME_MISSION` FROM `MISSION` WHERE `ID_MISSION`=%s"
				cursor.execute(sql_name_mission, (result['ID_MISSION_USER']))
				name_mission = cursor.fetchone()
				if name_mission:
					return name_mission
				else:
					return None
					
		except Exception as e:
			print u"No hemos podido obtener la misión activa del usuario."
			return None