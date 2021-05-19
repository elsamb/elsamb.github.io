from flask import Blueprint 
from flask import render_template
from project.models import Articles

content = Blueprint('content', __name__, template_folder='templates')

#localhost:5000/content
@content.route('/')
def articles_list():
	articles = Articles.query.all()
	return render_template('post/posts.html', articles = articles)

# localhost:5000/content/first-post
@content.route('/<slug>')
def article_detail(slug):
	article = Articles.query.filter(Articles.slug==slug).first()
	return render_template('post/post_detail.html', article=article)