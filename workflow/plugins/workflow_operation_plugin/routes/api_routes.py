from flask import Blueprint, jsonify, request
import os
import yaml

# FIXED: Changed blueprint name from "api_bp" to "workflow_api"
api_bp = Blueprint("workflow_api", __name__, url_prefix="/myapi")

@api_bp.route("/base_operations", methods=["GET"])
def list_base_operations():
    """Get all base operation templates from templates_config.yaml"""
    try:
        TEMPLATE_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../templates_config.yaml")
        with open(TEMPLATE_CONFIG_PATH, "r") as f:
            templates = yaml.safe_load(f)
        return jsonify(templates), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "plugin": "workflow_operation_plugin"})

@api_bp.route("/workflows", methods=["GET"])
def list_workflows():
    return jsonify({"workflows": []})

@api_bp.route("/operations", methods=["GET"])
def list_operations():
    return jsonify({"operations": []})

@api_bp.route("/workflows", methods=["POST"])
def create_workflow():
    data = request.get_json()
    return jsonify({"message": "Workflow created", "data": data}), 201

@api_bp.route("/operations", methods=["POST"])
def create_operation():
    data = request.get_json()
    return jsonify({"message": "Operation created", "data": data}), 201
