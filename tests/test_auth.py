import unittest
from flask import json
from .test_base import BaseTestCase


class TestLogin(BaseTestCase):
    """ Test register and Sign up for a user """

    def test_access_invalid_endpoint(self):
        response = self.client.post("/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(json.loads(response.data))  # if we don't generate JSON here, we will error

    def test_login(self):
        # attempt to create new valid user and login
        credentials = {"username": "admin", "password": "admin"}
        response = self.client.post("/auth/login", data=json.dumps(credentials), content_type="application/json")
        self.assertTrue(response.status_code, 200)

    def test_login_no_username(self):
        credentials = {"username": "", "password": "admin"}
        response = self.client.post("/auth/login", data=json.dumps(credentials), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertTrue(json.loads(response.data))  # test return JSON err msg

    def test_login_no_password(self):
        credentials = {"username": "admin", "password": ""}
        response = self.client.post("/auth/login", data=json.dumps(credentials), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertTrue(json.loads(response.data))  # test return JSON err msg

    def test_login_no_credentials(self):
        credentials = {"username": "", "password": ""}
        response = self.client.post("/auth/login", data=json.dumps(credentials), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertTrue(json.loads(response.data))  # test return JSON err msg

    def test_login_no_required_field(self):
        credentials = {"username": "andrew"}
        response = self.client.post("/auth/login", data=json.dumps(credentials), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertTrue(json.loads(response.data))  # test return JSON err msg

    def test_register_user(self):
        credentials = {"username": "andrew", "password": "andrew"}  # this should be the second user we are registering
        response = self.client.post("/auth/register", data=json.dumps(credentials), content_type="application/json")
        self.assertEqual(response.status_code, 201)

    def test_register_user_no_username(self):
        credentials = {"username": "", "password": "andrew"}  # this should be the second user we are registering
        response = self.client.post("/auth/register", data=json.dumps(credentials), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertTrue(json.loads(response.data))  # test return JSON err msg

    def test_register_user_pass_no_password(self):
        credentials = {"username": "andrew", "password": ""}  # this should be the second user we are registering
        response = self.client.post("/auth/register", data=json.dumps(credentials), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertTrue(json.loads(response.data))

    def test_register_user_pass_no_username_or_password(self):
        credentials = {"username": "", "password": ""}  # this should be the second user we are registering
        response = self.client.post("/auth/register", data=json.dumps(credentials), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertTrue(json.loads(response.data))  # test return JSON err msg

    def test_register_with_existing_username(self):
        credentials = {"username": "admin", "password": "admin"}  # this should be the second user we are registering
        response = self.client.post("/auth/register", data=json.dumps(credentials), content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(json.loads(response.data))  # test return JSON err msg

    def test_register_user_required_field_not_passed(self):
        # if the dev forgets to add fields in required format as API requires
        credentials = {"username": "admin"}  # this should be the second user we are registering
        response = self.client.post("/auth/register", data=json.dumps(credentials), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertTrue(json.loads(response.data))  # test return JSON err msg


if __name__ == "__main__":
    unittest.main()
