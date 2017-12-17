from datetime import datetime
import unittest
from flask import json
from .test_base import BaseTestCase
from recipe.models import db, User, Category, Recipes


class TestCategory(BaseTestCase):

    def login_user(self):
        """ We use this to login the user.
        we generate a token we use user whenever we send a request."""
        self.user = db.session.query(User).filter_by(username="admin").first()
        # simulate login
        self.token = self.user.generate_auth_token().decode("utf-8")

    def create_category(self):
        self.new_category = Category(
            name="testcategory",
            description="test",
            date_created=datetime.now(),
            created_by=self.user.id,
            date_modified=datetime.now())
        db.session.add(self.new_category)
        db.session.commit()

    def create_category_recipe(self):
        self.new_recipe = Recipes(
            name="cook something",
            description="test",
            date_created=datetime.now(),
            categoryid=1,
            date_modified=datetime.now())
        db.session.add(self.new_recipe)
        db.session.commit()

    def create_user(self):
        new_user = User(username="testuser", password="testuser", email="admin@gmail.com")
        db.session.add(new_user)
        db.session.commit()
        self.new_user = db.session.query(User).filter_by(username="testuser").first()
        self.token = new_user.generate_auth_token().decode("utf-8")
        """we use this new user when we are going to be testing if a user can do
        something to a category that does not belong to them"""

    def test_access_route_invalid_token(self):
        self.login_user()
        self.token = ""
        details={"categoryname":"sample","des":"test"}
        response1 = self.client.post("/categories", data=json.dumps(details),
            headers={"Authorization": "Bearer {}".format(self.token)})
        response2 = self.client.get("/categories", data=json.dumps(details),
            headers={"Authorization": "Bearer {}".format(self.token)})
        response3 = self.client.put("/categories/<1>", data=json.dumps(details),
            headers={"Authorization": "Bearer {}".format(self.token)})
        response4 = self.client.delete("/categories/<1>", data=json.dumps(details),
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response1.status_code, 401)
        self.assertEqual(response2.status_code, 401)
        self.assertEqual(response3.status_code, 401)
        self.assertEqual(response4.status_code, 401)

    def test_create_category_no_categoryname(self):
        self.login_user()
        details={"categoryname":"","des":"test"}# blank and invalid name
        response = self.client.post(
            "/categories", data=json.dumps(details),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_get_categories(self):
        self.login_user()
        self.create_category()
        response = self.client.get("/categories", headers={
            "Authorization": "Bearer {}".format(self.token)})
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_get_categories_with_id(self):
        self.login_user()
        self.create_category()
        response = self.client.get("/categories/1", headers={
            "Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_get_categorys_invalid_id(self):
        # invalid category id, category that does not exist
        self.login_user()
        response = self.client.get("/categories/1", headers={
            "Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        # test we return error json containing error message
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_get_category_unauthorized(self):
        # when  they try to access a resource that is not theirs
        self.login_user()
        # create the only category list in the system, it belongs to admin id 1
        self.create_category()
        """ the category belongs to member one, i.e admin
        created another user and attempt to access the category """
        self.create_user()
        # try to gain access with thier token to admins category
        response = self.client.get("/categories/1", headers={
            "Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_update_category(self):
        self.login_user()
        self.create_category()
        response = self.client.put("/categories/1", data=json.dumps(
            {"name": "newname","description":"better cooking"}),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        # we need to check that indeed the name was changed
        r = db.session.query(Category).filter_by(id=1).first()
        self.assertTrue(r.name == "newname")

    def test_update_category_invalid_id(self):
        self.login_user()
        # we dont have any category in the system
        response = self.client.put(
            "/categories/1", data=json.dumps({"name": "newname"}),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_update_category_unauthorized(self):
        # when a user tries to get another users category
        self.login_user()
        self.create_category()
        self.create_user()  # the new user who should not have access to this category
        response = self.client.put("/categories/1", data=json.dumps(
            {"name": "newname"}), headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_update_category_wrong_parameters(self):
        self.login_user()
        self.create_category()
        # pass non existing parameter in json body before update
        response = self.client.put(
            "/categories/1",
            data=json.dumps({"sajdkbasjkd": "newname"}),
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_delete_category(self):
        self.login_user()
        self.create_category()
        response = self.client.delete(
            "/categories/1",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 200)
        r = db.session.query(Category).filter_by(name="testcategory").first()
        self.assertFalse(r is None)

    def test_delete_category_invalid_id(self):
        self.login_user()
        """there is no category in the system"""
        response = self.client.delete(
            "/categories/1",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_delete_category_unauthorized(self):
        """when a user tries to delete another users category"""
        self.login_user()
        self.create_category()
        """the new user should not have access to the category"""
        self.create_user()
        response = self.client.delete(
            "/categories/1",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_create_new_recipe_category(self):
        self.login_user()
        self.create_category()
        # test if we can created a new recipe in the category created above
        response = self.client.post(
            "/categories/1/recipe",
            data=json.dumps(
                {"name": "snacks","description":"simple meal"}
                ),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        category = db.session.query(
            Category).filter_by(name="testcategory").first()
        self.assertTrue(category.recipe[0].name == "snacks")

    def test_create_category_recipe_no_name(self):
        self.login_user()
        self.create_category()
        # test if we can created a new recipe in the category created above
        response = self.client.post("/categories/1/recipe", data=json.dumps(
            {"name": "", "date_created": "asd"}),
            headers={"Authorization": "Bearer {}".format(self.token)},
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_update_recipe_category(self):
        self.login_user()
        self.create_category()
        self.create_category_recipe()
        response = self.client.put("/categories/1/recipe/1", data=json.dumps(
            {
                "name": "do this",
                "description": "this is a new meal"
            }), content_type="application/json",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 200)

    def test_update_category_recipe_invalid_id(self):
        self.login_user()
        self.create_category()
        # there is no recipe to delete in database attempting to delete recipe id 1
        response = self.client.put(
            "/categories/1/recipe/1",
            data=json.dumps({
                "name": "do this", "date_created": "asd", "category_id": 1
                }), content_type="application/json",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))

    def test_delete_recipe_category(self):
        self.login_user()
        self.create_category()
        self.create_category_recipe()
        response = self.client.delete(
            "/categories/1/recipe/1",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 200)
        recipe = db.session.query(Recipes).get(1)
        self.assertTrue(recipe is None)

    def test_delete_category_recipe_invalid_id(self):
        self.login_user()
        self.create_category()
        # no recipe to delete in database
        response = self.client.delete(
            "/categories/1/recipe/1",
            headers={"Authorization": "Bearer {}".format(self.token)})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(type(json.loads(response.data) == "json"))


if __name__ == "__main__":
    unittest.main()
