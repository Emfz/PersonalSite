from flask import Flask, render_template, url_for, request, redirect, flash, abort
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, PasswordField, StringField, SelectMultipleField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp
from flask_ckeditor import CKEditor, CKEditorField
from werkzeug.security import check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from dotenv import dotenv_values
from math import ceil

ENTRIES_PER_PAGE = 10

env_values = dotenv_values(".env")

app = Flask(__name__)
app.secret_key = env_values.get("SECRET_KEY")


app.config["SQLALCHEMY_DATABASE_URI"] = env_values.get("DATABASE_URI")
database = SQLAlchemy(app)

ckeditor = CKEditor(app)
app.config['CKEDITOR_ENABLE_CODESNIPPET'] = True

login_manager = LoginManager(app)




# Forms
class LoginForm(Form):
	user = StringField("User", validators = [DataRequired(), Length(max = 10), Regexp("^[^\",'<>\{\}* ]*$")])
	password = PasswordField("Password", validators = [DataRequired(), Length(min = 1, max = 30), Regexp("^[^\",'<>\{\}* ]*$")])
	submit = SubmitField()

class PortfolioPageSelectionForm(Form):
	page_selector = SelectField("Page")

class PortfolioEntryCreationForm(Form):
	title = StringField("Title", validators = [DataRequired()])
	subtitle = StringField("Subtitle")
	abstract = StringField("Abstract")
	category_tag = SelectMultipleField("Tags", choices = ["C++", "Python", "Java", "C", "Web", "Electronics", "Control", "Robotics"])
	body = CKEditorField("Body", validators = [DataRequired()])	
	submit = SubmitField()



# Database models
class PortfolioEntry(database.Model):
	id = database.Column(database.Integer, primary_key = True)
	title = database.Column(database.String(150), nullable = False)
	subtitle = database.Column(database.String(150))
	abstract = database.Column(database.String(300))
	category_tag = database.Column(database.String(100))
	date = database.Column(database.Date, nullable = False)
	body = database.Column(database.Text, nullable = False)
	last_edit_date = database.Column(database.Date, nullable = False)



# User model
class User(UserMixin):
	def __init__(self) -> None:
		super().__init__()
		self.id = 0
	def get_id(self):
		return self.id


portfolio_cache = []
with app.app_context():
	database.create_all()
	portfolio_cache = PortfolioEntry.query.order_by(PortfolioEntry.date.desc()).all()

# Routes

@app.route("/")
def home():
	return render_template("index.html", year = get_date().year)

@app.route("/cv")
def cv():
	return render_template("cv.html", year = get_date().year)




# Portfolio routes
@app.route("/portfolio/page-<int:page_number>", methods = ["GET", "POST"])
def portfolio(page_number):
	
	if page_number == 0:
		return abort(404)

	page_selection_form = PortfolioPageSelectionForm(request.form)

	if request.method == "POST":
		return redirect(url_for('portfolio', page_number = page_selection_form.page_selector.data))
	
	entries = portfolio_cache

	if not entries:
		return render_template("portfolio.html", year = get_date().year, entries = [])

	total_entries = len(entries)
	total_pages = ceil(total_entries / ENTRIES_PER_PAGE)
	remaining_entries = total_entries - ENTRIES_PER_PAGE * (page_number - 1)
	
	page_selection_form.page_selector.choices  = [i for i in range(1, total_pages + 1)]

	# Set the default selection of the selector field as the current page number
	page_selection_form.page_selector.process_data(page_number)

	if remaining_entries > 0:
		starting_index = ENTRIES_PER_PAGE * (page_number - 1)
		slicing_index = starting_index + min(remaining_entries, ENTRIES_PER_PAGE)
		return render_template("portfolio.html", year = get_date().year, entries = entries[starting_index : slicing_index], total_pages = total_pages, current_page = page_number, form = page_selection_form)
	return abort(404)

@app.route("/portfolio/<int:id>")
def portfolio_entry(id):
	entry = database.get_or_404(PortfolioEntry, id)
	return render_template("portfolioEntryTemplate.html", year = get_date().year, entry = entry)




# Create, update, delete portfolio entries
@app.route("/portfolio/add-entry", methods = ["GET", "POST"])
@login_required
def create_portfolio_entry():
	form = PortfolioEntryCreationForm(request.form)
	today = get_date()
	if request.method == "POST" and form.validate():
		new_entry = PortfolioEntry(title = form.title.data,
						subtitle = form.subtitle.data,
						abstract = form.abstract.data,
						category_tag = ','.join(form.category_tag.data),
						date = today,
						body = form.body.data,
						last_edit_date = today)
		database.session.add(new_entry)
		database.session.commit()
		global portfolio_cache
		portfolio_cache = PortfolioEntry.query.order_by(PortfolioEntry.date.desc()).all()
		return redirect(url_for('portfolio', page_number = 1))
	return render_template("newEntry.html", year = today.year, form = form)

@app.route("/portfolio/delete-confirmation/<int:id>")
@login_required
def delete_confirmation(id):
	entry = database.get_or_404(PortfolioEntry, id)
	return render_template("deleteConfirmation.html", year = get_date().year, entry = entry)

@app.route("/portfolio/delete/<int:id>", methods = ["POST"])
@login_required
def delete(id):
	entry = database.get_or_404(PortfolioEntry, id)
	database.session.delete(entry)
	database.session.commit()
	global portfolio_cache
	portfolio_cache = PortfolioEntry.query.order_by(PortfolioEntry.date.desc()).all()
	return redirect(url_for('portfolio', page_number = 1))

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
		entry.last_edit_date = get_date()
		database.session.commit()
		global portfolio_cache
		portfolio_cache = PortfolioEntry.query.order_by(PortfolioEntry.date.desc()).all()
		return redirect(url_for('portfolio', page_number = 1))
	return render_template("editEntry.html", year = get_date().year, form = form, id = entry.id)



# Login
@app.route("/login", methods = ["GET", "POST"])
def login():
	form = LoginForm(request.form)
	if request.method == "POST":
		if not form.validate():
			flash("The input has a forbidden character")
			return redirect(url_for('login'))
		user_hash = env_values.get("USER_HASH")
		password_hash = env_values.get("PASSWORD_HASH")
		user = form.user.data
		password = form.password.data
		if check_password_hash(user_hash, user) and check_password_hash(password_hash, password):
			login_user(User())
			return redirect(url_for('portfolio', page_number = 1))
		flash("Incorrect credentials")
	return render_template("login.html", year = get_date().year, form = form)

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




# Error pages
@app.errorhandler(404)
def error404(error):
	return render_template("error404.html", year = get_date().year), 404

@app.errorhandler(401)
def error401(error):
	return render_template("error401.html", year = get_date().year), 401


def get_date():
	return date.today()

