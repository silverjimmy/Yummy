from flask_sqlalchemy import SQLAlchemy
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from passlib.hash import sha256_crypt
from . import app
import os

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:admin1234@localhost/finalapi"
db = SQLAlchemy(app)


class Recipe(db.Model):

    __tablename__ = "Recipe"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    """ You can set this so it changes whenever the row is updated """
    date_modified = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, nullable=False)
    """ creates an association in Categories so we can get the
    recipe an category belongs to """
    categories = db.relationship("Categories", backref="recp", lazy="dynamic")

    def __init__(self, name, date_created, created_by, date_modified):
        self.name = name
        self.date_created = date_created
        self.created_by = created_by
        self.date_modified = date_modified

    def __repr__(self):
        return "<{} {} {} {} {} >".format(self.id, self.name, self.date_created, self.date_modified, self.created_by)

    def set_last_modified_date(self, date):
        self.date_modified = date

    def returnthis(self):
        allcatergories = [category.returnthis() for category in self.categories]
        return {
            "id": self.id,
            "name": self.name,
            "date_created": self.date_created,
            "date_modified": self.date_modified,
            "created_by": self.created_by,
            "categories": allcatergories
        }


class Categories(db.Model):

    __tablename__ = "Categories"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    """ You can set this so that it changes whenever the row is updated """
    date_modified = db.Column(db.DateTime, nullable=True)
    done = db.Column(db.Boolean, nullable=False, unique=False, default=False)
    recipeid = db.Column(db.Integer, db.ForeignKey("Recipe.id"), nullable=False, unique=False)

    def __init__(self, name, date_created, date_modified, recipeid, done=False):
        self.name = name
        self.date_created = date_created
        self.done = done
        self.date_modified = date_modified
        self.recipeid = recipeid

    def __repr__(self):
        return "<{} {} {} {} {} >".format(self.userid, self.name, self.date_created, self.date_modified, self.done)

    def set_last_modified_date(self, date):
        self.date_modified = date

    def returnthis(self):
        return {
            "id": self.id,
            "name": self.name,
            "date_created": self.date_created,
            "date_modified": self.date_modified,
            "done": self.done
        }


class User(db.Model):

    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = self.hash_password(password)

    def __repr__(self):
        return "<{} {} {}>".format(self.id, self.username, self.password)

    def validate_password(self, supplied_password):
        """ validate if password supplied is correct """
        return sha256_crypt.verify(supplied_password, self.password)

    def hash_password(self, password):
        return sha256_crypt.encrypt(password)

    def generate_auth_token(self):
        # generate authentication token based on the unique userid field
        s = Serializer(app.config['SECRET_KEY'], expires_in=6000)
        return s.dumps({"id": self.id})  # this is going to be binary

    @staticmethod
    # this is static as it is called before the user object is created
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'], expires_in=30)
        try:
            # this should return the user id
            user = s.loads(token)
        except (SignatureExpired, BadSignature):
            return None
        return user["id"]
