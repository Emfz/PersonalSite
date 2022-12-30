from flask import Flask, render_template, url_for
import time
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
database = SQLAlchemy(app)

year = time.localtime().tm_year


class PortfolioEntry(database.Model):
	id = database.Column(database.Integer, primary_key = True)
	title = database.Column(database.String, nullable = False)
	subtitle = database.Column(database.String(150))
	abstract = database.Column(database.String(300))
	category_tag = database.Column(database.String(100))
	date = database.Column(database.String(10), nullable = False)
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


if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0")
	# app.run(debug=True)