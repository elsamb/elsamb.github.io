from flask import render_template, flash, redirect, url_for, request
from project import app, db, admin
from project.forms import *
from project.models import *
from project.email import send_password_reset_email
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
import psycopg2
from project.decorator import admin_required

@app.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.commit()

#View function
@app.route('/') 
@app.route('/home') #/ y /home están asociadas a la misma página así
def home(): 
	return render_template('home.html', title='Home - Hera Technology')

#View function
@app.route('/sugerencias') 
def sugerencias(): 
	return render_template('sugerencias.html', title='Sugerencias')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated: 
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Nombre de usuario o contraseña inválidos')
			return redirect(url_for('login'))
		login_user(user, remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('home')
		return redirect(next_page)
	return render_template('login.html', title='Iniciar sesión', form=form)

## Social 
@app.route('/social', methods=['GET', 'POST'])
@login_required
def social():
	form = PostForm()
	if form.validate_on_submit():
		post = Post(body=form.post.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('¡Post publicado!')
		return redirect(url_for('social'))
	page = request.args.get('page', 1, type=int)
	posts = current_user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('social', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('social', page=posts.prev_num) \
		if posts.has_prev else None
	return render_template('social.html', title='Social', form=form, posts=posts.items,
							next_url=next_url, prev_url=prev_url)

# Explorar
@app.route('/explore')
@login_required
def explore():
	page = request.args.get('page', 1, type=int)
	#users_ex = Users.query.all()
	posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('explore', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('explore', page=posts.prev_num) \
		if posts.has_prev else None
	return render_template('social.html', title = 'Explorar', posts=posts.items,
							next_url=next_url, prev_url=prev_url)

#Perfil del usuario
@app.route('/user/<username>')
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type=int)
	posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('user', username=user.username, page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('user', username=user.username, page=posts.prev_num) \
		if posts.has_prev else None
	form = EmptyForm()
	return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url, form=form)

# Logout
@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('home'))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('admin_view'))
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(username=form.username.data, email=form.email.data)
		user.set_password(form.password.data)

		db.session.add(user)
		db.session.commit()
		flash('¡Enhorabuena, eres un usuario registrado!')
		return redirect(url_for('login'))
	return render_template('register.html', title='Registro', form=form)

# Request password reset
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user: 
			send_password_reset_email(user)
		flash('Comprueba tu correo para las instrucciones y crear una nueva contraseña')
		return redirect(url_for('login'))
	return render_template('reset_password_request.html', title='Resetea tu contraseña', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	user = User.verify_reset_password_token(token)
	if not user: 
		return redirect(url_for('home'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		user.set_password(form.password.data)
		db.session.commit()
		flash('Has cambiado tu contraseña.')
		return redirect(url_for('login'))
	return render_template('reset_password.html', form=form)

# Edit profile
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Se han guardado los cambios.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Editar Perfil',
                           form=form)

##  Follow
@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
	form = EmptyForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=username).first()
		if user is None:
			flash('User {} not found.'.format(username))
			return redirect(url_for('social'))
		if user == current_user:
			flash('You cannot follow yourself!')
			return redirect(url_for('user', username=username))
		current_user.follow(user)
		db.session.commit()
		flash('You are following {}!'.format(username))
		return redirect(url_for('user', username=username))
	else:
		return redirect(url_for('social'))

## Unfollow
@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
	form = EmptyForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=username).first()
		if user is None:
			flash('User {} not found.'.format(username))
			return redirect(url_for('social'))
		if user == current_user:
			flash('You cannot unfollow yourself!')
			return redirect(url_for('user', username=username))
		current_user.unfollow(user)
		db.session.commit()
		flash('You are not following {}.'.format(username))
		return redirect(url_for('user', username=username))
	else:
		return redirect(url_for('social'))


## Admin 
@app.route('/admin/')
@app.route('/admin')
@login_required
@admin_required
def admin():
	return render_template('admin.html')

	
@app.route('/familiayamigos')
def familiayamigos(): 
	conn = psycopg2.connect(host = "db",
							port = "5432",
							dbname="hello_flask_dev",
							#dbname="hello_flask_prod",
    						user="hello_flask",
    						password="hello_flask")
	# you must create a Cursor object. It will let
	#  you execute all the queries you need
	cur = conn.cursor()
	# Use all the SQL you like
	sqlite_select_query= """SELECT * from Articles WHERE category='Familia y amigos' ORDER BY DATE(updated_at)"""
	cur.execute(sqlite_select_query)
	data = cur.fetchall()


	articles_query = """SELECT * from Articles WHERE category='Familia y amigos' AND subcategory='Artículo' ORDER BY DATE(updated_at)"""
	cur.execute(articles_query)
	art = cur.fetchall()

	video_query = """SELECT * from Articles WHERE category='Familia y amigos' AND subcategory='Vídeo' ORDER BY DATE(updated_at)"""
	cur.execute(video_query)
	vid = cur.fetchall()

	news_query = """SELECT * from Articles WHERE category='Familia y amigos' AND subcategory='Noticia' ORDER BY DATE(updated_at)"""
	cur.execute(news_query)
	new = cur.fetchall()


	return render_template('familiayamigos.html', title="Familia y Amigos", data=data, art=art, vid=vid, new=new)


@app.route('/alimentacion')
def alimentacion(): 
	conn = psycopg2.connect(host = "db",
							port = "5432",
							dbname="hello_flask_dev",
							#dbname="hello_flask_prod",
    						user="hello_flask",
    						password="hello_flask")
	# you must create a Cursor object. It will let
	#  you execute all the queries you need
	cur = conn.cursor()
	# Use all the SQL you like
	sqlite_select_query= """SELECT * from Articles WHERE category='Alimentación' ORDER BY DATE(updated_at)"""
	cur.execute(sqlite_select_query)
	data = cur.fetchall()

	articles_query = """SELECT * from Articles WHERE category='Alimentación' AND subcategory='Artículo' ORDER BY DATE(updated_at)"""
	cur.execute(articles_query)
	art = cur.fetchall()

	video_query = """SELECT * from Articles WHERE category='Alimentación' AND subcategory='Vídeo' ORDER BY DATE(updated_at)"""
	cur.execute(video_query)
	vid = cur.fetchall()

	news_query = """SELECT * from Articles WHERE category='Alimentación' AND subcategory='Noticia' ORDER BY DATE(updated_at)"""
	cur.execute(news_query)
	new = cur.fetchall()
	return render_template('alimentacion.html', title="Alimentación", data=data, art=art, vid=vid, new=new)

@app.route('/autocuidado')
def autocuidado(): 
	conn = psycopg2.connect(host = "db",
							port = "5432",
							dbname="hello_flask_dev",
							#dbname="hello_flask_prod",
    						user="hello_flask",
    						password="hello_flask")
	# you must create a Cursor object. It will let
	#  you execute all the queries you need
	cur = conn.cursor()
	# Use all the SQL you like
	sqlite_select_query= """SELECT * from Articles WHERE category='Autocuidado' ORDER BY DATE(updated_at)"""
	cur.execute(sqlite_select_query)
	data = cur.fetchall()


	articles_query = """SELECT * from Articles WHERE category='Autocuidado' AND subcategory='Artículo' ORDER BY DATE(updated_at)"""
	cur.execute(articles_query)
	art = cur.fetchall()

	video_query = """SELECT * from Articles WHERE category='Autocuidado' AND subcategory='Vídeo' ORDER BY DATE(updated_at)"""
	cur.execute(video_query)
	vid = cur.fetchall()

	news_query = """SELECT * from Articles WHERE category='Autocuidado' AND subcategory='Noticia' ORDER BY DATE(updated_at)"""
	cur.execute(news_query)
	new = cur.fetchall()
	return render_template('autocuidado.html', title="Autocuidado", data=data, art=art, vid=vid, new=new)


@app.route('/deporte')
def deporte(): 
	conn = psycopg2.connect(host = "db", 
							port = "5432",
							dbname="hello_flask_dev",
							#dbname="hello_flask_prod",
							user="hello_flask",
							password="hello_flask")
	# you must create a Cursor object. It will let
	#  you execute all the queries you need
	cur = conn.cursor()
	# Use all the SQL you like
	sqlite_select_query= """SELECT * from Articles WHERE category='Deporte' ORDER BY DATE(updated_at)"""
	cur.execute(sqlite_select_query)
	data = cur.fetchall()

	articles_query = """SELECT * from Articles WHERE category='Deporte' AND subcategory='Artículo' ORDER BY DATE(updated_at)"""
	cur.execute(articles_query)
	art = cur.fetchall()

	video_query = """SELECT * from Articles WHERE category='Deporte' AND subcategory='Vídeo' ORDER BY DATE(updated_at)"""
	cur.execute(video_query)
	vid = cur.fetchall()

	news_query = """SELECT * from Articles WHERE category='Deporte' AND subcategory='Noticia' ORDER BY DATE(updated_at)"""
	cur.execute(news_query)
	new = cur.fetchall()
	return render_template('deporte.html', title="Deporte", data=data, art=art, vid=vid, new=new)
	#return render_template('deporte.html', title="Deporte")

@app.route('/relajacion')
def relajacion(): 
	conn = psycopg2.connect(host = "db",
							port = "5432",
							dbname="hello_flask_dev",
							#dbname="hello_flask_prod",
    						user="hello_flask",
    						password="hello_flask")
	# you must create a Cursor object. It will let
	#  you execute all the queries you need
	cur = conn.cursor()
	# Use all the SQL you like
	sqlite_select_query= """SELECT * from Articles WHERE category='Relajación' ORDER BY DATE(updated_at)"""
	cur.execute(sqlite_select_query)
	data = cur.fetchall()

	articles_query = """SELECT * from Articles WHERE category='Relajación' AND subcategory='Artículo' ORDER BY DATE(updated_at)"""
	cur.execute(articles_query)
	art = cur.fetchall()

	video_query = """SELECT * from Articles WHERE category='Relajación' AND subcategory='Vídeo' ORDER BY DATE(updated_at)"""
	cur.execute(video_query)
	vid = cur.fetchall()

	news_query = """SELECT * from Articles WHERE category='Relajación' AND subcategory='Noticia' ORDER BY DATE(updated_at)"""
	cur.execute(news_query)
	new = cur.fetchall()
	return render_template('relajacion.html', title="Relajación", data=data, art=art, vid=vid, new=new)


@app.route('/mood', methods=['GET', 'POST'])
@login_required
def mood(): 
	form = AnimoForm()
	form2 = SuenoForm()
	form3 = EnergyForm()
	form4 = DiaryForm()
	if form.validate_on_submit():
		animo_user = Animo(animo=form.animo.data, author=current_user)
		db.session.add(animo_user)
		db.session.commit()
		flash('¡Ánimo guardado!')

	if form2.validate_on_submit():
		sueno_user = Sueno(horas=form2.horas.data, calidad=form2.calidad.data, horas_cama=form2.horas_cama.data, suenos=form2.suenos.data, author=current_user)
		db.session.add(sueno_user)
		db.session.commit()
		flash('¡Sueño guardado!')

	if form3.validate_on_submit():
		energy_user = Energia(energia=form3.energia.data, author=current_user)
		db.session.add(energy_user)
		db.session.commit()
		flash('¡Energía guardada!')

	if form4.validate_on_submit():
		diary_user = Diary(diary=form4.diary.data, author=current_user)
		db.session.add(diary_user)
		db.session.commit()
		flash('¡Diario guardado!')

	return render_template('animo.html', title="Ánimo", form=form, form2=form2, form3=form3, form4=form4)

@app.route('/recursos')
def recursos():
	return render_template('recursos.html')

@app.route('/dashboard')
@login_required
def dashboard():
	return render_template('dashboard.html')

@app.route('/dashboard-animo')
@login_required
def dashboardanimo():
	animos = current_user.animo
	print(animos)
	return render_template('dashboard-animo.html', animos=animos.items)


@app.route('/dashboard-medicos')
@login_required
def dashboardmedicos():
	users=User.query.all()
	return render_template('dashboard-medicos.html', users=users)
