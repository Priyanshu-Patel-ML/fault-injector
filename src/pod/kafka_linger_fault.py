import time
import requests
from datetime import datetime
 
def set_linger_delay(api_url: str = "http://48.194.77.240:8080/v1/fault_gen/app-fault/KAKFA_FAULT_LINGER/set"):
    """
    Calls the API to activate Kafka linger fault.
    No payload is required.
    """
    print(f"Calling API: {api_url}")
 
    try:
        response = requests.put(api_url, timeout=10)
        response.raise_for_status()
 
        print("Kafka linger fault successfully activated.")
        time.sleep(300)
        print("Sleeping for 300 secs")
 
        return {
            "status": "success",
            "message": "Kafka linger fault set"
        }
 
    except Exception as e:
        print(f"Failed to set Kafka linger fault: {str(e)}")
 
        return {
            "status": "failed",
            "error": str(e)
        }
 
 
# def inject_linger_delay(api_url: str, payload: dict, token: str):
#     main_check_url = "http://48.194.82.60:3000/api/booking/bookings"
 
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }
 
#     # -----------------------------------------------------------
#     # 1️⃣ STEP 1 — Get initial count of bookings
#     # -----------------------------------------------------------
#     # try:
#     initial_res = requests.get(main_check_url, headers=headers)
#     initial_res.raise_for_status()
#     initial_bookings = initial_res.json()
#     initial_count = len(initial_bookings)
#     print(f"Initial booking count: {initial_count}")
#     # time.sleep(3)
#     # except Exception as e:
#     #     return {
#     #         "status": "failed",
#     #         "error": f"Failed to fetch initial bookings: {str(e)}",
#     #         "logs": logs
#     #     }
 
#     # -----------------------------------------------------------
#     # 2️⃣ STEP 2 — Trigger the CREATE BOOKING API
#     # -----------------------------------------------------------
#     try:
#         create_res = requests.post(api_url, json=payload, headers=headers)
#         create_res.raise_for_status()
#         # print("Create booking status:", create_res.status_code)
#         # print("Response headers:", create_res.headers)
#         # print("Response text:", create_res.text)
#         print("Create booking triggered successfully.")
#     except Exception as e:
#         # print("Status Code:", create_res.status_code)
#         # print("Response Text:", create_res.text)
#         print(f"Failed Create Booking")
#         return {
#             "status": "failed",
#             "error": f"Create booking failed: {str(e)}",
#             "logs": logs
#         }
 
#     # -----------------------------------------------------------
#     # 3️⃣ STEP 3 — Poll every 2 sec until count increases OR timeout 60 sec
#     # -----------------------------------------------------------
#     start_time = time.time()
#     new_count = initial_count
 
#     print("Waiting for booking count to increase...")
 
#     while time.time() - start_time < 60:
#         try:
#             poll_start = datetime.now() # timestamp right before calling GET
#             print(f"Poll start time: {poll_start.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
 
#             current_res = requests.get(main_check_url, headers=headers)
#             current_res.raise_for_status()
 
#             poll_end = time.time()  # timestamp right after GET completes
#             api_latency = poll_end - poll_start  # GET request latency
#             print(api_latency)
#             current_bookings = current_res.json()
#             new_count = len(current_bookings)
 
#             if new_count > initial_count:
#                 total_time = poll_end - start_time  # total time until count changed
 
#                 print(f"Booking count increased from {initial_count} to {new_count}")
#                 print(f"API latency for last GET: {api_latency} seconds")
#                 print(f"Total time taken for increase: {total_time} seconds")
 
#                 return {
#                     "status": "success",
#                     "message": "Booking successfully created and confirmed by count change.",
#                     "initial_count": initial_count,
#                     "final_count": new_count,
#                     "api_latency": api_latency,
#                     "total_time_taken": total_time,
#                     "logs": logs
#                 }
 
#         except Exception as e:
#             logs.append(f"Error while polling: {str(e)}")
 
#         time.sleep(2)
 
#     # -----------------------------------------------------------
#     # 4️⃣ STEP 4 — Timeout
#     # -----------------------------------------------------------
#     print("Timeout: booking count did not increase within 60 seconds.")
 
#     return {
#         "status": "timeout",
#         "message": "Booking creation triggered but count did not increase.",
#         "initial_count": initial_count,
#         "final_count": new_count,
#         "logs": logs
#     }
 
 
 
def reset_linger_delay(api_url: str = "http://48.194.77.240:8080/v1/fault_gen/app-fault/KAKFA_FAULT_LINGER/reset"):
    """
    Calls the API to reset Kafka linger fault.
    If authentication is required, use admin/admin.
    """
    print(f"Calling API to reset Kafka linger fault: {api_url}")
 
    try:
        response = requests.put(api_url, timeout=10)
        response.raise_for_status()
 
        print("Kafka linger fault reset successfully.")
 
        return {
            "status": "success",
            "message": "Kafka linger fault reset"
        }
 
    except Exception as e:
        print(f"Failed to reset Kafka linger fault: {str(e)}")
 
        return {
            "status": "failed",
            "error": str(e)
        }
