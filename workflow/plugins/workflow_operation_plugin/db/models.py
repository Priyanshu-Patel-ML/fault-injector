import datetime
from workflow_operation_plugin.db import db
from sqlalchemy.dialects.postgresql import JSONB
 
# ---------------------------------------------------
# Association Table: workflow ↔ operations (many-to-many)
# ---------------------------------------------------
workflow_operation_map = db.Table(
    "workflow_operation_map",
    db.Column("workflow_id", db.Integer, db.ForeignKey("workflows.workflow_id"), primary_key=True),
    db.Column("operation_id", db.Integer, db.ForeignKey("operations.operation_id"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.datetime.utcnow),
    extend_existing=True
)
 
# ---------------------------------------------------
# Workflow Model (previously DAG)
# ---------------------------------------------------
class Workflow(db.Model):
    __tablename__ = "workflows"
    __table_args__ = {'extend_existing': True}

    workflow_id = db.Column(db.Integer, primary_key=True)
    workflow_name = db.Column(db.String(255), unique=True, nullable=False)
    workflow_yaml = db.Column(JSONB, nullable=True)     # YAML (or equivalent) stored as JSONB
    file_path = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    operations = db.relationship(
        "Operation",
        secondary=workflow_operation_map,
        back_populates="workflows",
        cascade="all"
    )

    def to_dict(self, include_operations=False):
        data = {
            "workflow_id": self.workflow_id,
            "workflow_yaml": self.workflow_yaml,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat(),
        }
        if include_operations:
            data["operations"] = [op.to_dict() for op in self.operations]
        return data
 
 
# ---------------------------------------------------
# Operation Model (previously Experiment)
# ---------------------------------------------------
class Operation(db.Model):
    __tablename__ = "operations"
    __table_args__ = {'extend_existing': True}

    operation_id = db.Column(db.Integer, primary_key=True)
    operation_name = db.Column(db.String(255), nullable=False, unique=True)
    operation_json = db.Column(JSONB, nullable=True)
    file_path = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    workflows = db.relationship(
        "Workflow",
        secondary=workflow_operation_map,
        back_populates="operations"
    )

    def to_dict(self):
        return {
            "operation_id": self.operation_id,
            "operation_name": self.operation_name,
            "operation_json": self.operation_json,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat()
        }
 
