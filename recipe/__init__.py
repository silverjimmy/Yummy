from flask import Flask


app = Flask(__name__)
app.config["SECRET_KEY"] = "This is bruno"

from . import models
from . import views
