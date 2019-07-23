# -*- coding: utf-8 -*-
import pymysql.cursors
import socket
import time
import datetime


class MapeoBD:

	#esto se puede parametrizar mas, con el host, user, password y db
	def __init__(self, host, user, password, db):
		#ciclo para poder reintentar todas las veces que sea necesario o que requiera el usuario
		while True:
			try:
				#conexion hacia la base de datos
				print "Conectando a la DB..."
				self.connection = pymysql.connect(host=host, user=user, password=password, db=db, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
				print "Conectado a la DB!"
			
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
	
	def get_profile_image(self, name):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `PIC_USER` FROM `USER` WHERE `NAME_USER`=%s"
				cursor.execute(sql, (name, ))
				result = cursor.fetchone()
				return result
		except Exception as e:
			raise e	

	def check_username(self, username):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `ID_USER` FROM `USER` WHERE `USERNAME_USER`=%s"
				cursor.execute(sql, (username, ))
				#obtiene un resultado, para obtener todos cursor.fetchall()
				#result = cursor.fetchone()
				result = cursor.fetchall()
				#si encontramos algo
				if result:
					return False
				#si no encontramos algo
				else:
					return True
		except Exception as e:
			print "Oooops, no podemos comprobar el nombre de usuario."

	def create_username(self, name, last1, last2, i):
		username = name + "." + last1
		if self.check_username(username):
			return username
		else:
			username = name + "." + last1 + last2[i]
			if self.check_username(username):
				return username
			else:
				self.create_username(name, last1, last2, i+1)

	def store_new_user(self, data):
		try:
			with self.connection.cursor() as cursor:
				sql = "INSERT INTO `USER`(`NAME_USER`, `LASTNAME1_USER`, `LASTNAME2_USER`, `CITY_USER`, `STATE_USER`, `COUNTRY_USER`, `EMAIL_USER`, `PHONE_USER`, `USERNAME_USER`, `USERPASS_USER`, `ADMIN_USER`, `STATUS_USER`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,(SELECT PASSWORD(%s)),%s,%s)"
				cursor.execute(sql, (data['name'], data['last1'], data['last2'], data['city'], data['state'], data['country'], data['email'], data['phone'], data['username'], data['password'], data['admin'], data['status']))
				self.connection.commit()
				return True
		except Exception as e:
			print "Oooops, no podemos guardar el nuevo usuario en la base de datos."
			return False

	def store_new_phone(self, data):
		try:
			with self.connection.cursor() as cursor:
				sql = "INSERT INTO `PHONE`(`MODEL_PHONE`, `IMEI_PHONE`, `ACTIVE_PHONE`, `ALLOWED_PHONE`) VALUES (%s, %s, %s, %s)"
				cursor.execute(sql, (data['model'], data['imei'], data['active'], 0))
				self.connection.commit()
				return True
		except Exception as e:
			print "Oooops, no podemos guardar el nuevo dispositivo movil en la base de datos."
			return False

	def login_user(self, username, password):
		with self.connection.cursor() as cursor:
			sql = "SELECT `ID_USER`, `NAME_USER`, `LASTNAME1_USER`, `LASTNAME2_USER`, `PIC_USER`, `CITY_USER`, `STATE_USER`, `COUNTRY_USER`, `EMAIL_USER`, `PHONE_USER`, `USERNAME_USER`, `ADMIN_USER`, `STATUS_USER`, `LAST_CONNECTION_USER`, `IP_LAST_CONNECTION_USER` FROM `USER` WHERE `USERNAME_USER`=%s AND `USERPASS_USER`=(SELECT PASSWORD(%s))"
			cursor.execute(sql, (username, password, ))
			#obtiene un resultado, para obtener todos cursor.fetchall()
			result = cursor.fetchone()
			#si result tiene algo, entonces es true
			if result and result['ADMIN_USER'] != 0 and result['STATUS_USER'] == 1: #revisar si es mejor poner distinto o el igual a algo, pensando en posibles instusiones al sistema
				#actualizamos la ip, por ende el timestamp de la ultima conexion
				with self.connection.cursor() as cursor:
					sql_update = "UPDATE `USER` SET `IP_LAST_CONNECTION_USER`=%s WHERE `USERNAME_USER`= %s"
					cursor.execute(sql_update, (str(socket.gethostbyname(socket.gethostname())), username, ))
					self.connection.commit()
				return result
			else:
				return None

	def store_token(self, token):
		try:
			ts = time.time()
			timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
			with self.connection.cursor() as cursor:
				sql = "INSERT INTO `TOKENIZER`(`TOKEN`, `DATETIME_CREATED_TOKEN`) VALUES (%s, %s)"
				cursor.execute(sql, (token, timestamp))
				self.connection.commit()
				return True
		except Exception as e:
			print "Oooops, no podemos guardar el token en la base de datos."
			return False

	def get_list_user(self, code):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `NAME_USER`, `LASTNAME1_USER`, `LASTNAME2_USER` FROM `USER` WHERE `ADMIN_USER`= %s"
				cursor.execute(sql, (code, ))
				result = cursor.fetchall()
				return result
		except Exception as e:
			print "Oooops, no podemos obtener la lista de usuarios desde la base de datos."
			return None

	#para obtener el nombre, apellido1 y apellido2 desde el select(dropdown) hay que hacer un split entre los espacios
	def relate_user_phone(self, data_user, data_phone):
		try:
			name_user = data_user.split(" ")
			with self.connection.cursor() as cursor:
				sql_user = "SELECT `ID_USER` FROM `USER` WHERE `NAME_USER`=%s AND `LASTNAME1_USER`=%s AND `LASTNAME2_USER`=%s"
				cursor.execute(sql_user, (name_user[0], name_user[1], name_user[2]))
				result_user = cursor.fetchone()
				sql_phone = "SELECT `ID_PHONE` FROM `PHONE` WHERE `IMEI_PHONE`=%s"
				cursor.execute(sql_phone, (data_phone))
				result_phone = cursor.fetchone()
				sql_final = "INSERT INTO `USER_REGISTER_PHONE`(`ID_USER`, `ID_PHONE`) VALUES (%s, %s)"
				cursor.execute(sql_final, (result_user['ID_USER'], result_phone['ID_PHONE']))
				self.connection.commit()
				return True
		except Exception as e:
			print u"Oooops, no podemos relacionar al usuario con el dispositivo móvil en la base de datos."
			return False

	def relate_phone_token(self, token, imei):
		try:
			with self.connection.cursor() as cursor:
				sql_token = "SELECT `ID_TOKEN` FROM `TOKENIZER` WHERE `TOKEN`=%s"
				cursor.execute(sql_token, (token))
				result_token = cursor.fetchone()
				sql_imei = "SELECT `ID_PHONE` FROM `PHONE` WHERE `IMEI_PHONE`=%s"
				cursor.execute(sql_imei, (imei))
				result_imei = cursor.fetchone()
				sql_final = "INSERT INTO `PHONE_HAS_TOKEN`(`ID_PHONE`, `ID_TOKEN`) VALUES (%s, %s)"
				cursor.execute(sql_final, (result_imei['ID_PHONE'], result_token['ID_TOKEN']))
				self.connection.commit()
				return True
		except Exception as e:
			print u"No hemos podido relacionar el dispositivo móvil con el token creado."
			return False
		
		
	def check_allow_phone(self, imei):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `ALLOWED_PHONE` FROM `PHONE` WHERE `IMEI_PHONE`=%s"
				cursor.execute(sql, (imei))
				result = cursor.fetchone()
				if result['ALLOWED_PHONE'] == 1:
					return True
				else:
					return False
		except Exception as e:
			print u"No hemos podido consultar sobre el permiso del dispositivo móvil solicitado."
			return False


	def get_active_missions(self, username):
		try:
			list_data_mission = []
			with self.connection.cursor() as cursor:
				sql = "SELECT `ID_MISSION` FROM `USER_CREATE_MISSION` WHERE `ID_USER`=(SELECT `ID_USER` FROM `USER` WHERE `USERNAME_USER`=%s)"
				cursor.execute(sql, (username))
				result = cursor.fetchall()
				for element in result:
					sql_consult = "SELECT `NAME_MISSION`, `DESCRIPTION_MISSION`, `DATE_CREATED_MISSION`, `DATE_START_MISSION`, `DATE_END_MISSION`, `IS_ACTIVE_MISSION`, `ID_MAP_MISSION` FROM `MISSION` WHERE `ID_MISSION`=%s"
					cursor.execute(sql_consult, (element['ID_MISSION']))
					list_data_mission.append(cursor.fetchone())
				return list_data_mission

		except Exception as e:
			print u"No podemos obtener las misiones activas del usuario."
			return None


	def get_maps(self):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `ID_MAP`,`NAME_MAP` FROM `MAP`"
				cursor.execute(sql, ())
				result = cursor.fetchall()
				return result
		except Exception as e:
			print u"No podemos obtener los mapas creados."
			return None


	def check_name_mission(self, name_map):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `ID_MISSION` FROM `MISSION` WHERE `NAME_MISSION`=%s"
				cursor.execute(sql, (name_map))
				if cursor.fetchall():
					return True
				else:
					return False
		except Exception as e:
			print u"No podemos comprobar si existe el nombre de la misión."
			return True


	def relate_user_mission(self, username, name_mission):
		try:
			with self.connection.cursor() as cursor:
				sql_user = "SELECT `ID_USER` FROM `USER` WHERE `USERNAME_USER`=%s"
				cursor.execute(sql_user, (username))
				result_user = cursor.fetchone()
				sql_mission = "SELECT `ID_MISSION` FROM `MISSION` WHERE `NAME_MISSION`=%s"
				cursor.execute(sql_mission, (name_mission))
				result_mission = cursor.fetchone()
				sql_update = "INSERT INTO `USER_CREATE_MISSION`(`ID_USER`, `ID_MISSION`) VALUES (%s, %s)"
				cursor.execute(sql_update, (result_user['ID_USER'], result_mission['ID_MISSION']))
				self.connection.commit()
				return True
		except Exception as e:
			print u"No podemos crear la relación entre el usuario y la misión creada."
			return False


	def store_new_mission(self, data_mission):
		try:
			ts = time.time()
			timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
			with self.connection.cursor() as cursor:
				sql =  "INSERT INTO `MISSION`(`NAME_MISSION`, `DESCRIPTION_MISSION`, `DATE_CREATED_MISSION`, `ID_MAP_MISSION`) VALUES (%s, %s, %s, %s)"
				cursor.execute(sql, (data_mission['name_mission'], data_mission['description'], timestamp, data_mission['id_map']))
				self.connection.commit()
				return True
		except Exception as e:
			print u"No podemos guardar la nueva misión en la base de datos."
			return False


	def get_data_mission(self, name_mission):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT SQL_NO_CACHE `NAME_MISSION`, `DESCRIPTION_MISSION`, `DATE_CREATED_MISSION`, `DATE_START_MISSION`, `DATE_END_MISSION`, `IS_ACTIVE_MISSION`, `ID_MAP_MISSION` FROM `MISSION` WHERE `NAME_MISSION`=%s"
				cursor.execute(sql, (name_mission))
				result = cursor.fetchone()
				#esta es importante para ver los cambios en la base de datos, si se hace un cambio directo en la base de datos, sin pasar por la plataforma
				self.connection.commit()
				return result
		except Exception as e:
			print u"No podemos obtener los datos de la misión desde la base de datos."
			return None


	def get_id_mission(self, name_mission):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `ID_MISSION` FROM `MISSION` WHERE `NAME_MISSION`=%s"
				cursor.execute(sql, (name_mission))
				result = cursor.fetchone()
				return result
		except Exception as e:
			print u"No podemos obtener el ID de la misión."
			return None


	def get_name_map(self, id_map):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `NAME_MAP` FROM `MAP` WHERE `ID_MAP`=%s"
				cursor.execute(sql, (id_map))
				result = cursor.fetchone()
				return result
		except Exception as e:
			print u"No podemos obtener el nombre del mapa a partir del identificador en la base de datos."
			return None


	def deactivate_mission(self, name_mission):
		try:
			with self.connection.cursor() as cursor:
				sql = "UPDATE `MISSION` SET `IS_ACTIVE_MISSION`=%s WHERE `NAME_MISSION`=%s"
				cursor.execute(sql, (0, name_mission))
				self.connection.commit()
				return True
		except Exception as e:
			print u"No hemos podido actualizar el estado de la misión en la base de datos."
			return False


	def activate_mission(self, name_mission):
		try:
			with self.connection.cursor() as cursor:
				sql = "UPDATE `MISSION` SET `IS_ACTIVE_MISSION`=%s WHERE `NAME_MISSION`=%s"
				cursor.execute(sql, (1, name_mission))
				self.connection.commit()
				return True
		except Exception as e:
			print u"No hemos podido actualizar el estado de la misión en la base de datos."
			return False


	def delete_mission(self, name_mission, username):
		try:
			with self.connection.cursor() as cursor:
				sql_id_mission = "SELECT `ID_MISSION` FROM `MISSION` WHERE `NAME_MISSION`=%s"
				cursor.execute(sql_id_mission, (name_mission))
				result_id_mission = cursor.fetchone()
				sql_id_user = "SELECT `ID_USER` FROM `USER` WHERE `USERNAME_USER`=%s"
				cursor.execute(sql_id_user, username)
				result_id_user = cursor.fetchone()
				sql_delete = "DELETE FROM `USER_CREATE_MISSION` WHERE `ID_USER`=%s AND `ID_MISSION`=%s"
				cursor.execute(sql_delete, (result_id_user['ID_USER'], result_id_mission['ID_MISSION']))
				sql = "DELETE FROM `MISSION` WHERE `NAME_MISSION`=%s"
				cursor.execute(sql, (name_mission))
				self.connection.commit()
				return True
		except Exception as e:
			print u"No podemos eliminar la misión solicitada."
			return False


	def get_participant_free2(self):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `ID_USER`, `NAME_USER`, `LASTNAME1_USER`, `LASTNAME2_USER`, `CITY_USER`, `EMAIL_USER`, `USERNAME_USER` FROM `USER` WHERE `ADMIN_USER`=0 AND `STATUS_USER`=1"
				cursor.execute(sql)
				result = cursor.fetchall()
				sql_participant = "SELECT DISTINCT `ID_USER` FROM `USER_PARTICIPATE_MISSION` WHERE 1"
				cursor.execute(sql_participant)
				result_participant = cursor.fetchall()
				for free_participant in result_participant:
					for participant in result:
						if free_participant['ID_USER'] == participant['ID_USER']:
							del participant
				return result			
		except Exception as e:
			print u"No hemos podido obtener los participantes libres desde la base de datos."
			return None


	def get_participant_free(self):
		try:
			with self.connection.cursor() as cursor:
				sql = "SELECT `ID_USER`, `NAME_USER`, `LASTNAME1_USER`, `LASTNAME2_USER`, `CITY_USER`, `EMAIL_USER`, `USERNAME_USER` FROM `USER` WHERE `ADMIN_USER`=0 AND `STATUS_USER`=1 AND `ID_MISSION_USER`=-1"
				cursor.execute(sql)
				result = cursor.fetchall()
				return result
		except Exception as e:
			print u"No hemos podido obtener los participantes libres desde la base de datos."
			return None


	def get_participant_of_mission(self, name_mission):
		try:
			with self.connection.cursor() as cursor:
				sql_id_mission = "SELECT `ID_MISSION` FROM `MISSION` WHERE `NAME_MISSION`=%s"
				cursor.execute(sql_id_mission, (name_mission))
				result = cursor.fetchone()
				sql_participant = "SELECT `ID_USER`, `USERNAME_USER`, `NAME_USER`, `LASTNAME1_USER`, `LASTNAME2_USER` FROM `USER` WHERE `ID_MISSION_USER`=%s"
				cursor.execute(sql_participant, (result['ID_MISSION']))
				result_participant = cursor.fetchall()
				return result_participant
		except Exception as e:
			print u"No hemos podido obtener los participantes de una misión."
			return None


	def release_user_mission(self, name_mission):
		try:
			participant_mission = self.get_participant_of_mission(name_mission)
			with self.connection.cursor() as cursor:
				for participant in participant_mission:
					sql = "UPDATE `USER` SET `ID_MISSION_USER`=-1 WHERE `ID_USER`=%s"
					cursor.execute(sql, (participant['ID_USER']))
				return True
		except Exception as e:
			print u"No hemos podido liberar a los usuarios de la misión."
			return False


	def set_active_mission_user(self, id_mision, list_user):
		try:
			with self.connection.cursor() as cursor:
				for user in list_user:
					sql = "UPDATE `USER` SET `ID_MISSION_USER`=%s WHERE `ID_USER`=%s "
					cursor.execute(sql, (id_mision, str(user)))
					self.connection.commit()
				return True
		except Exception as e:
			print u"No hemos podido asignar una misión a los usuarios en la base de datos."
			return False

