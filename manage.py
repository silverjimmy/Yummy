from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import os

from recipe import app
from recipe.models import db

app.config["SQLALCHEMY_DATABASE_URL"] = "postgresql://postgres:admin1234@localhost/sample_db"
migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()