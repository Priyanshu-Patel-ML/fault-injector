import subprocess
import os
from pathlib import Path
import requests
from logzero import logger
from typing import Optional
import json
from pymongo import MongoClient

__all__ = [
    "stress_endpoint", 
    "stress_continuous_multi_endpoint",
    "count_posts_direct", 
    "cleanup_database_direct",
    "stress_endpoint_test"
]

def stress_endpoint_test():
    """Test function"""
    print("Hello world")
    return

def _run_process_and_wait(cmd, env=None, stdout_to_file: Optional[str] = None, debug: bool = False) -> bool:
    logger.debug("Running command: %s", " ".join(cmd))
    if env is None:
        env = os.environ.copy()
    try:
        if stdout_to_file:
            with open(stdout_to_file, "w") as fh:
                proc = subprocess.Popen(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT)
                rc = proc.wait()
        else:
            proc = subprocess.Popen(cmd, env=env, stdout=(None if debug else subprocess.PIPE), stderr=subprocess.STDOUT)
            out, _ = proc.communicate()
            if debug and out:
                logger.debug("Process output: %s", out.decode(errors="ignore") if isinstance(out, (bytes, bytearray)) else out)
            rc = proc.returncode
        logger.debug("Process finished with rc=%s", rc)
        return rc == 0
    except Exception as e:
        logger.exception("Error running process: %s", e)
        return False

def stress_endpoint(endpoint: str, vus: int = 1, duration: str = "10s",
                    username: str = None, password: str = None,
                    log_file: str = "k6_output.log", summary_file: str = "k6_summary.json",
                    debug: bool = False,
                    method: str = "GET", body: str = None,
                    headers: Optional[dict] = None):
    """
    Stress a single endpoint using k6 and JWT login.
    Captures k6 summary (requests, avg, p95, errors, etc.)
    """

    env = dict(os.environ)

    # Login for JWT token
    if username and password:
        login_url = "http://4.154.253.199:8080/api/user/login"
        resp = requests.post(login_url, data={"username": username, "password": password}, allow_redirects=False)
        token = resp.cookies.get("login_token")
        if not token:
            logger.error("❌ Login failed, cannot get token")
            return False
        env["CHAOS_K6_LOGIN_TOKEN"] = token
        logger.info(f"✅ Obtained login_token (JWT): {token}")

    # Pass runtime config to k6
    env["CHAOS_K6_URL"] = endpoint
    env["CHAOS_K6_VUS"] = str(vus)
    env["CHAOS_K6_DURATION"] = str(duration)
    env["CHAOS_K6_METHOD"] = method.upper()
    if body:
        env["CHAOS_K6_BODY"] = body
    if headers:
        env["CHAOS_K6_HEADERS"] = json.dumps(headers)

    script_path = str(Path(__file__).parent / "scripts" / "single-endpoint.js")
    if not Path(script_path).exists():
        logger.error("k6 script not found at %s", script_path)
        return False

    # k6 command with summary export
    cmd = [
        "k6", "run",
        "--summary-export", summary_file,   # ✅ save machine-readable results
        "--vus", str(vus),
        "--duration", str(duration),
        script_path
    ]

    # Save stdout (raw logs + metrics) to a file
    success = _run_process_and_wait(cmd, env=env, stdout_to_file=log_file, debug=debug)

    if success:
        logger.info("✅ Stress test completed successfully")
        logger.info(f"📊 k6 summary saved to {summary_file}")
        try:
            with open(summary_file) as f:
                summary = json.load(f)
                http_reqs = summary["metrics"]["http_reqs"]["count"]
                avg_time = summary["metrics"]["http_req_duration"]["avg"]
                p95_time = summary["metrics"]["http_req_duration"]["p(95)"]
                logger.info(f"📈 Requests: {http_reqs}, Avg: {avg_time:.2f} ms, P95: {p95_time:.2f} ms")
        except Exception as e:
            logger.warning(f"⚠️ Could not parse summary file: {e}")
    else:
        logger.error("❌ Stress test failed")

    if log_file:
        logger.info(f"k6 full output logged to {log_file}")

    return success

def stress_continuous_multi_endpoint(endpoints: list, min_vus: int = 30, max_vus: int = 60,
                                   ramp_duration: str = "2m", steady_duration: str = "5m",
                                   username: str = None, password: str = None,
                                   log_file: str = "k6_continuous_load.log", 
                                   summary_file: str = "k6_continuous_summary.json",
                                   continuous: bool = True, debug: bool = False):
    """
    Continuous multi-endpoint load test with variable VUs using k6.
    """
    
    env = dict(os.environ)

    # Login for JWT token
    if username and password:
        login_url = "http://4.154.253.199:8080/api/user/login"
        resp = requests.post(login_url, data={"username": username, "password": password}, allow_redirects=False)
        token = resp.cookies.get("login_token")
        if not token:
            logger.error("❌ Login failed, cannot get token")
            return False
        env["CHAOS_K6_LOGIN_TOKEN"] = token
        logger.info(f"✅ Obtained login_token (JWT): {token}")

    # Pass configuration to k6 script
    env["CHAOS_K6_MIN_VUS"] = str(min_vus)
    env["CHAOS_K6_MAX_VUS"] = str(max_vus)
    env["CHAOS_K6_RAMP_DURATION"] = str(ramp_duration)
    env["CHAOS_K6_STEADY_DURATION"] = str(steady_duration)
    env["CHAOS_K6_ENDPOINTS"] = json.dumps(endpoints)

    script_path = str(Path(__file__).parent / "scripts" / "continuous-multi-endpoint.js")
    if not Path(script_path).exists():
        logger.error("k6 script not found at %s", script_path)
        return False

    # k6 command for continuous load
    cmd = [
        "k6", "run",
        "--summary-export", summary_file,
        script_path
    ]

    # Run continuous load test
    success = _run_process_and_wait(cmd, env=env, stdout_to_file=log_file, debug=debug)

    if success:
        logger.info("✅ Continuous load test started successfully")
        logger.info(f"📊 k6 summary will be saved to {summary_file}")
    else:
        logger.error("❌ Continuous load test failed to start")

    if log_file:
        logger.info(f"k6 continuous output logged to {log_file}")

    return success

# Database cleanup functions
def count_posts_direct(db_host: str, db_port: int = 27017, database_name: str = "post", collection_name: str = "post"):
    """Count posts directly via MongoDB connection"""
    try:
        client = MongoClient(f"mongodb://{db_host}:{db_port}/{database_name}", serverSelectionTimeoutMS=5000)
        collection = client[database_name][collection_name]
        total_count = collection.count_documents({})
        client.close()
        logger.info(f"📊 Total posts: {total_count}")
        return {"status": "success", "total_posts": total_count}
    except Exception as e:
        logger.error(f"Failed to count posts: {e}")
        return {"status": "error", "total_posts": -1, "message": str(e)}

def cleanup_database_direct(db_host: str, db_port: int = 27017, database_name: str = "post", 
                          collection_name: str = "post", keep_count: int = 10000, dry_run: bool = False):
    """Clean up database - keep only latest N records"""
    try:
        client = MongoClient(f"mongodb://{db_host}:{db_port}/{database_name}", serverSelectionTimeoutMS=5000)
        collection = client[database_name][collection_name]
        total_count = collection.count_documents({})
        logger.info(f"📊 Total posts before cleanup: {total_count}")
        
        if total_count <= keep_count:
            client.close()
            logger.info(f"✅ Only {total_count} posts, no cleanup needed")
            return {"status": "success", "posts_deleted": 0, "message": "No cleanup needed"}
        
        if dry_run:
            client.close()
            posts_to_delete = total_count - keep_count
            logger.info(f"🗑️ DRY RUN: Would delete {posts_to_delete} posts")
            return {"status": "success", "posts_deleted": 0, "dry_run": True}
        
        # Keep only latest N records
        latest_posts = list(collection.find().sort("_id", -1).limit(keep_count))
        if len(latest_posts) == keep_count:
            oldest_id = latest_posts[-1]["_id"]
            result = collection.delete_many({"_id": {"$lt": oldest_id}})
            deleted_count = result.deleted_count
        else:
            deleted_count = 0
        
        client.close()
        logger.info(f"✅ Deleted {deleted_count} posts")
        return {"status": "success", "posts_deleted": deleted_count}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"status": "error", "posts_deleted": 0, "message": str(e)}
