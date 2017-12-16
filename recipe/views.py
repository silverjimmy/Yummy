from datetime import datetime
from flask import request, jsonify, g, json
from flask_httpauth import HTTPTokenAuth
from . import app
from .models import db
from .models import User, Category, Recipes


auth = HTTPTokenAuth(scheme="Bearer")
db.create_all()

@auth.verify_token
def verify_auth_token(token):
    """ login_required is going to call verify token since this is an instance
    of HTTPTokenAuth verify_token is going to look at the value in the
    Authorization header which we set to Authorization : Bearer <key> according
    to OAuth 2 standards, parse it for us and return the token part inside of
    token parameter
    """
    # they supply a token in place of the username in HTTPBasicAuthentication
    if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
    if not token:
        return False
    userid = User.verify_auth_token(token=token)
    if userid is None:
        return False
    g.user = db.session.query(User).filter_by(id=userid).first()
    return True
@app.route("/auth/register", methods=["POST"])
def register():
    """ This function registers a new user.
    checks credentials provided against existing ones
    makes sure every user is unique
    sends auth token to the user"""
    if not request.json:
        return jsonify({"message": "Details missing"}), 400
    
    username = request.json.get("username")
    password = request.json.get("password")
    email = request.json.get("email")

    if username is None or username.replace(" ", "") == "": 
        return jsonify({"message":"User regisration details incorrect"}),401

    if request.json.get("password") is None or request.json.get("password").replace(" ", "") == "":
        return jsonify({"message":"User regisration details incorrect"}),401

    if request.json.get("email") is None or request.json.get("email").replace(" ", "") == "":
        return jsonify({"message":"User regisration details incorrect"}),401

    user = db.session.query(User).filter_by(email=email).first()
    if user:
        return jsonify({"message": "Cannot create user, User already exists"}), 403
    username
    new_user = User(username, password, email)
    db.session.add(new_user)
    db.session.commit()
    token = new_user.generate_auth_token()
    # return json.dumps({"token": str(token)}), 201
    return json.dumps({"token": token.decode('utf-8')}), 201


@app.route("/auth/login", methods=["POST"])
def login():
    """ This function logs the user in.
    checks for supplied parameters against db
    generates token and sends to the user if valid user"""
    if not request.json:
        return jsonify({"message": "Expected username and password sent via JSON"}), 400
    username = request.json.get("username").strip()
    password = request.json.get("password").strip()
    if not username or not password:
        """ we expect the username and password passed as json """
        return jsonify({"message": "Requires username and password to be\
         provided"}), 401
    new_user = db.session.query(User).filter_by(username=username).first()
    if not new_user or not new_user.validate_password(password):  # case of invalid credentials
        return jsonify({"message": "Invalid login credentials"}), 401
    # create user and store in db
    token = new_user.generate_auth_token()
    return json.dumps({"token": token.decode("utf-8"), "id": new_user.id}), 200


@app.route("/categories", methods=["POST"])
@auth.login_required
def create_category():
    """ This function creates a new category.
    make sure the user has a valid token before creating"""
    # we are logged in, we have access to g, where we have a field, g.userid
    if not request.json or request.json.get("name") is None or request.json.get("name").replace(" ", "") == "" or request.json.get("description") is None or request.json.get("description").replace(" ", "") == "":
        return jsonify({
            "message": "Please supply Required Details"
            }), 400

    
    category = db.session.query(Category).filter_by(created_by=g.user.id, name=request.json.get("name")).first()
    if category:
        return jsonify({
            "message": "The Category name you are using has already been saved"}), 400
    description = request.json.get("description")
    category = Category(name=request.json.get("name").strip(), description = request.json.get("description").strip(), date_created=datetime.now(), created_by=g.user.id, date_modified=datetime.now())
    db.session.add(category)
    db.session.commit()
    return jsonify({"message": "Category Saved"}), 201


@app.route("/categories", methods=["GET"])
@auth.login_required
def list_created_category():
    """ Return the categories belonging to the user.
    determine user from the supplied token """
    search_name = False
    search_limit = False
    if request.args.get("q"):
        search_name = True
    if request.args.get("limit"):
        search_limit = True
    if search_name and search_limit:
        category = db.session.query(Category).filter_by(created_by=g.user.id).filter(Category.name.like("%{}%".format(request.args.get("q")))).limit(request.args.get("limit")).all()
    elif search_name:
        category = db.session.query(Category).filter(Category.created_by == g.user.id, Category.name.like('%{}%'.format(request.args.get("q")))).all()
    elif search_limit:
        category = db.session.query(Category).filter_by(created_by=g.user.id).limit(request.args.get("limit")).all()
    else:
        category = db.session.query(Category).filter_by(created_by=g.user.id).all()
    ls = []
    if not category:
        if not search_name:
            return jsonify(
                {"message": "Need to supply name of recipe you are looking for"}
                ), 400
        else:
            return jsonify(
                {"message": "No recipe with that name belonging to user"}
                ), 401
    for recipe in category:
        ls.append(recipe.returnthis())
    return jsonify(ls), 200


@app.route("/categories/<id>", methods=["GET"])
@auth.login_required
def get_category(id):
    """ Return the certain category for user. """
    ls = []
    category = db.session.query(Category).get(id)
    if not category:
        return jsonify({"message": "No recipe with that id"}), 400
    if not category.created_by == g.user.id:
        return jsonify({
            "message": "That recipe does not belong to you "}), 403
    ls.append(category.returnthis())
    return jsonify(ls), 200


@app.route("/categories/<id>", methods=["PUT"])
@auth.login_required
def update_category(id):
    """ Update a category """
    if not request.json or request.json.get("name") is None or request.json.get("name").replace(" ", "") == "":
        return jsonify({"message": "you need to supply new edits in json"}), 400
    category = db.session.query(Category).filter_by(id=id).first()
    if not category:
        return jsonify({"message": "The recipe you request does not exist"}), 400
    if not category.created_by == g.user.id:
        return jsonify({"message": "You don't have permission to modify this recipe"}), 403
    category.name = request.json.get("name")
    category.description = request.json.get("description")
    category.date_modified = datetime.now()
    db.session.commit()
    return jsonify({"message": "category successful update"}), 200
  

@app.route("/categories/<id>", methods=["DELETE"])
@auth.login_required
def delete_category(id):
    category = db.session.query(Category).filter_by(id=id).first()
    if not category:
        return jsonify({"message": "The Category you requested does not exist"}), 400
    if not category.created_by == g.user.id:
        return jsonify(
            {"message": "You don't have permission to modify this Category"}), 400

        db.session.delete(category)
        db.session.commit()
    return jsonify({"message": "Successfully deleted Category"}), 200  
        # status code - not found

@app.route("/categories/<id>/recipe", methods=["POST"])
@auth.login_required
def create_new_recipe(id):
    """ This function created a new recipe in the category."""
    if not request.json:
        return jsonify(
            {"message": "you need to supply name of new recipe as JSON"}), 400
    recipe_name = request.json.get("name")
    desc = request.json.get("description")
    if recipe_name is None or recipe_name.replace(" ", "") == "":
        return jsonify(
            {"message": "you need to supply name of new recipe as JSON"}
            ), 400
    if desc is None or desc.replace(" ", "") == "":
        return jsonify(
            {"message": "you need to supply name of recipe description as JSON"}
            ), 400
    category = db.session.query(Recipes).filter_by(name=recipe_name).first()
    if category:
        return jsonify({"message": "User has already created that recipe"}), 400
    category = db.session.query(Category).filter_by(id=id).first()
    if not category:
        return jsonify({"message": "Category does not exist"}), 400
    new_recipe = Recipes(
        name=recipe_name.strip(),
        description=desc.strip(),
        date_created=datetime.now(),
        date_modified=datetime.now(),
        categoryid=id
        )
    db.session.add(new_recipe)
    db.session.commit()
    return jsonify({"message": "Successfully created recipe"}), 200

@app.route("/categories/<id>/recipe/<recipe_id>", methods=["PUT"])
@auth.login_required
def update_category_list_recipe(id, recipe_id):
    """ Update name and done status of a category list recipe"""
    if not request.json:
        return jsonify(
            {"message": "you need to supply new name as JSON"}), 400
    recipe_name = request.json.get("name").strip()
    done = request.json.get("done")
    if recipe_name is None or recipe_name == "":
        return jsonify({"message": "you need to supply new name as JSON"}), 400
    category = db.session.query(Category).filter_by(id=id).first()
    if not category:
        return jsonify({
            "message": "The category does not exist, it was probably deleted"
            }), 400
    listrecipe = db.session.query(Recipes).filter_by(id=recipe_id).first()
    if not listrecipe:
        return jsonify(
            {"message": "Recipe does not exist, no recipe with that id"}
            ), 400
    if listrecipe.name == recipe_name:
        return jsonify(
            {"message": "No change to be recorded, set a new value for whatever you want to update"}
            ), 400

    listrecipe.name = recipe_name
    listrecipe.date_modified = datetime.now()
    db.session.commit()
    return jsonify({"message": "Successfully updated recipe"}), 200


@app.route("/categories/<id>/recipe/<recipe_id>", methods=["DELETE"])
@auth.login_required
def delete_recipe_list_recipe(id, recipe_id):
    category = db.session.query(Category).filter_by(id=id).first()
    if not category:
        return jsonify({
            "message": "The category does not exist, it was probably deleted"
            }), 400
    recipe = db.session.query(Recipes).filter_by(id=recipe_id).first()
    if not recipe:
        return jsonify(
            {"message": "Recipe does not exist, no recipe with that id"}
            ), 400
    db.session.delete(recipe)
    db.session.commit()
    return jsonify({"message": "Successfully deleted recipe"}), 200

@app.errorhandler(404)
def handle404(e):
    return jsonify({"message": "Invalid endpoint"}), 404

@app.errorhandler(400)
def handle400(e):
    return jsonify({"message": "Missing details"}), 400
