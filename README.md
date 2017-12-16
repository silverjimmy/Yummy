# Challange3

#Yummy Category Api - FLASK

## Introduction
Flask API


## Installation
* Create a virtual environment to work on the project.
    ```
    virtualenv {name of the venv u want}
    ```
Then Activate the venv using:
    ```
    source {virtual environment you created}/bin/activate
    ```
* Create database:
using python
    ```
    -from recipe.models import db
    -db.create_all()
    ```
* Do database migrations.
    ```
    -python ./manage.py db init
    -python ./manage.py db migrate
    -python ./manage.py db upgrade
    ```

* Navigate to the application directory:

    ```
    cd Yummy_Recipe_API
    ```

* Create a virtual environment to install the
application in. You could install virtualenv and virtualenvwrapper.
Within your virtual environment, install the application package dependencies with:

    ```
    pip install -r requirements.txt
    ```

* Run the application with:

    ```
    python run.py
    ```
* for tests run in terminal using:

    ```
    pytest tests
    ```

#### URL endpoints

| URL Endpoint | HTTP Methods | Summary |
| -------- | ------------- | --------- |
| `/auth/register/` | `POST`  | Register a new user|
| `/auth/login/` | `POST` | Login and retrieve token|
| `/categories/` | `POST` | Create a new Category |
| `/categories/` | `GET` | Retrieve all categories for user |
| `/categories?q=` | `GET` | Queries Database for the specific Category |
| `/categories?limit=` | `GET` | Sets the number of items to show after querying the Database |
| `/categories/<id>/` | `GET` |  Retrieve category list details |
| `/categories/<id>/` | `PUT` | Update category list details |
| `/categories/<id>/` | `DELETE` | Delete a category list |
| `/categories/<id>/recipe/` | `POST` |  Create recipe in a category list |
| `/categories/<id>/recipe/<recipe_id>/` | `DELETE`| Delete a recipe in a category list|
| `/categories/<id>/recipe/<recipe_id>/` | `PUT`| update a category list recipe details|


##Note
Remember to set up ur postgres according to your system config for postrges.
