# PWP SPRING 2024
# Online Board Game
# Group information
* Markus Komulainen markkomu@student.oulu.fi
* Antti Korpi akorpi20@student.oulu.fi
* Mikael Marin mmarin20@student.oulu.fi
* Waltteri Rasila krasila@student.oulu.fi

## Technical information

Database uses SQLite, version 3.40.1\
(Python sqlite3 library version: 2.6.0)

## Instructions:

**Pull submodules if you want to use the client and spectator API:**\
```git submodule update```

**(Optional but recommended) Setup a python virtual environment:**\
```python -m venv <name>```

- **Activate environment:**\
```<name>/Scripts/activate.bat``` (Windows)

**Install dependencies:**\
```pip install -r requirements.txt```

**Install app package:**\
```pip install -e .```

**Setup an example database:**\
```flask populate-db```

**Run the API:**\
```flask run```

**Run tests (inside the virtual environment after installing the package):**\
```pytest```

**Test coverage:**\
```pytest --cov-report term-missing --cov=app```
