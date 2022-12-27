from flask import Flask, render_template, url_for
import time


app = Flask(__name__)
year = time.localtime().tm_year

@app.route("/")
def home():
	return render_template("index.html", year = year)

@app.route("/cv")
def cv():
	return render_template("cv.html", year = year)



if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0")
	# app.run(debug=True)