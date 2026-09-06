from flask import Blueprint, render_template

sub_pages = Blueprint("sub_pages", __name__)

@sub_pages.route("/contact")
def contact():
    return render_template("contact.html")

@sub_pages.route("/projects")
def projects():
    return render_template("projects.html")