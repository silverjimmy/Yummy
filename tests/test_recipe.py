from datetime import datetime
import unittest
from flask import json
from .test_base import BaseTestCase
from recipe.models import db, User, Recipe, Categories


class TestRecipe(BaseTestCase):

    def login_user(self):
        """ We use this to login the user.
        we generate a token we use user whenever we send a request."""
        self.user = db.session.query(User).filter_by(username="admin").first()
        # simulate login
        self.token = self.user.generate_auth_token().decode("utf-8")

    def create_recipe(self):
        self.new_recipe = Recipe(
            name="testrecipe",
            date_created=datetime.now(),
            created_by=self.user.id,
            date_modified=datetime.now())
        db.session.add(self.new_recipe)
        db.session.commit()

    def create_recipe_catergory(self):
        self.new_catergory = Categories(
            name="cook something",
            date_created=datetime.now(),
            recipeid=1,
            date_modified=datetime.now())
        db.session.add(self.new_catergory)
        db.session.commit()

    def create_user(self):
        new_user = User(username="testuser", password="testuser")
        db.session.add(new_user)
        db.session.commit()
        self.new_user = db.session.query(User).filter_by(username="testuser").first()
        self.token = new_user.generate_auth_token().decode("utf-8")
        """we use this new user when we are going to be testing if a user can do
        something to a recipe that does not belong to them"""

    def test_access_route_invalid_token(self):
        self.login_user()
        self.token = ""
        recipename = "games to buy"
        response1 = self.client.post("/recipes", data=json.dumps(
            {"name": recipename}),
            headers={"Authorization": "Bearer {}".format(self.token)})
        response2 = self.client.get("/recipes", data=json.dumps(
            {"name": recipename}),
            headers={"Authorization": "Bearer {}".format(self.token)})
        response3 = self.client.put("/recipes/<1>", data=json.dumps(
            {"name": recipename}),
            headers={"Authorization": "Bearer {}".format(self.token)})
        response4 = self.client.delete("/recipes/<1>", data=json.dumps(
            {"name": recipename}),
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response1.status_code, 401)
        self.assertEqual(response2.status_code, 401)
        self.assertEqual(response3.status_code, 401)
        self.assertEqual(response4.status_code, 401)

    def test_create_recipe(self):
        self.login_user()
        recipename = "games to buy"
        response = self.client.post(
            "/recipes",
            data=json.dumps({"name": recipename}),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        # we get this on successful creation
        self.assertEqual(response.status_code, 201)
        # also check if there is recipe in the db with that name
        name = db.session.query(Recipe).filter_by(name=recipename).first()
        self.assertTrue(name is not None)

    def test_create_recipe_no_recipename(self):
        self.login_user()
        recipename = ""  # blank and invalid name
        response = self.client.post(
            "/recipes", data=json.dumps({"name": recipename}),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_get_recipes(self):
        self.login_user()
        self.create_recipe()
        response = self.client.get("/recipes", headers={
            "Authorization": "Bearer {}".format(self.token)})
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_get_recipes_with_id(self):
        self.login_user()
        self.create_recipe()
        response = self.client.get("/recipes/1", headers={
            "Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_get_recipes_invalid_id(self):
        # invalid recipe id, recipe that does not exist
        self.login_user()
        response = self.client.get("/recipes/1", headers={
            "Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        # test we return error json containing error message
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_get_recipe_unauthorized(self):
        # when  they try to access a resource that is not theirs
        self.login_user()
        # create the only recipe list in the system, it belongs to admin id 1
        self.create_recipe()
        """ the recipe belongs to member one, i.e admin
        created another user and attempt to access the recipe """
        self.create_user()
        # try to gain access with thier token to admins recipe
        response = self.client.get("/recipes/1", headers={
            "Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_update_recipe(self):
        self.login_user()
        self.create_recipe()
        response = self.client.put("/recipes/1", data=json.dumps(
            {"name": "newname"}),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        # we need to check that indeed the name was changed
        r = db.session.query(Recipe).filter_by(id=1).first()
        self.assertTrue(r.name == "newname")

    def test_update_recipe_invalid_id(self):
        self.login_user()
        # we dont have any recipe in the system
        response = self.client.put(
            "/recipes/1", data=json.dumps({"name": "newname"}),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_update_recipe_unauthorized(self):
        # when a user tries to get another users recipe
        self.login_user()
        self.create_recipe()
        self.create_user()  # the new user who should not have access to this recipe
        response = self.client.put("/recipes/1", data=json.dumps(
            {"name": "newname"}), headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_update_recipe_wrong_parameters(self):
        self.login_user()
        self.create_recipe()
        # pass non existing parameter in json body before update
        response = self.client.put(
            "/recipes/1",
            data=json.dumps({"sajdkbasjkd": "newname"}),
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_delete_recipe(self):
        self.login_user()
        self.create_recipe()
        response = self.client.delete(
            "/recipes/1",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 200)
        r = db.session.query(Recipe).filter_by(name="testrecipe").first()
        self.assertTrue(r is None)

    def test_delete_recipe_invalid_id(self):
        self.login_user()
        """there is no recipe in the system"""
        response = self.client.delete(
            "/recipes/1",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_delete_recipe_unauthorized(self):
        """when a user tries to delete another users recipe"""
        self.login_user()
        self.create_recipe()
        """the new user should not have access to the recipe"""
        self.create_user()
        response = self.client.delete(
            "/recipes/1",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_create_new_catergory_recipe(self):
        self.login_user()
        self.create_recipe()
        # test if we can created a new category in the recipe created above
        response = self.client.post(
            "/recipes/1/categories",
            data=json.dumps(
                {"name": "snacks"}
                ),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        recipe = db.session.query(
            Recipe).filter_by(name="testrecipe").first()
        self.assertTrue(recipe.categories[0].name == "snacks")

    def test_create_recipe_catergory_no_name(self):
        self.login_user()
        self.create_recipe()
        # test if we can created a new category in the recipe created above
        response = self.client.post("/recipes/1/categories", data=json.dumps(
            {"name": "", "date_created": "asd", "recipe_id": 1}),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_update_catergory_recipe(self):
        self.login_user()
        self.create_recipe()
        self.create_recipe_catergory()
        response = self.client.put("/recipes/1/categories/1", data=json.dumps(
            {
                "name": "do this",
                "recipe_id": 1
            }), content_type="application/json",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 200)

    def test_update_recipe_catergory_invalid_id(self):
        self.login_user()
        self.create_recipe()
        # there is no category to delete in database attempting to delete category id 1
        response = self.client.put(
            "/recipes/1/categories/1",
            data=json.dumps({
                "name": "do this", "date_created": "asd", "recipe_id": 1
                }), content_type="application/json",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_delete_catergory_recipe(self):
        self.login_user()
        self.create_recipe()
        self.create_recipe_catergory()
        response = self.client.delete(
            "/recipes/1/categories/1",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 200)
        category = db.session.query(Categories).get(1)
        self.assertTrue(category is None)

    def test_delete_recipe_catergory_invalid_id(self):
        self.login_user()
        self.create_recipe()
        # no category to delete in database
        response = self.client.delete(
            "/recipes/1/categories/1",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))


if __name__ == "__main__":
    unittest.main()
