from datetime import datetime
from flask import request, jsonify, g, json
from flask_httpauth import HTTPTokenAuth
from . import app
from .models import db
from .models import User, Recipe, Categories


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


@app.route("/auth/login", methods=["POST"])
def login():
    """ This function logs the user in.
    checks for supplied parameters against db
    generates token and sends to the user if valid user"""
    if not request.json:
        return jsonify({"message": "Expected username and password sent via JSON"}), 400
    username = request.json.get("username")
    password = request.json.get("password")
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


@app.route("/auth/register", methods=["POST"])
def register():
    """ This function registers a new user.
    checks credentials provided against existing ones
    makes sure every user is unique
    sends auth token to the user"""
    if not request.json:
        return jsonify({"message": "Expected username and password sent via JSON"}), 400
    username = request.json.get("username")
    password = request.json.get("password")
    if not username or not password:
        return jsonify({"message": "Requires username and password to be provided"}), 401
    user = db.session.query(User).filter_by(username=username).first()
    if user:
        return jsonify({"message": "Cannot create user, already exists"}), 403
    new_user = User(username, password)
    db.session.add(new_user)
    db.session.commit()
    token = new_user.generate_auth_token()
    # return json.dumps({"token": str(token)}), 201
    return json.dumps({"token": token.decode('utf-8')}), 201


@app.route("/recipes", methods=["POST"])
@auth.login_required
def create_recipe():
    """ This function creates a new recipe.
    make sure the user has a valid token before creating"""
    # we are logged in, we have access to g, where we have a field, g.userid
    if not request.json or request.json.get("name") is None or request.json.get("name") == "":
        return jsonify({
            "message": "Please supply recipe name"
            }), 400
    recipe = db.session.query(Recipe).filter_by(created_by=g.user.id, name=request.json.get("name")).first()
    if recipe:
        return jsonify({
            "message": "The Recipe name you are using has already been saved"}), 400
    recipe = Recipe(name=request.json.get("name"), date_created=datetime.now(), created_by=g.user.id, date_modified=datetime.now())
    db.session.add(recipe)
    db.session.commit()
    return jsonify({"message": "Recipe Saved"}), 201


@app.route("/recipes", methods=["GET"])
@auth.login_required
def list_created_recipe():
    """ Return the recipes belonging to the user.
    determine user from the supplied token """
    search_name = False
    search_limit = False
    if request.args.get("q"):
        search_name = True
    if request.args.get("limit"):
        search_limit = True
    if search_name and search_limit:
        recipe = db.session.query(Recipe).filter_by(created_by=g.user.id).filter(Recipe.name.like("%{}%".format(request.args.get("q")))).limit(request.args.get("limit")).all()
    elif search_name:
        recipe = db.session.query(Recipe).filter(Recipe.created_by == g.user.id, Recipe.name.like('%{}%'.format(request.args.get("q")))).all()
    elif search_limit:
        recipe = db.session.query(Recipe).filter_by(created_by=g.user.id).limit(request.args.get("limit")).all()
    else:
        recipe = db.session.query(Recipe).filter_by(created_by=g.user.id).all()
    ls = []
    if not recipe:
        if not search_name:
            return jsonify(
                {"message": "Need to supply name of category you are looking for"}
                ), 400
        else:
            return jsonify(
                {"message": "No category with that name belonging to user"}
                ), 401
    for category in recipe:
        ls.append(category.returnthis())
    return jsonify(ls), 200


@app.route("/recipes/<catergoryid>", methods=["GET"])
@auth.login_required
def get_recipe(catergoryid):
    """ Return the certain recipe for user. """
    ls = []
    recipe = db.session.query(Recipe).get(catergoryid)
    if not recipe:
        return jsonify({"message": "No category with that id"}), 400
    if not recipe.created_by == g.user.id:
        return jsonify({
            "message": "That category does not belong to you "}), 403
    ls.append(recipe.returnthis())
    return jsonify(ls), 200


@app.route("/recipes/<id>", methods=["PUT"])
@auth.login_required
def update_recipe(id):
    """ Update name or done status of a recipe """
    if not request.json or request.json.get("name") is None or request.json.get("name") == "":
        return jsonify({"message": "you need to supply new edits in json"}), 400
    recipe = db.session.query(Recipe).filter_by(id=id).first()
    if not recipe:
        return jsonify({"message": "The category you request does not exist"}), 400
    if not recipe.created_by == g.user.id:
        return jsonify({"message": "You don't have permission to modify this category"}), 403
    recipe.name = request.json.get("name")
    recipe.date_modified = datetime.now()
    db.session.commit()
    return jsonify({"message": "successful update"}), 200


@app.route("/recipes/<id>", methods=["DELETE"])
@auth.login_required
def delete_recipe(id):
    recipe = db.session.query(Recipe).filter_by(id=id).first()
    if not recipe:
        return jsonify({"message": "The category you request does not exist"}), 400
    if not recipe.created_by == g.user.id:
        return jsonify(
            {"message": "You don't have permission to modify this category"}), 400
    db.session.delete(recipe)
    db.session.commit()
    return jsonify({"message": "Deleted recipe"}), 200


@app.route("/recipes/<id>/categories", methods=["POST"])
@auth.login_required
def create_new_catergory(id):
    """ This function created a new category in the recipe."""
    if not request.json:
        return jsonify(
            {"message": "you need to supply name of new category as JSON"}), 400
    catergory_name = request.json.get("name")
    if catergory_name is None or catergory_name == "":
        return jsonify(
            {"message": "you need to supply name of new category as JSON"}
            ), 400
    recipe = db.session.query(Categories).filter_by(name=catergory_name).first()
    if recipe:
        return jsonify({"message": "User has already created that category"}), 400
    recipe = db.session.query(Recipe).filter_by(id=id).first()
    if not recipe:
        return jsonify({"message": "Recipe does not exist"}), 400
    new_catergory = Categories(
        name=catergory_name,
        date_created=datetime.now(),
        date_modified=datetime.now(),
        recipeid=id
        )
    db.session.add(new_catergory)
    db.session.commit()
    return jsonify({"message": "Successfuly created category"}), 200


@app.route("/recipes/<id>/categories/<catergory_id>", methods=["PUT"])
@auth.login_required
def update_recipe_list_catergory(id, catergory_id):
    """ Update name and done status of a recipe list category"""
    if not request.json:
        return jsonify(
            {"message": "you need to supply new name as JSON"}), 400
    catergory_name = request.json.get("name")
    done = request.json.get("done")
    if catergory_name is None or catergory_name == "":
        return jsonify({"message": "you need to supply new name as JSON"}), 400
    recipe = db.session.query(Recipe).filter_by(id=id).first()
    if not recipe:
        return jsonify({
            "message": "The recipe does not exist, it was probably deleted"
            }), 400
    recipetlistcatergory = db.session.query(Categories).filter_by(id=catergory_id).first()
    if not recipetlistcatergory:
        return jsonify(
            {"message": "Category does not exist, no category with that id"}
            ), 400
    if recipetlistcatergory.name == catergory_name:
        return jsonify(
            {"message": "No change to be recorded, set a new value for whatever you want to update"}
            ), 400
    if done:
        if done.lower() == "true":
            recipetlistcatergory.done = True
        else:
            recipetlistcatergory.done = False
    recipetlistcatergory.name = catergory_name
    recipetlistcatergory.date_modified = datetime.now()
    db.session.commit()
    return jsonify({"message": "Successfully updated category"}), 200


@app.route("/recipes/<id>/categories/<catergory_id>", methods=["DELETE"])
@auth.login_required
def delete_recipe_list_catergory(id, catergory_id):
    recipe = db.session.query(Recipe).filter_by(id=id).first()
    if not recipe:
        return jsonify(
            {"message": "Recipe does not exist, cannot delete"}
            ), 400
    if not recipe.created_by == g.user.id:
        return jsonify({
            "message": "You dont own the recipe, cannot delete"}), 401
    recipecatergory = db.session.query(Categories).filter_by(id=catergory_id).first()
    if not recipecatergory:
        return jsonify({"message": "User does not have that category, cannot delete"}), 400
    db.session.delete(recipecatergory)
    db.session.commit()
    return jsonify({"message": "Successfully deleted category"}), 200


@app.errorhandler(500)
def handle500(e):
    db.session.rollback()
    return jsonify({"messgae": "Error 500!!"}), 500


@app.errorhandler(404)
def handle404(e):
    return jsonify({"message": "Invalid endpoint"}), 404
