import werkzeug
from flask import Flask, render_template, request, redirect, url_for, flash, abort
import smtplib
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from forms import CreatePostForm, CreateUserForm, LoginForm, CreateCommentForm, CreateAdminForm
import datetime
from flask_ckeditor import CKEditorField, CKEditor
from flask_login import LoginManager, login_user, UserMixin, logout_user, login_required, current_user
from functools import wraps
from sqlalchemy.orm import relationship
from flask_gravatar import Gravatar
import os
from dotenv import load_dotenv

app = Flask(__name__)
login_manager = LoginManager()
Bootstrap(app)
login_manager.init_app(app)
ckeditor = CKEditor(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)
app.app_context().push()
load_dotenv("upgraded_blog\.env")
key = os.getenv("app_password")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL",  "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = key
app.config['SESSION_COOKIE_SECURE'] = False

db = SQLAlchemy(app)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))






class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="comments_on_post")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="commenter")
    is_admin = db.Column(db.Boolean)

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    comment = db.Column(db.Text, nullable=False)
    commenter_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    commenter = relationship("User", back_populates="comments")
    comments_on_post = relationship("BlogPost", back_populates="comments")

db.create_all()

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.is_admin == False:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function




@app.route('/')
def index():
    all_posts = db.session.query(BlogPost).all()
    return render_template('index.html', blog_posts = all_posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']
        my_email = os.getenv("email")
        email_password = os.getenv('password')
        connection = smtplib.SMTP('smtp.gmail.com')
        connection.starttls()
        connection.login(user=my_email, password= email_password)
        connection.sendmail(from_addr=my_email, to_addrs=my_email,
                            msg=f"Subject: New Enquiry \n\n Your user: {name} \n email: {email} \n phone: {phone} \n said: {message} ")

        return render_template('contact.html', normal_header= False)
    return render_template('contact.html', normal_header=True)


@app.route('/post/<id>', methods=["GET", "POST"])
def post(id):
    chosen_post = BlogPost.query.filter_by(id = id).first()
    form = CreateCommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
        else:
            new_comment = Comment(
                comment = request.form['body'],
                commenter = current_user,
                post_id = id
            )
            db.session.add(new_comment)
            db.session.commit()
    return render_template('post.html', post = chosen_post, current_user = current_user, form = form)


@app.route('/makepost', methods=["GET", "POST"])
@admin_only
def make_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(title=request.form['title'],
                            subtitle=request.form['subtitle'],
                            date=datetime.date.today().strftime("%B %d, %Y"),
                            body=request.form['body'],
                            author= current_user,
                            img_url=request.form['img_url']


                            )
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template("make-post.html", form = form)

@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Log on credentials are incorrect, please try again")
            return redirect(url_for('login'))

        else:
            pwhash = user.password
            is_correct_password = werkzeug.security.check_password_hash(pwhash, password)
            if is_correct_password:
                login_user(user)
                if user.id == 1:
                    user.is_admin = True
                    db.session.commit()

                return redirect(url_for('index'))
            else:
                flash("Log on credentials are incorrect, please try again")

    return render_template("login.html", form = form)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = CreateUserForm()
    if form.validate_on_submit():
        user_password = form.password.data
        email = form.email.data
        user = User.query.filter_by(email = email).first()
        if user:
            flash("Account already registered under this email.  Please try logging in instead")
        else:
            hashed_password = werkzeug.security.generate_password_hash(user_password, method='pbkdf2:sha256', salt_length=8)
            new_user = User(
                email = email,
                password = hashed_password,
                name = form.name.data,
                is_admin = False

        )
            db.session.add(new_user)
            db.session.commit()
            user = User.query.filter_by(email=email).first()

            login_user(new_user)

            return redirect(url_for('index'))
    return render_template("register.html", form = form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        is_edit = False
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("post", id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)

@app.route('/delete', methods=["POST", "GET"])
@admin_only
def delete():
    post_id = request.args.get("post_id")
    post = BlogPost.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    all_posts = db.session.query(BlogPost).all()
    return render_template('index.html', blog_posts=all_posts)



@app.route('/admin-panel', methods=["POST", "GET"])
@admin_only
def create_admin():
    form = CreateAdminForm()
    if form.validate_on_submit():
        email = form.email.data
        new_admin = User.query.filter_by(email = email).first()
        if not new_admin:
            flash("No user found with this email.  Try Registering them instead.")
        new_admin.is_admin = True
        db.session.commit()
        flash("User added to admin team successfully")

    return render_template('admin-panel.html', form = form)


if __name__ == "__main__":
    app.run(debug=True)
