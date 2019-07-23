# -*- coding: utf-8 -*-

from wtforms import TextField, SubmitField, SelectField, validators, ValidationError
from flask_wtf import FlaskForm

class UserZeroForm(FlaskForm):
	name = TextField('Nombre', [validators.Required(u'Porfavor ingrese un nombre.')])
	lastname1 = TextField('Primer apellido', [validators.Required(u'Porfavor ingrese el primer apellido.')])
	lastname2 = TextField('Segundo apellido', [validators.Required(u'Porfavor ingrese el segundo apellido.')])
	city = TextField('Ciudad', [validators.Required(u'Porfavor ingrese una ciudad de residencia.')])
	state = TextField(u'Región', [validators.Required(u'Porfavor ingrese una región.')])
	country = TextField(u'País', [validators.Required(u'Porfavor ingrese el país.')])
	email = TextField(u'Correo electrónico', [validators.Required(u'Porfavor ingrese el correo electrónico.'), validators.Email('Porfavor ingrese un dirección de correo electrónico válida.')])
	phone = TextField(u'Número de teléfono', [validators.Required(u'Porfavor ingrese un número de teléfono.'), validators.Length(message='El formato debe ser +569+número.', min=12, max=12)])
	submit = SubmitField('Guardar')