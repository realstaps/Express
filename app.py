from flask import Flask, redirect, url_for, render_template , request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user,current_user,login_required
from auth.OAuthAll import OAuthSignIn
from werkzeug import secure_filename
import os
from datetime import datetime
import time
import json

app = Flask(__name__)

UPLOAD_FOLDER = '/static/posts/uploads'
ALLOWED_EXTENSIONS = set(['jpg','png','jpeg'])

app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '232991410370871',
        'secret': 'ca0f688420f86264b9003708c48050db'
    },
    'twitter': {
        'id': 'VJnPtET7hBLVfJ4WQl4ImaBTa',
        'secret': 'sgQxTgzyOPqdS2t7g9iH79vhgYfmyZGTjIS2ujmzk1W2hn6Y7S'
    }
}

db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'index'

class User(UserMixin,db.Model):
	id = db.Column(db.Integer,primary_key=True)
	social_id = db.Column(db.String(64),nullable=False,unique=True)
	nickname = db.Column(db.String(64),nullable=False)
	name = db.Column(db.String(64),nullable=False)
	email = db.Column(db.String(64),nullable=True)
	picture = db.Column(db.Text,nullable=True)
	posts = db.relationship('Post', backref='user_id' , lazy='dynamic')
	comments = db.relationship('Comment', backref='user_id' , lazy='dynamic')
	replies = db.relationship('Reply', backref='user_id' , lazy='dynamic')

	def to_json(self):
		dic = {}
		dic['id'] = self.id
		dic['social_id'] = self.social_id
		dic['nickname'] = self.nickname
		dic['name'] = self.name
		dic['email'] = self.email
		dic['picture'] = self.picture
		
		return json.dumps(dic)




class Post(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	title = db.Column(db.String(255),nullable=False)
	body = db.Column(db.Text,nullable=False)
	picture = db.Column(db.Text,nullable=True)
	date = db.Column(db.DateTime,nullable=True)
	author = db.Column(db.Integer,db.ForeignKey('user.id'))
	comments = db.relationship('Comment', backref='post_id' , lazy='dynamic')

	def to_json(self):
		dic = {}
		dic['id'] = self.id
		dic['title'] = self.title
		dic['body'] = self.body
		dic['picture'] = self.picture
		dic['date'] = self.date.strftime("%A %d, %m %Y %H:%M")
		dic['author'] = self.author

		return json.dumps(dic)

class Comment(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	comment = db.Column(db.Text,nullable=False)
	date = db.Column(db.DateTime,nullable=True)
	post = db.Column(db.Integer,db.ForeignKey('post.id'))
	author = db.Column(db.Integer,db.ForeignKey('user.id'))
	replies = db.relationship('Reply', backref='comment_id', lazy='dynamic')

	def to_json(self):
		dic = {}
		dic['id'] = self.id
		dic['comment'] = self.comment
		dic['post'] = self.post
		dic['date'] = self.date.strftime("%A %d, %m %Y %H:%M")
		dic['author'] = self.author

		return json.dumps(dic)


class Reply(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	reply = db.Column(db.Text,nullable=False)
	date = db.Column(db.DateTime,nullable=True)
	author = db.Column(db.Integer,db.ForeignKey('user.id'))
	comment = db.Column(db.Integer,db.ForeignKey('comment.id'))


	

def is_allowed(filename):
	return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

@app.before_first_request
def before_first_request():
	db.create_all()


@lm.user_loader
def load_user(id):
	return User.query.get(int(id))

@app.route("/")
def index():
	if current_user.is_authenticated:
		return redirect(url_for('homepage'))
	return render_template('main.html')

@app.route("/feed")
@login_required
def homepage():
	posts = Post.query.limit(10).all()
	return render_template('index.html',posts=posts)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
	if not current_user.is_anonymous:
		return redirect(url_for('index'))
	oauth = OAuthSignIn.get_provider(provider)
	return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
	if not current_user.is_anonymous:
		return redirect(url_for('index'))
	oauth = OAuthSignIn.get_provider(provider)

	social_id,username, email , picture , name = oauth.callback()

	if social_id is None:
		flash('Authentification failed.')
		return redirect(url_for('index'))
	user = User.query.filter_by(social_id=social_id).first()
	if not user:
		user = User(social_id=social_id,nickname=username,email=email,name=name,picture=picture)

		db.session.add(user)
		db.session.commit()
	login_user(user,True)

	return redirect(url_for('homepage'))

@app.route('/posts/add/',methods=["POST"])
@login_required
def add_post():
	if request.form.has_key('title') :
		photo = request.files.get('photo',None)
		filename = None
		directory = os.getcwd()
		dir_photo = os.getcwd()

		if photo and is_allowed(photo.filename):
			try:
				directory = app.config['UPLOAD_FOLDER']+"/"+str(current_user.id)+"/"
				dir_photo = os.getcwd()+directory.replace('/','\\')
				os.makedirs(dir_photo)
			except OSError:
					pass
			filename = secure_filename(photo.filename).split('.')
			filename[0] = filename[0]+str(time.time()).replace('.',"")[-6:-1]
			dir_photo = dir_photo+".".join(filename)
			filename = directory+".".join(filename)
			photo.save(dir_photo)

		post = Post(title = request.form['title'] , body = request.form['body'] , author = current_user.id,picture = filename,date = datetime.utcnow())
		db.session.add(post)
		db.session.commit()
	return redirect(url_for('homepage'))

@app.route('/posts/<int:id>')
def get_post(id):
	post = Post.query.get(id)
	list_comment = []

	if post is not None:
		comments = post.comments.all()
		if comments is not None:
			for comment in comments:
				list_comment.append(comment.to_json())
		post.comment = json.dumps(list_comment)
		post = post.to_json()

	return post


@app.route('/comments/add/',methods=['POST'])
def add_comment():
	post = request.form.get('post',None)
	com = request.form.get('comment',None)
	comment = "Error"+str(post)+com

	if post is not None and com is not None and current_user.is_authenticated:
		comment = Comment(date = datetime.utcnow(),comment=com,post=post,author=current_user.id);
		db.session.add(comment)
		db.session.commit()

		user = User.query.get(comment.author)
		comment.author =  user.to_json()
		comment = comment.to_json()

	return comment

if __name__ == '__main__':
	app.run(debug=True)

