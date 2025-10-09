# db/models.py
import datetime
from . import db
from sqlalchemy.dialects.postgresql import JSONB

class Dag(db.Model):
    __tablename__ = "dags"

    dag_id = db.Column(db.Integer, primary_key=True)
    dag_name = db.Column(db.String(255), nullable=False)
    dag_yaml = db.Column(JSONB, nullable=True)     # store YAML as JSONB
    file_path = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationship: one DAG can have multiple tasks
    tasks = db.relationship('Task', backref='dag', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "dag_id": self.dag_id,
            "dag_name": self.dag_name,
            "dag_yaml": self.dag_yaml,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat(),
            "tasks": [task.to_dict() for task in self.tasks]  # include related tasks
        }


class Task(db.Model):
    __tablename__ = "tasks"

    task_id = db.Column(db.Integer, primary_key=True)
    dag_id = db.Column(db.Integer, db.ForeignKey('dags.dag_id'), nullable=False)
    task_name = db.Column(db.String(255), nullable=False)
    task_json = db.Column(JSONB, nullable=True)    # store Chaos experiment JSON
    file_path = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "dag_id": self.dag_id,
            "task_name": self.task_name,
            "task_json": self.task_json,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat()
        }
