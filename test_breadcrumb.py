from flask import Flask
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
from flask import Flask, render_template, redirect, url_for, request, make_response, session, abort
from flask import jsonify
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import datetime
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
from flask_restful import reqparse, abort, Api, Resource
from random import randint


app = Flask(__name__)

# Initialize Flask-Breadcrumbs
Breadcrumbs(app=app)


@app.route('/')
@register_breadcrumb(app, '.', 'Home')
def index():
    number = randint(1, 100)
    return render_template("tests2.html", number=number)


@app.route("/a")
@register_breadcrumb(app, '.a', 'a')
def a():
    return render_template("tests.html")

if __name__ == '__main__':
    app.run()
