from flask import Flask, render_template, url_for
import time


app = Flask(__name__)

@app.route("/")
def home():
	year = time.localtime().tm_year
	return render_template("index.html", year = year)



if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0")