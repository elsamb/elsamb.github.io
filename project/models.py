from project import app, db, login, admin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from flask_security import UserMixin, RoleMixin
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, BaseView, expose
from wtforms.fields import SelectField, TextAreaField
from datetime import datetime
from time import time
import re
from hashlib import md5
import jwt
from flask import request, redirect, url_for
import urllib.parse as urlparse

### Followers ###
followers = db.Table('followers', 
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')), 
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))

### Roles ### 
roles_users = db.Table('roles_users', 
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')))

### Tags ###
articles_tags = db.Table('articles_tags', 
    db.Column('articles_id', db.Integer, db.ForeignKey('articles.id_article')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')   
    active = db.Column(db.Boolean(), default=True, nullable = False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    animo = db.relationship('Animo', backref='author', lazy='dynamic')
    energia = db.relationship('Energia', backref='author', lazy='dynamic')
    sueno = db.relationship('Sueno', backref='author', lazy='dynamic')
    diary = db.relationship('Diary', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    # Password setter
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login integration
    def get_id(self):
        return str(self.id)

    def is_active(self): 
        return True

    def is_authenticated(self): 
        print('Comando')
        return True

    #Avatar
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest,size)

    #Followers
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0
        
    def followed_posts(self): 
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())


    # Send email when the user forgets the password
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in}, 
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

def slugify(s):
    pattern = r'[^\w+]'
    return re.sub(pattern, '-', s)


class Articles(db.Model):
    __searchable__ = []
    id_article = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    url = db.Column(db.String(), nullable=False)
    author = db.Column(db.String(), nullable=False)
    text = db.Column(db.String(250))
    category = db.Column(db.String())
    subcategory = db.Column(db.String())
    image = db.Column(db.String())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(140), unique=True)
    tags = db.relationship('Tag', secondary=articles_tags, backref=db.backref('articles'), lazy='dynamic')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.generate_slug()


    def __repr__(self):
       return f'<Título: {self.title}>'

    def get_url(self):
        return self.url

    def generate_slug(self):
        if self.title:
            self.slug = slugify(self.title)
        else:
            self.slug = str(int(time()))    

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    slug = db.Column(db.String(64), unique=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slug =slugify(self.title)

    def __repr__(self):
        return f'{self.name}'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Animo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animo = db.Column(db.String(), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Animo {}>'.format(self.animo)
        
    def __init__(self, animo, timestamp, user_id):
       #self.id_article = id_article
       self.animo = animo
       self.timestamp = timestamp

class Energia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    energia = db.Column(db.String(), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Energia {}>'.format(self.energia)

class Sueno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horas = db.Column(db.String(), nullable=False)
    calidad = db.Column(db.String())
    horas_cama = db.Column(db.String())
    suenos = db.Column(db.String())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Diary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    diary = db.Column(db.String(), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

### Visualización de la vista Admin ###
class AdminMixin:
    def is_accessible(self):
        return #current_user.has_role('admin')
    def inaccessible_callback(self, name, **kwargs):
        return #redirect(url_for('security.login', next=request.url))

class HomeAdminView(AdminIndexView):
    def is_accessible(self):
        return current_user.has_role('admin')
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next=request.url))

class UserView(ModelView):
    # Show only name and email columns in list view
    column_list = ('id', 'username', 'email')
    column_searchable_list = ['email', 'username']
    column_exclude_list = ['password']
    #form_excluded_columns = column_exclude_list
    column_details_exclude_list = column_exclude_list
    column_filters = column_searchable_list
    edit_modal = True
    create_modal = True    
    can_export = True
    can_view_details = True
    details_modal = True
    pass


class ArticlesView(ModelView):
    # Admin manager for MyModel
    column_list = ('title', 'updated_at', 'author', 'category', 'subcategory')
    column_searchable_list = ['title', 'updated_at', 'author', 'category', 'subcategory']
    column_filters = column_searchable_list
    form_overrides = dict(category=SelectField, subcategory=SelectField, text=TextAreaField)
    form_args = dict(
        # Pass the choices to the `SelectField`
        category=dict(
            choices=[('Deporte', 'Deporte'), ('Familia y amigos', 'Familia y amigos'), ('Relajación', 'Relajación'), ('Alimentación', 'Alimentación'), ('Autocuidado', 'Autocuidado')]), 

        subcategory=dict(
            choices=[('Artículo', 'Artículo'), ('Noticia', 'Noticia'), ('Vídeo', 'Vídeo')])
        )
    column_default_sort = ('updated_at', True)

    pass


class AnimoView(ModelView):
    pass
class EnergyView(ModelView):
    pass
class SuenoView(ModelView):
    pass
class DiaryView(ModelView):
    pass

class BaseModelView(ModelView):
    def getinfo(self):
        return "this is another model"

admin.add_view(UserView(User, db.session, name="Pacientes"))
admin.add_view(ArticlesView(Articles, db.session, name="Sugerencias"))
admin.add_view(AnimoView(Animo, db.session))
admin.add_view(EnergyView(Energia, db.session))
admin.add_view(SuenoView(Sueno, db.session))
admin.add_view(DiaryView(Diary, db.session))
admin.add_view(BaseModelView(Tag, db.session, name= u'label management'))