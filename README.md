# naamataulu-backend

## Setting up the environment

### Environment variables

You need to have the required environment variables in `.env` file.
Template file can be found `template.env`.

```bash
DJANGO_SECRET_KEY=          # https://docs.djangoproject.com/en/2.1/ref/settings/#s-secret-key
DJANGO_DEBUG=True           # https://docs.djangoproject.com/en/2.1/ref/settings/#s-debug
DJANGO_SQLITE=              # True if you want to run local sqlite database
DATABASE_URL=               # Address and credentials of postgres database (Found in Heroku settings)
DISABLE_COLLECTSTATIC=      # Set true for local
WEB_CONCURRENCY=            # How many instances of the backend Gunicorn runs (1 is enough for local testing)
PORT=                       # TCP port the service listens to
ALLOWED_HOST=               # Comma separated API addresses. (A list of strings representing the host/domain names that this Django site can serve. This is a security measure to prevent HTTP Host header attacks, which are possible even under many seemingly-safe web server configurations.)

# Application envars and their default values
DEFAULT_IMPLEMENTER=dlib
MAX_FEATURES_PER_USER=3
MULTITHREAD=0
PROCESS_COUNT=4
MAX_RECOGNIZED_USERS=3
```

### Without Docker

If you are able to install the dependencies locally without Docker the backend should run just fine after you have passed the environment variables.
(See ```run.sh```)

#### Virtualenv
You need to setup virtualenv to make sure you are using right package versions:

```bash
# Linux
pip install virtualenv                      
virtualenv ENV --python=/usr/bin/python3.6      # We are using Python 3.6
source ENV/bin/activate                         # Activate environment
sh run.sh                                       # Run the app
sh run_tests.sh                                 # Run the tests
```

### Docker
```bash
# Build
docker build -t naamataulu-backend:latest

# Run
docker run --env-file .env -p 8000:8000 -it naamataulu-backend
```

Or with docker-compose

```bash
# Build & run
docker-compose up

# Running tests
sh run_tests_compose.sh
# or
docker-compose run web bash -c "cd src/naamataulu && python3 manage.py test api/tests"
```

## Modifying the model

If you modify the models (models.py) make sure to create migration files so they can be ran by other developers / production environment!

You need to be able to run the environment locally to make migration files. If you have problems installing some packages you can try disabling them since the makemigrations should only depend on Django.

```bash
python manage.py makemigrations
```

After running the command there should be a new migration file in ```src/naamataulu/api/migrations```.
