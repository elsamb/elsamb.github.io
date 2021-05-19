from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, RadioField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from project.models import User


class LoginForm(FlaskForm):
	username = StringField('Nombre de usuario', validators=[DataRequired()])
	password = PasswordField('Contraseña', validators=[DataRequired()])
	remember_me = BooleanField('Recuérdame')
	submit = SubmitField('Iniciar sesión')


class RegistrationForm(FlaskForm):
	username = StringField('Nombre de usuario', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Contraseña', validators=[DataRequired()])
	password2 = PasswordField(
		'Repite la contraseña', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Registro')

	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user is not None:
			raise ValidationError('Este nombre de usuario ya existe, usa uno diferente por favor.')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is not None:
			raise ValidationError('Este email ya ha sido utilizado, usa uno diferente, por favor.')

class EditProfileForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	about_me = TextAreaField('Sobre mí', validators=[Length(min=0, max=140)])
	submit = SubmitField('Submit')

	def __init__(self, original_username, *args, **kwargs):
		super(EditProfileForm, self).__init__(*args, **kwargs)
		self.original_username = original_username

	def validate_username(self, username):
		if username.data != self.original_username:
			user = User.query.filter_by(username=self.username.data).first()
			if user is not None: 
				raise ValidationError('Este nombre de usuario ya existe, usa uno diferente, por favor.')

class ResetPasswordRequestForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Nueva contraseña')

class ResetPasswordForm(FlaskForm):
	password = PasswordField('Contraseña', validators=[DataRequired()])
	password2 = PasswordField('Repite la contraseña', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Restablecer contraseña')

class EmptyForm(FlaskForm):
	submit = SubmitField('Enviar')

class PostForm(FlaskForm):
	post = TextAreaField('Escribe algo...', validators=[DataRequired(), Length(min=1, max=140)])
	submit = SubmitField('Enviar')

class AnimoForm(FlaskForm): 
	animo = RadioField('Ánimo', choices=[  ('5', '¡Genial!'), ('4', 'Bien'), ('3', 'Regular'), ('2', 'Mal'),('1', 'Fatal')])
	submit = SubmitField('Guardar')

class SuenoForm(FlaskForm): 
	horas = StringField('Horas')
	calidad = SelectField('Calidad del sueño', choices=[('1', 'Muy mal'), ('2', 'Mal'), ('3', 'Regular'), ('4', 'Bien'), ('5', 'Muy bien')])
	horas_cama = StringField('Horas en la cama')
	suenos = TextAreaField('Sueños')
	submit = SubmitField('Guardar')


class EnergyForm(FlaskForm): 
	energia = SelectField('Energía', choices=[('5', '¡A tope!'), ('4', 'Bastante'), ('3', 'Normal'), ('2', 'Poca'), ('1', 'Muy poca')])
	submit = SubmitField('Guardar')

class ActivityForm(FlaskForm): 
	activity = SelectMultipleField('Activities', choices=[('5', '¡A tope!'), ('4', 'Bastante'), ('3', 'Normal'), ('2', 'Poca'), ('1', 'Muy poca')])
	submit = SubmitField('Guardar')

class DiaryForm(FlaskForm): 
	diary = TextAreaField('¡Escribe lo que quieras!')
	submit = SubmitField('Guardar')