# db/__init__.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import logging

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with Docker Postgres compatibility and auto-migration."""
    
    # Docker/Local PostgreSQL configuration
    DB_USER = os.environ.get("POSTGRES_USER", "airflow")
    DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "airflow") 
    DB_NAME = os.environ.get("POSTGRES_DB", "airflow")
    DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    DB_PORT = os.environ.get("POSTGRES_PORT", "5433")
    
    # Check if running in Docker/K8s environment
    is_containerized = os.environ.get("CONTAINER_ENV", "false").lower() == "true"
    
    if is_containerized:
        # Use internal service names for containerized environments
        DB_HOST = os.environ.get("POSTGRES_HOST", "postgres-postgresql.default.svc.cluster.local")
        DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
    
    # Build connection URI
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Remove SSL configuration for local Docker setup
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {
            "connect_timeout": 10,
        }
    }
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Auto-migration on startup
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            logging.info("✅ Database tables created/verified successfully")
            
            # Try to run migrations, but don't fail if there are none
            try:
                from flask_migrate import upgrade
                upgrade()
                logging.info("✅ Database migrations completed successfully")
            except Exception as migrate_error:
                logging.warning(f"⚠️ Migration warning (this is usually OK): {migrate_error}")
                # Don't fail the app if migrations have issues
            
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
            # Don't raise exception to allow app to start
    
    return db

def get_db_health():
    """Check database connection health."""
    try:
        db.session.execute('SELECT 1')
        return {"status": "healthy", "message": "Database connection OK"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database error: {str(e)}"}
