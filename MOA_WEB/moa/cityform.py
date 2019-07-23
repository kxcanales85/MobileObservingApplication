from flask.ext.wtf import Form, SelectField


class CityForm(Form):
    state = SelectField(u'', choices=())
    city = SelectField(u'', choices=())