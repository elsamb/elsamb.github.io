from flask.cli import FlaskGroup 
from project import app, db
from project.models import *
import logging, os 
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_security import Security, SQLAlchemyUserDatastore
from flask_mail import Mail
import psycopg2
from project.posts.blueprint import content

cli = FlaskGroup(app)

app.register_blueprint(content, url_prefix='/content')
# localhost:5000/content

@cli.command("create_db")
def create_db():
	db.create_all()
	db.session.commit()

@cli.command("seed_db")
def seed_db():
	db.session.add(User(username='Michael', email="michael@mherman.org", password_hash='prueba'))
	db.session.commit()



if __name__ == "__main__":
	cli()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post} 


if not app.debug: 
	if app.config['MAIL_SERVER']:
		auth = None
		if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
			auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
		secure = None
		if app.config['MAIL_USE_TLS']:
			secure = ()
		mail_handler = SMTPHandler(
			mailhost = (app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
			fromaddr = 'no-reply@' + app.config['MAIL_SERVER'],
			toaddrs = app.config['ADMINS'], subject = 'Fallo agregador', 
			credentials = auth, secure=secure)
		mail_handler.setLevel(logging.ERROR)
		app.logger.addHandler(mail_handler)
		if not os.path.exists('logs'):
			os.mkdir('logs')
			file_handler = RotatingFileHandler('logs/agregador.log', maxBytes=10240,
				backupCount=10)
			file_handler.setFormatter(logging.Formatter(
				'%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
			file_handler.setLevel(logging.INFO)
			app.logger.addHandler(file_handler)

			app.logger.setLevel(logging.INFO)
			app.logger.info('Agregador startup')


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
