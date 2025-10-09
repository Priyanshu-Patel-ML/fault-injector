#!/usr/bin/env python3
import chaosk6_actions
 
print("=== Starting Load Test with Auto Cleanup ===")
 
# 1. Count posts before
print("\n1. Counting posts before load test...")
result = chaosk6_actions.count_posts_direct(db_host="172.179.55.194")
print(f"Posts before: {result['total_posts']}")
 
# 2. Run load test
print("\n2. Running load test...")
success = chaosk6_actions.stress_endpoint(
    endpoint="http://4.154.253.199:8080/api/post/compose",
    vus=500,
    duration="180s",
    username="jagan",
    password="maplelabs",
    method="POST",
    body="post_type=0&text=Load_Test_Auto_Cleanup"
)
print(f"Load test success: {success}")
 
# 3. Count posts after
print("\n3. Counting posts after load test...")
result = chaosk6_actions.count_posts_direct(db_host="172.179.55.194")
print(f"Posts after load test: {result['total_posts']}")
 
# 4. Cleanup
print("\n4. Cleaning up old posts...")
result = chaosk6_actions.cleanup_database_direct(
    db_host="172.179.55.194",
    keep_count=10000,
    dry_run=False
)
print(f"Cleanup result: {result}")
 
# 5. Final count
print("\n5. Final post count...")
result = chaosk6_actions.count_posts_direct(db_host="172.179.55.194")
print(f"Final posts: {result['total_posts']}")
 
print("\n=== Load Test with Auto Cleanup Complete ===")