# Local Setup
- Clone the project
- Run `local_setup.sh`

# Local Development Run
- `local_run.sh` To start the flask instance
-  `development`. Suited for local development and testing purposes

# Replit Execution
- Go to shell and run
    `pip install --upgrade poetry`
- Click on `main.py` and click button run
- Sample project is at https://replit.com/@iitcharankruthiventi/Kanban-v1
- The web app will be availabe at https://Kanban-v1.iitcharankruthiventi.repl.co
- Format https://<replname>.<username>.repl.co

# Folder Structure

- `database.sqlite3` has the sqlite DataBAse. Add the appropriate path in `main.py`.
- `.gitignore` - ignore file
- `local_setup.sh` Setup the virtualenv inside a local `.env` folder. Uses `pyproject.toml` and `poetry` to setup the project
- `local_run.sh`  Used to run the flask application in development mode
- `static` - default `static` files folder. It serves at '/static' path. More about it is [here](https://flask.palletsprojects.com/en/2.0.x/tutorial/static/).

- `static/allhome.js` All the javascript functions for the home page have been added in this file
- `templates` - Default flask templates folder


```
├── KanbanApp
    ├──__pycache__
    │    ├── config.cpython-36.pyc
    │    ├── config.cpython-37.pyc
    │    ├── controllers.cpython-36.pyc
    │    ├── controllers.cpython-37.pyc
    │    ├── database.cpython-36.pyc
    │    ├── database.cpython-37.pyc
    │    ├── __init__.cpython-36.pyc
    │    ├── __init__.cpython-37.pyc
    │    ├── models.cpython-36.pyc
    │    └── models.cpython-37.pyc
    ├── database.sqlite3
    ├── local_run.sh
    ├── local_setup.sh
    ├── main.py
    ├── poetry.lock
    ├── pyproject.toml
    ├── readme.md
    ├── requirements.txt
    ├── Insomnia.yaml
    ├── static
    |   ├── allhome.js
    |   ├── board_back.png
    |   ├── card_pic.png
    └── templates
        ├── home.html
        ├── login.html
        ├── signUp.html
        ├── forgotCred.html
        └── summary.html
```