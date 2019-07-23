from flask_login import UserMixin
#from flask_sqlalchemy import SQLAlchemy

class User(UserMixin):

	def __init__(self, data):
		self.id_user = data['ID_USER']
		self.name = data['NAME_USER']
		self.lastname1 = data['LASTNAME1_USER']
		self.lastname2 = data['LASTNAME2_USER']
		self.picture = data['PIC_USER']
		self.city = data['CITY_USER']
		self.state = data['STATE_USER']
		self.country = data['COUNTRY_USER']
		self.email = data['EMAIL_USER']
		self.phone = data['PHONE_USER']
		self.username = data['USERNAME_USER']
		self.admin = data['ADMIN_USER']
		self.lastconnection = data['LAST_CONNECTION_USER']
		self.lastip = data['IP_LAST_CONNECTION_USER']


	"""def __init__(self, id_user, name, lastname1, lastname2, picture, city, state, country, email, phone, username, admin, lastconnection, lastip):
		self.id_user = id_user
		self.name = name
		self.lastname1 = lastname1
		self.lastname2 = lastname2
		self.picture = picture
		self.city = city
		self.state = state
		self.country = country
		self.email = email
		self.phone = phone
		self.username = username
		self.admin = admin
		self.lastconnection = lastconnection
		self.lastip = lastip """

	def is_authenticated(self):
		return self.authenticated

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.id_user)

	def get_data(self):
		data = {}
		data["id_user"] = self.id_user
		data["name"] = self.name
		data["lastname1"] = self.lastname1
		data["lastname2"] = self.lastname2
		data["picture"] = self.picture
		data["city"] = self.city
		data["state"] = self.state
		data["country"] = self.country
		data["email"] = self.email
		data["phone"] = self.phone
		data["username"] = self.username
		data["picture"] = self.picture
		data["username"] = self.username
		data["admin"] = self.admin
		data["lastconnection"] = self.lastconnection
		data["lastip"] = self.lastip
		return data

	def __repr__(self):
		return '<User %r>' % (self.id_user)