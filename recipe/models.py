from flask_sqlalchemy import SQLAlchemy
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from passlib.hash import sha256_crypt
from . import app
import os

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TESTING"] = True  
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:admin1234@localhost/main_db"
db = SQLAlchemy(app)


class Category(db.Model):

    __tablename__ = "Category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    """ You can set this so it changes whenever the row is updated """
    date_modified = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, nullable=False)
    """ creates an association in Recipes so we can get the
    category a recipe belongs to """
    recipe = db.relationship("Recipes", backref="recp", lazy="dynamic")

    def __init__(self, name, description, date_created, created_by, date_modified):
        self.name = name
        self.description = description
        self.date_created = date_created
        self.created_by = created_by
        self.date_modified = date_modified

    def __repr__(self):
        return "<{} {} {} {} {} {} >".format(self.id, self.name, self.description, self.date_created, self.date_modified, self.created_by)

    def set_last_modified_date(self, date):
        self.date_modified = date

    def returnthis(self):
        allcatergories = [recipe.returnthis() for recipe in self.recipe]
        return {
            "Id": self.id,
            "Name": self.name,
            "Description": self.description,
            "Created_by": self.created_by,
            "Recipes": allcatergories
        }


class Recipes(db.Model):

    __tablename__ = "Recipes"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False) 
    """ You can set this so that it changes whenever the row is updated """
    date_modified = db.Column(db.DateTime, nullable=True)
    categoryid = db.Column(db.Integer, db.ForeignKey("Category.id", ondelete='SET NULL'), nullable=True)
        

    def __init__(self, name, description, date_created, date_modified, categoryid):
        self.name = name
        self.description = description
        self.date_created = date_created
        self.date_modified = date_modified
        self.categoryid = categoryid

    def __repr__(self):
        return "<{} {} {} {} {} {}>".format(self.userid, self.name, self.description,self.date_created, self.date_modified)

    def set_last_modified_date(self, date):
        self.date_modified = date

    def returnthis(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "date_created": self.date_created,
            "date_modified": self.date_modified
        }


class User(db.Model):

    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)

    def __init__(self, username, password, email):
        self.username = username
        self.password = self.hash_password(password)
        self.email = email

    def __repr__(self):
        return "<{} {} {} {}>".format(self.id, self.username, self.password, self.email)

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
        s = Serializer(app.config['SECRET_KEY'], expires_in=300)
        try:
            # this should return the user id
            user = s.loads(token)
        except (SignatureExpired, BadSignature):
            return None
        return user["id"]
