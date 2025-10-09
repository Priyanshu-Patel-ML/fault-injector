# db/__init__.py
try:
    from flask_sqlalchemy import SQLAlchemy
except ImportError:
    # Fallback for older Flask-SQLAlchemy versions
    from flask.ext.sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    """Attach database to Flask app using Docker Compose PostgreSQL"""

    # Database credentials from environment or defaults
    DB_USER = os.environ.get("POSTGRES_USER", "airflow")
    DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "airflow")
    DB_NAME = os.environ.get("POSTGRES_DB", "airflow")
    DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    DB_PORT = os.environ.get("POSTGRES_PORT", "5433")

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    return db
