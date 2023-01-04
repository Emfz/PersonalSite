from flask import Flask, render_template, url_for, request, redirect, flash
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, PasswordField, StringField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField
from werkzeug.security import check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from dotenv import dotenv_values

env_values = dotenv_values(".env")

app = Flask(__name__)
app.secret_key = env_values.get("SECRET_KEY")


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
database = SQLAlchemy(app)

ckeditor = CKEditor(app)

login_manager = LoginManager(app)

today = date.today()
year = today.year


class LoginForm(Form):
	user = StringField("User", validators = [DataRequired()])
	password = PasswordField("Password", validators = [DataRequired()])
	submit = SubmitField()

class PortfolioEntryCreationForm(Form):
	title = StringField("Title", validators = [DataRequired()])
	subtitle = StringField("Subtitle")
	abstract = StringField("Abstract")
	category_tag = SelectMultipleField("Tags", choices = ["C++", "Python", "Java", "C", "Web", "Electronics", "Control", "Robotics"])
	body = CKEditorField("Body", validators = [DataRequired()])	
	submit = SubmitField()

class PortfolioEntry(database.Model):
	id = database.Column(database.Integer, primary_key = True)
	title = database.Column(database.String, nullable = False)
	subtitle = database.Column(database.String(150))
	abstract = database.Column(database.String(300))
	category_tag = database.Column(database.String(100))
	date = database.Column(database.Date, nullable = False)
	body = database.Column(database.Text, nullable = False)

class User(UserMixin):
	def __init__(self) -> None:
		super().__init__()
		self.id = 0
	def get_id(self):
		return self.id

with app.app_context():
	database.create_all()
	# TestEntry = PortfolioEntry(title = "Emulating the Chip-8 processor",
	# 							subtitle = "A flashback to the dawn of videogames.",
	# 							abstract = "I'll walk you through how I emulated a retro console in a modern system.",
	# 							category_tag = "c++,python,java",
	# 							date = year,
	# 							body = "ASDF")
	# database.session.add(TestEntry)
	# database.session.commit()



@app.route("/")
def home():
	return render_template("index.html", year = year)

@app.route("/cv")
def cv():
	return render_template("cv.html", year = year)

@app.route("/portfolio")
def portfolio():
	entries = PortfolioEntry.query.all()
	return render_template("portfolio.html", year = year, entries = entries)

@app.route("/portfolio/<int:id>")
def portfolio_entry(id):
	entry = database.get_or_404(PortfolioEntry, id)
	return render_template("portfolioEntryTemplate.html", year = year, entry = entry)

@app.route("/portfolio/add-entry", methods = ["GET", "POST"])
@login_required
def create_portfolio_entry():
	form = PortfolioEntryCreationForm(request.form)
	if request.method == "POST" and form.validate():
		date = today
		new_entry = PortfolioEntry(title = form.title.data,
						subtitle = form.subtitle.data,
						abstract = form.abstract.data,
						category_tag = ','.join(form.category_tag.data),
						date = date,
						body = form.body.data)
		database.session.add(new_entry)
		database.session.commit()
		return redirect(url_for('portfolio'))
	return render_template("newEntry.html", year = year, form = form)

@app.route("/login", methods = ["GET", "POST"])
def login():
	form = LoginForm(request.form)
	if request.method == "POST" and form.validate():
		user_hash = env_values.get("USER_HASH")
		password_hash = env_values.get("PASSWORD_HASH")
		user = form.user.data
		password = form.password.data
		if check_password_hash(user_hash, user) and check_password_hash(password_hash, password):
			login_user(User())
			return redirect(url_for('portfolio'))
		flash("Incorrect credentials")
	return render_template("login.html", form = form)


@app.route("/portfolio/delete-confirmation/<int:id>")
@login_required
def delete_confirmation(id):
	entry = database.get_or_404(PortfolioEntry, id)
	return render_template("deleteConfirmation.html", year = year, entry = entry)

@app.route("/portfolio/delete/<int:id>", methods = ["POST"])
@login_required
def delete(id):
	entry = database.get_or_404(PortfolioEntry, id)
	database.session.delete(entry)
	database.session.commit()
	return redirect(url_for('portfolio'))

@app.route("/portfolio/edit/<int:id>", methods = ["GET", "POST"])
@login_required
def edit_entry(id):
	entry = database.get_or_404(PortfolioEntry, id)
	if request.method == "GET":
		form = PortfolioEntryCreationForm(title = entry.title,
									subtitle = entry.subtitle,
									abstract = entry.abstract,
									category_tag = entry.category_tag.split(","),
									body = entry.body)
	else:
		form = PortfolioEntryCreationForm(request.form)
	if request.method == "POST" and form.validate():
		entry.title = form.title.data
		entry.subtitle = form.subtitle.data
		entry.abstract = form.abstract.data
		entry.category_tag = ','.join(form.category_tag.data)
		entry.body = form.body.data
		database.session.commit()
		return redirect(url_for('portfolio'))
	return render_template("editEntry.html", year = year, form = form, id = entry.id)


# Login manager
@login_manager.user_loader
def load_user(user_id):
	if user_id == 0:
		return User()
	return None

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for("home"))



if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0")
	# app.run(debug=True)