from flask import Flask, redirect, url_for, request, render_template
from flask_bootstrap import Bootstrap
from flask_admin import Admin
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_mail import Mail
from flask_moment import Moment 
from flask_sqlalchemy import SQLAlchemy
import flask_login as login
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)


# Create customized model view class
class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

### Visualización de la vista Admin ###
class HomeAdminView(AdminIndexView):
    def is_accessible(self):
        return current_user.has_role('admin')
    def inaccessible_callback(self, name, **kwargs):
        return render_template('404.html')


admin = Admin(app, 'Hera', template_mode='bootstrap4', url='/', index_view=HomeAdminView(name='Admin'), base_template='admin/my_master.html')
migrate = Migrate(app, db)
moment = Moment(app)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'Por favor, inicia sesión para acceder a esta página.'
bootstrap = Bootstrap(app)
mail = Mail(app)


from project import routes, models, forms, errors


