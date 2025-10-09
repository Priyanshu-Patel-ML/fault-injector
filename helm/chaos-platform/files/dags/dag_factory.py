# load_chaos_yaml_dags.py
from dagfactory import load_yaml_dags

# Path to your YAML experiments (inside container)
yaml_folder = "/opt/airflow/src/pod"

# Automatically load all YAML files in the folder as DAGs
load_yaml_dags(globals(), dags_folder=yaml_folder)
