# -*- coding: utf-8 -*-

from wtforms import TextField, SubmitField, validators
from flask_wtf import FlaskForm


class MissionForm(FlaskForm):
	name_mission = TextField(u'Nombre de la misión', [validators.Required(u'Porfavor ingrese un nombre para la misión.')])
	description_mission = TextField(u'Descripción de la misión', [validators.Required(u'Porfavor ingrese una descripción de la misión.'), validators.Length(message=u'Debe ingresar mínimo 10 caracteres y máximo 250.', min=10, max=250)])
	create = SubmitField('Crear')