from flask import Flask, render_template
from sub_pages.views import sub_pages

app = Flask(__name__)

app.register_blueprint(sub_pages)

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
