import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Maak een object LoginManager() aan
login_manager = LoginManager()

app = Flask(__name__)

# verbind de Flask App met de Database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SECRET_KEY"] = "5678909876567890987654567898765"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# verbind de database met Flask
db = SQLAlchemy(app)
Migrate(app, db)

# De app wordt bekend gemaakt bij de Loginmanager
login_manager.init_app(app)

# de view die zorgt voor het inloggen
login_manager.login_view = "login"
