from flask import Flask, render_template, url_for, request, redirect
import time
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, PasswordField, StringField, TextAreaField, SelectMultipleField, SubmitField, DateField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
database = SQLAlchemy(app)

ckeditor = CKEditor(app)

# today = time.localtime()
today = date.today()
# year = today.tm_year
year = today.year



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
	posts = PortfolioEntry.query.all()
	return render_template("portfolio.html", year = year, posts = posts)

@app.route("/portfolio/<int:id>")
def portfolio_entry(id):
	post = database.get_or_404(PortfolioEntry, id)
	return render_template("portfolioEntryTemplate.html", year = year, post = post)

@app.route("/portfolio/add-entry", methods = ["GET", "POST"])
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
	return render_template("newPost.html", year = year, form = form)



if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0")
	# app.run(debug=True)