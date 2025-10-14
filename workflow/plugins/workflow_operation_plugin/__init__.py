# workflow_operation_plugin/__init__.py

from airflow.plugins_manager import AirflowPlugin

from workflow_operation_plugin.routes import api_bp  # ✅ fixed import
 
class WorkflowOperationPlugin(AirflowPlugin):

    name = "workflow_operation_plugin"

    flask_blueprints = [api_bp]

 