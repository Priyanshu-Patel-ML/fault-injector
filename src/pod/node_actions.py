import subprocess
import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def load_kubernetes_config():
    """Load Kubernetes configuration"""
    try:
        config.load_incluster_config()
        print("✅ Loaded in-cluster Kubernetes config")
    except:
        try:
            config.load_kube_config()
            print("✅ Loaded local Kubernetes config")
        except:
            raise Exception("❌ Failed to load Kubernetes configuration")

def cordon_node(label_selector=None, name=None):
    """Cordon nodes to make them unschedulable"""
    load_kubernetes_config()
    v1 = client.CoreV1Api()
    
    try:
        if label_selector:
            nodes = v1.list_node(label_selector=label_selector)
            print(f"Found {len(nodes.items)} nodes with label selector: {label_selector}")
        elif name:
            nodes = v1.list_node(field_selector=f"metadata.name={name}")
            print(f"Found node: {name}")
        else:
            raise ValueError("Either label_selector or name must be provided")
        
        cordoned_nodes = []
        for node in nodes.items:
            node_name = node.metadata.name
            print(f"Cordoning node: {node_name}")
            
            # Patch node to set unschedulable=true
            body = {"spec": {"unschedulable": True}}
            v1.patch_node(name=node_name, body=body)
            cordoned_nodes.append(node_name)
            print(f"✅ Successfully cordoned node: {node_name}")
        
        return {"cordoned_nodes": cordoned_nodes}
        
    except ApiException as e:
        print(f"❌ Kubernetes API error: {e}")
        raise
    except Exception as e:
        print(f"❌ Error cordoning nodes: {e}")
        raise

def uncordon_node(label_selector=None, name=None):
    """Uncordon nodes to make them schedulable again"""
    load_kubernetes_config()
    v1 = client.CoreV1Api()
    
    try:
        if label_selector:
            nodes = v1.list_node(label_selector=label_selector)
            print(f"Found {len(nodes.items)} nodes with label selector: {label_selector}")
        elif name:
            nodes = v1.list_node(field_selector=f"metadata.name={name}")
            print(f"Found node: {name}")
        else:
            raise ValueError("Either label_selector or name must be provided")
        
        uncordoned_nodes = []
        for node in nodes.items:
            node_name = node.metadata.name
            print(f"Uncordoning node: {node_name}")
            
            # Patch node to set unschedulable=false
            body = {"spec": {"unschedulable": False}}
            v1.patch_node(name=node_name, body=body)
            uncordoned_nodes.append(node_name)
            print(f"✅ Successfully uncordoned node: {node_name}")
        
        return {"uncordoned_nodes": uncordoned_nodes}
        
    except ApiException as e:
        print(f"❌ Kubernetes API error: {e}")
        raise
    except Exception as e:
        print(f"❌ Error uncordoning nodes: {e}")
        raise