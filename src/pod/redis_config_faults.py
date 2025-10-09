import subprocess
import time

def redis_exec_command(pod_label, redis_command):
    """Executes a redis-cli command inside a pod matching the label."""
    pod_name_cmd = f"kubectl get pod -l app={pod_label} -o jsonpath='{{.items[0].metadata.name}}'"
    pod_name = subprocess.check_output(pod_name_cmd, shell=True, text=True).strip()

    full_cmd = f"kubectl exec {pod_name} -- redis-cli {redis_command}"
    output = subprocess.check_output(full_cmd, shell=True, text=True)
    print(f"[CMD] {redis_command} → {output.strip()}")
    return output.strip()


def redis_memory_stress_test(pod_label="user-timeline-redis", limit_in_kb=100,
                             eviction_policy="noeviction", duration=240):
    """Set Redis maxmemory and policy via kubectl exec for a duration."""
    redis_exec_command(pod_label, f"CONFIG SET maxmemory {limit_in_kb}kb")
    redis_exec_command(pod_label, f"CONFIG SET maxmemory-policy {eviction_policy}")

    print(f"[INFO] Set maxmemory={limit_in_kb}KB, policy={eviction_policy}")
    print(f"[INFO] Sleeping for {duration} seconds for stress effect...")
    time.sleep(duration)

    return reset_maxmemory(pod_label)


def reset_maxmemory(pod_label="user-timeline-redis"):
    """Reset Redis memory settings via kubectl exec."""
    redis_exec_command(pod_label, "CONFIG SET maxmemory 0")
    redis_exec_command(pod_label, "CONFIG SET maxmemory-policy noeviction")
    print("[INFO] Redis settings reset to default.")
    return {"status": "reset"}
