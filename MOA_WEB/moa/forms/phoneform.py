# -*- coding: utf-8 -*-

from wtforms import TextField, SubmitField, SelectField, validators, ValidationError
from flask_wtf import FlaskForm

def luhn_checksum(card_number):
	def digits_of(n):
		return [int(d) for d in str(n)]
	digits = digits_of(card_number)
	odd_digits = digits[-1::-2]
	even_digits = digits[-2::-2]
	checksum = 0
	checksum += sum(odd_digits)
	for d in even_digits:
		checksum += sum(digits_of(d*2))
	return checksum % 10

def is_luhn_valid(form, field):
	if luhn_checksum(field.data) != 0:
		raise ValidationError(u'número inválido. Recuerde que presionando *#06# en el dispositivo móvil puede comprabar el número de IMEI correcto.')
		#return self.luhn_checksum(card_number) == 0

class PhoneForm(FlaskForm):
	model = TextField(u'Modelo', [validators.Required(u'Porfavor ingrese un modelo del teléfono.')])
	imei = TextField(u'Número IMEI', [validators.Required(u'Porfavor ingrese un número IMEI válido'), validators.Length(message=u'El IMEI debe tener 15 dígitos.', min=15, max=15), is_luhn_valid])
	submit = SubmitField('Guardar')