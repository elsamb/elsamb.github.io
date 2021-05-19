import os


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
	SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") 
	SQLALCHEMY_TRACK_MODIFICATIONS = False 
	WHOOSH_BASE='whoosh'
	MAIL_SERVER = 'smtp.gmail.com' #'os.environ.get('MAIL_SERVER')'
	MAIL_PORT = 587 #int(os.environ.get('MAIL_PORT') or 25)
	MAIL_USE_TLS = True #os.environ.get('MAIL_USE_TLS') is not None 
	MAIL_USERNAME = 'elsasecundaria21' #os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = 'cuentasec#21' #os.environ.get('MAIL_PASSWORD')
	ADMINS = ['elsasecundaria21@gmail.com']
	POSTS_PER_PAGE = 10
	LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
	DEBUG = False
	TESTING = False
	CSRF_ENABLED = True


class ProductionConfig(Config):
	DEBUG = False

class StagingConfig(Config):
	DEVELOPMENT = True 
	DEBUG = True

class TestingConfig(Config):
	TESTING = True 