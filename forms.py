from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired, URL, length
from flask_ckeditor import CKEditorField, CKEditor

class CreateCommentForm(FlaskForm):
    body = CKEditorField("Comment")
    submit = SubmitField("Post Comment")

class CreateAdminForm(FlaskForm):
    email = EmailField("Enter Email of User", validators=[DataRequired()])
    submit = SubmitField("Make Admin")

class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField('Blog Content')
    submit = SubmitField("Submit Post")

class CreateUserForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField(validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")

class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators = [DataRequired()])
    submit = SubmitField("Log in")
