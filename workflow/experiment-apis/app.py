from flask import Flask, jsonify, request
from flasgger import Swagger
import yaml
import os, json, datetime
from jinja2 import Environment, FileSystemLoader
from flask_migrate import Migrate
from db import init_db, db
from db.models import Dag, Task
from pathlib import Path

app = Flask(__name__)
init_db(app)
migrate = Migrate(app, db)

# Swagger config → serve docs at "/"
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,   # include all endpoints
            "model_filter": lambda tag: True,   # include all models
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/" 
}

swagger = Swagger(app, config=swagger_config)

# Load templates config once at startup
with open("templates_config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Map user-friendly display_name -> path
TEMPLATES = {t["display_name"]: t["path"] for t in config["templates"]}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DAG_TEMPLATE_DIR = BASE_DIR       # same directory
OUTPUT_DIR = "/tmp/dags_user"  # Use /tmp which is always writable
os.makedirs(OUTPUT_DIR, exist_ok=True)

env = Environment(loader=FileSystemLoader(DAG_TEMPLATE_DIR))
TEMPLATE_FILE = "dag_template.yaml.j2"

def load_json_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template JSON not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


@app.route("/experiments", methods=["GET"])
def list_templates():
    """
    List available templates
    ---
    responses:
      200:
        description: List of available templates
        examples:
          application/json: 
            [
              {"name": "Kubernetes Node Config"},
              {"name": "Kubernetes Pod Config"}
            ]
    """
    return jsonify([{"name": name} for name in TEMPLATES.keys()])


def apply_overrides_to_block(block, override_block):
    """
    Apply overrides to a single block (action/probe) in method or rollbacks
    """
    # For action → provider → arguments
    if block.get("type") == "action":
        args = block.get("provider", {}).get("arguments", {})
        override_args = override_block.get("arguments", {})
        for k, v in override_args.items():
            if k in args:
                args[k] = v
        block["provider"]["arguments"] = args
        # Optionally override action name
        if "name" in override_block:
            block["name"] = override_block["name"]

    # For probe → provider
    elif block.get("type") == "probe":
        if "provider" in override_block:
            block["provider"] = override_block["provider"]
        if "name" in override_block:
            block["name"] = override_block["name"]

    return block


@app.route("/generate", methods=["POST"])
def generate_json():
    """
    Generate JSON from template with dynamic overrides
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - template_name
          properties:
            template_name:
              type: string
              description: User-friendly template name from templates_config.yaml
            overrides:
              type: object
              description: Key-value pairs to override in the JSON
              example:
                method:
                  - name: "apply-database-memory-stress"
                    arguments:
                      name: "vatsalya"
                      label_selectors: "app=testing"
                  - name: "wait-for-memory-stress-duration"
                    provider:
                      type: "process"
                      path: "hello_world"
                rollbacks:
                  - name: "cleanup-database-memory-stress"
                    arguments:
                      name: "vatsalya hello"
    responses:
      200:
        description: Generated JSON and saved file path
      400:
        description: Invalid template name
      500:
        description: Error in processing template
    """
    data = request.get_json()
    template_name = data.get("template_name")
    overrides = data.get("overrides", {})

    if template_name not in TEMPLATES:
        return jsonify({
            "error": f"Invalid template name. Available: {list(TEMPLATES.keys())}"
        }), 400

    # Load base template
    base_json = load_json_file(TEMPLATES[template_name])

    # Apply overrides to all method blocks
    method_overrides = overrides.get("method", [])
    for idx, step in enumerate(base_json.get("method", [])):
        for ovr in method_overrides:
            if ovr.get("name") == step.get("name"):
                base_json["method"][idx] = apply_overrides_to_block(step, ovr)

    # Apply overrides to all rollback blocks
    rollback_overrides = overrides.get("rollbacks", [])
    for idx, step in enumerate(base_json.get("rollbacks", [])):
        for ovr in rollback_overrides:
            if ovr.get("name") == step.get("name"):
                base_json["rollbacks"][idx] = apply_overrides_to_block(step, ovr)

    # Save new JSON in the same folder as original template
    original_path = TEMPLATES[template_name]
    folder = os.path.dirname(original_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    base_file_name = os.path.splitext(os.path.basename(original_path))[0]
    new_file_name = f"{base_file_name}_generated_{timestamp}.json"
    new_file_path = os.path.join(folder, new_file_name)

    with open(new_file_path, "w") as f:
        json.dump(base_json, f, indent=4)

    return jsonify({
        "message": "JSON generated successfully",
        "file_path": new_file_path,
        "generated_json": base_json
    })


@app.route("/generate-user-task", methods=["POST"])
def generate_user_task():
    """
    Generate a user-specific Chaos experiment task from a template.
    ---
    tags:
      - Task Management
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - dag_id
            - task_name
            - template_name
          properties:
            dag_id:
              type: integer
              example: 1
            task_name:
              type: string
              example: apply-pod-memory-stress
            template_name:
              type: string
              example: pod_memory_stress_rollback
            overrides:
              type: object
              properties:
                method:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                        example: apply-database-memory-stress
                      arguments:
                        type: object
                        example:
                          name: vatsalya
                          label_selectors: app=testing
                rollbacks:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                        example: cleanup-database-memory-stress
                      arguments:
                        type: object
                        example:
                          name: rollback-memory
    responses:
      201:
        description: Task generated and saved successfully
      400:
        description: Missing required fields or invalid input
      404:
        description: DAG not found
      500:
        description: Server error
    """
    try:
        data = request.get_json()

        dag_id = data.get("dag_id")
        task_name = data.get("task_name")
        template_name = data.get("template_name")
        overrides = data.get("overrides", {})

        # --- Validation ---
        if not dag_id or not task_name or not template_name:
            return jsonify({"error": "Fields 'dag_id', 'task_name', and 'template_name' are required"}), 400

        dag = Dag.query.get(dag_id)
        if not dag:
            return jsonify({"error": f"DAG with id {dag_id} not found"}), 404

        if template_name not in TEMPLATES:
            return jsonify({"error": f"Invalid template name. Available: {list(TEMPLATES.keys())}"}), 400

        # --- Load base template ---
        base_json = load_json_file(TEMPLATES[template_name])

        # --- Apply overrides ---
        method_overrides = overrides.get("method", [])
        for idx, step in enumerate(base_json.get("method", [])):
            for ovr in method_overrides:
                if ovr.get("name") == step.get("name"):
                    base_json["method"][idx] = apply_overrides_to_block(step, ovr)

        rollback_overrides = overrides.get("rollbacks", [])
        for idx, step in enumerate(base_json.get("rollbacks", [])):
            for ovr in rollback_overrides:
                if ovr.get("name") == step.get("name"):
                    base_json["rollbacks"][idx] = apply_overrides_to_block(step, ovr)

        # --- Save modified JSON ---
    #    folder = os.path.dirname(TEMPLATES[template_name])
   #     timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
      #  base_file_name = Path(TEMPLATES[template_name]).stem
      #  new_file_name = f"{base_file_name}_{task_name}_{timestamp}.json"
       # new_file_path = os.path.join(folder, new_file_name)

     #   with open(new_file_path, "w") as f:
     #       json.dump(base_json, f, indent=4)

        # --- Save to DB ---
        new_task = Task(
            dag_id=dag_id,
            task_name=task_name,
            task_json=base_json,
       #     file_path=new_file_path
        )
        db.session.add(new_task)
        db.session.commit()

        return jsonify({
            "message": "Task generated and saved successfully",
            "task": new_task.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/tasks/<int:dag_id>", methods=["GET"])
def get_tasks_by_dag(dag_id):
    """
    Get all tasks for a specific DAG.
    ---
    tags:
      - Task Management
    parameters:
      - name: dag_id
        in: path
        type: integer
        required: true
        description: ID of the DAG to fetch tasks for
    responses:
      200:
        description: List of tasks for the DAG
        schema:
          type: array
          items:
            type: object
            properties:
              task_id:
                type: integer
              dag_id:
                type: integer
              task_name:
                type: string
              task_json:
                type: object
              file_path:
                type: string
              created_at:
                type: string
      404:
        description: DAG not found
      500:
        description: Server error
    """
    try:
        dag = Dag.query.get(dag_id)
        if not dag:
            return jsonify({"error": f"DAG with id {dag_id} not found"}), 404

        tasks = [task.to_dict() for task in dag.tasks]

        return jsonify({
            "dag_id": dag_id,
            "dag_name": dag.dag_name,
            "tasks": tasks
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/template/params", methods=["GET"])
def get_template_params():
    """
    Get dynamic parameters available in a template
    ---
    parameters:
      - name: template_name
        in: query
        type: string
        required: true
        description: User-friendly template name (from templates_config.yaml)
    responses:
      200:
        description: List of overridable keys
    """
    template_name = request.args.get("template_name")
    if not template_name:
        return jsonify({"error": "Missing template_name"}), 400

    # Validate against config
    if template_name not in TEMPLATES:
        return jsonify({"error": f"Invalid template name. Available: {list(TEMPLATES.keys())}"}), 400

    # Load JSON from resolved path
    try:
        base_json = load_json_file(TEMPLATES[template_name])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    dynamic_fields = {
        "method": [],
        "rollbacks": []
    }

    # Extract from "method"
    for step in base_json.get("method", []):
        if step.get("type") == "action":
            args = step.get("provider", {}).get("arguments", {})
            dynamic_fields["method"].append({
                "name": step.get("name"),
                "type": "action",
                "keys": list(args.keys())
            })
        elif step.get("type") == "probe":
            provider = step.get("provider", {})
            keys = list(provider.keys()) if isinstance(provider, dict) else ["provider"]
            dynamic_fields["method"].append({
                "name": step.get("name"),
                "type": "probe",
                "keys": keys
            })

    # Extract from "rollbacks"
    for step in base_json.get("rollbacks", []):
        if step.get("type") == "action":
            args = step.get("provider", {}).get("arguments", {})
            dynamic_fields["rollbacks"].append({
                "name": step.get("name"),
                "type": "action",
                "keys": list(args.keys())
            })
        elif step.get("type") == "probe":
            provider = step.get("provider", {})
            keys = list(provider.keys()) if isinstance(provider, dict) else ["provider"]
            dynamic_fields["rollbacks"].append({
                "name": step.get("name"),
                "type": "probe",
                "keys": keys
            })

    # Reorder each block to have 'name' and 'type' first
    for section in ["method", "rollbacks"]:
        for i, block in enumerate(dynamic_fields[section]):
            reordered = {"name": block["name"], "type": block["type"], "keys": block["keys"]}
            dynamic_fields[section][i] = reordered

    return jsonify(dynamic_fields)
    


def apply_overrides_to_task(task, override):
    """Apply overrides to a task dictionary"""
    task_copy = task.copy()
    for k, v in override.items():
        task_copy[k] = v
    return task_copy



@app.route("/generate_dag", methods=["POST"])
def generate_dag():
    """
    Generate DAG YAML from provided task list (with optional dependencies).
    Expects POST body like:
    {
      "dag_id": "chaos_node_dag",
      "tasks": [
        {
          "task_id": "taskA",
          "json_file": "container_restart.json",
          "dependencies": []
        },
        {
          "task_id": "taskB",
          "json_file": "cpu_stress_ng.json",
          "dependencies": ["taskA"]
        }
      ]
    }
    """
    data = request.get_json()
    dag_id = data.get("dag_id")
    tasks = data.get("tasks", [])

    if not dag_id or not tasks:
        return jsonify({"error": "dag_id and tasks are required"}), 400

    # Ensure dependencies field exists for each task
    for t in tasks:
        t.setdefault("dependencies", [])

    # Render Jinja template
    template = env.get_template(TEMPLATE_FILE)
    dag_yaml = template.render(dag_id=dag_id, tasks=tasks)

    # Save YAML output
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    safe_dag_file = f"{dag_id}_generated_{timestamp}.yaml"
    dag_file_path = os.path.join(OUTPUT_DIR, safe_dag_file)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(dag_file_path, "w") as f:
        f.write(dag_yaml)

    return jsonify({
        "message": "DAG YAML generated successfully",
        "file_path": dag_file_path,
        "dag_yaml": dag_yaml
    }), 200

@app.route("/generate-user-dag", methods=["POST"])
def generate_user_dag():
    """
    Generate DAG YAML from task list and save to database
    ---
    tags:
      - DAG Management
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - dag_save_id
            - dag_id
            - tasks
          properties:
            dag_save_id:
              type: integer
              description: The database ID of the DAG record to save YAML into
              example: 1
            dag_id:
              type: string
              description: Logical DAG identifier
              example: chaos_node_dag
            tasks:
              type: array
              description: List of tasks with optional dependencies
              items:
                type: object
                properties:
                  task_id:
                    type: string
                    example: taskA
                  json_file:
                    type: string
                    example: container_restart.json
                  dependencies:
                    type: array
                    items:
                      type: string
                    example: []
    responses:
      201:
        description: DAG YAML generated and saved successfully
      400:
        description: Missing required fields
      404:
        description: DAG record not found
      500:
        description: Server error
    """
    try:
        data = request.get_json()
        dag_save_id = data.get("dag_save_id")
        dag_id = data.get("dag_id")
        tasks = data.get("tasks", [])

        if not dag_save_id or not dag_id or not tasks:
            return jsonify({"error": "Fields 'dag_save_id', 'dag_id', and 'tasks' are required"}), 400

        # Ensure DAG record exists
        dag = Dag.query.get(dag_save_id)
        if not dag:
            return jsonify({"error": f"DAG record with id {dag_save_id} not found"}), 404

        # Ensure each task has dependencies field
        for t in tasks:
            t.setdefault("dependencies", [])

        # Render Jinja template
        template = env.get_template(TEMPLATE_FILE)
        dag_yaml_content = template.render(dag_id=dag_id, tasks=tasks)

        # Save YAML to file
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        safe_file_name = f"dag_{dag_id}_{timestamp}.yaml"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        file_path = os.path.join(OUTPUT_DIR, safe_file_name)
        with open(file_path, "w") as f:
            f.write(dag_yaml_content)

        # Save YAML in JSONB format in database
        dag.dag_yaml = json.loads(json.dumps({
            "dag_id": dag_id,
            "tasks": tasks,
            "yaml": dag_yaml_content
        }))
        dag.file_path = file_path
        db.session.commit()

        return jsonify({
            "message": "DAG YAML generated and saved successfully",
            "dag_save_id": dag_save_id,
            "dag_id": dag_id,
            "file_path": file_path,
            "dag_yaml": dag_yaml_content
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@app.route('/create-dag-id', methods=['POST'])
def create_dag():
    """
    Create a new DAG record with just dag_name.
    ---
    tags:
      - DAG Management
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            dag_name:
              type: string
              example: chaos_node_dag
    responses:
      201:
        description: DAG created successfully
      400:
        description: Missing dag_name
      500:
        description: Database error
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be in JSON format"}), 400

        data = request.get_json()
        dag_name = data.get("dag_name")

        if not dag_name or not dag_name.strip():
            return jsonify({"error": "Missing required field 'dag_name'"}), 400

        existing_dag = Dag.query.filter_by(dag_name=dag_name).first()
        if existing_dag:
            return jsonify({"error": f"DAG with name '{dag_name}' already exists"}), 400

        new_dag = Dag(dag_name=dag_name.strip())
        db.session.add(new_dag)
        db.session.commit()

        return jsonify({
            "message": "DAG created successfully",
            "dag": new_dag.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/dags', methods=['GET'])
def get_all_dags():
    """
    Get all DAGs
    ---
    tags:
      - DAG Management
    responses:
      200:
        description: List of all DAGs
    """
    try:
        dags = Dag.query.all()
        return jsonify({
            "dags": [dag.to_dict() for dag in dags]
        }), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/dags/<int:dag_id>', methods=['GET'])
def get_dag_by_id(dag_id):
    """
    Get DAG information by ID
    ---
    tags:
      - DAG Management
    parameters:
      - name: dag_id
        in: path
        type: integer
        required: true
        description: ID of the DAG to retrieve
    responses:
      200:
        description: DAG information
      404:
        description: DAG not found
    """
    try:
        dag = Dag.query.get(dag_id)
        if not dag:
            return jsonify({"error": f"DAG with id {dag_id} not found"}), 404

        return jsonify({"dag": dag.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/dags/<int:dag_id>/yaml', methods=['GET'])
def get_dag_yaml_only(dag_id):
    """
    Get only the YAML string of a DAG by DAG ID
    ---
    tags:
      - DAG Management
    parameters:
      - name: dag_id
        in: path
        type: integer
        required: true
        description: ID of the DAG whose YAML content is to be retrieved
    responses:
      200:
        description: DAG YAML string
        schema:
          type: object
          properties:
            dag_id:
              type: integer
            dag_name:
              type: string
            yaml:
              type: string
      404:
        description: DAG not found
      500:
        description: Database error
    """
    try:
        dag = Dag.query.get(dag_id)
        if not dag:
            return jsonify({"error": f"DAG with id {dag_id} not found"}), 404

        yaml_content = dag.dag_yaml.get("yaml") if dag.dag_yaml else None

        return jsonify({
            "dag_id": dag.dag_id,
            "dag_name": dag.dag_name,
            "yaml": yaml_content
        }), 200

    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
