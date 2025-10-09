import subprocess
import time

NAMESPACE = "default"
DEPLOYMENT_NAME = "user-mongodb"

def get_mongodb_pod_name():
    """Get the current MongoDB pod name dynamically"""
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", NAMESPACE, "-l", "app=user-mongodb", "-o", "jsonpath={.items[0].metadata.name}"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Failed to get pod name: {e}")
        return None


def update_mongodb_max_connections(new_max_connections: int):
    """Update the ConfigMap and rollout restart deployment"""
    print(f"Updating MongoDB maxIncomingConnections to {new_max_connections}...")

    configmap_yaml = f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-mongodb
  namespace: {NAMESPACE}
data:
  mongod.conf: |
    net:
      tls:
        mode: disabled
      maxIncomingConnections: {new_max_connections}
"""

    tmp_file = "/tmp/updated-mongodb-configmap.yaml"
    with open(tmp_file, "w") as f:
        f.write(configmap_yaml)

    try:
        subprocess.run(["kubectl", "apply", "-f", tmp_file], check=True)
        print("ConfigMap updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to apply ConfigMap: {e}")
        return False

    try:
        subprocess.run(["kubectl", "rollout", "restart", f"deployment/{DEPLOYMENT_NAME}", "-n", NAMESPACE], check=True)
        print("Deployment restart initiated")
        subprocess.run(["kubectl", "rollout", "status", f"deployment/{DEPLOYMENT_NAME}", "-n", NAMESPACE, "--timeout=120s"], check=True)
        print("Deployment rolled out successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart deployment: {e}")
        return False

    time.sleep(10)  # Wait for pod readiness
    return True


def rollback_mongodb_max_connections():
    """Rollback ConfigMap to original (without maxIncomingConnections)"""
    print("Rolling back MongoDB configuration...")
    original_config = f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-mongodb
  namespace: {NAMESPACE}
data:
  mongod.conf: |
    net:
      tls:
        mode: disabled
"""

    tmp_file = "/tmp/original-mongodb-configmap.yaml"
    with open(tmp_file, "w") as f:
        f.write(original_config)

    try:
        subprocess.run(["kubectl", "apply", "-f", tmp_file], check=True)
        subprocess.run(["kubectl", "rollout", "restart", f"deployment/{DEPLOYMENT_NAME}", "-n", NAMESPACE], check=True)
        subprocess.run(["kubectl", "rollout", "status", f"deployment/{DEPLOYMENT_NAME}", "-n", NAMESPACE, "--timeout=120s"], check=True)
        print("Rollback successful")
        time.sleep(10)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Rollback failed: {e}")
        return False


def exec_mongo_command(mongo_command):
    """Executes a mongo shell command inside the MongoDB pod"""
    pod_name = get_mongodb_pod_name()
    if not pod_name:
        print("Cannot find MongoDB pod")
        return None

    cmd = ["kubectl", "exec", "-n", NAMESPACE, pod_name, "--", "mongo", "--eval", mongo_command]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout
    else:
        print(f"Mongo command failed: {result.stderr}")
        return None
