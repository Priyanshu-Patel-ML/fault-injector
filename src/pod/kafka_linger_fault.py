import time

import requests
 
 
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
 
 
def inject_linger_delay(api_url: str, payload: dict, token: str):

    main_check_url = "http://48.194.82.60:3000/api/booking/bookings"
 
    headers = {

        "Authorization": f"Bearer {token}",

        "Content-Type": "application/json"

    }
 
    # -----------------------------------------------------------

    # 1️⃣ STEP 1 — Get initial count of bookings

    # -----------------------------------------------------------

    try:

        initial_res = requests.get(main_check_url, headers=headers, timeout=10)

        initial_res.raise_for_status()

        initial_bookings = initial_res.json()

        initial_count = len(initial_bookings)

        print(f"Initial booking count: {initial_count}")

    except Exception as e:

        return {

            "status": "failed",

            "error": f"Failed to fetch initial bookings: {str(e)}",

            "logs": logs

        }
 
    # -----------------------------------------------------------

    # 2️⃣ STEP 2 — Trigger the CREATE BOOKING API

    # -----------------------------------------------------------

    # try:

    create_res = requests.post(api_url, json=payload, headers=headers, timeout=10)

    create_res.raise_for_status()

    print("Create booking triggered successfully.")

    # except Exception as e:

    #     print(f"Failed Create Booking")

    #     return {

    #         "status": "failed",

    #         "error": f"Create booking failed: {str(e)}",

    #         "logs": logs

    #     }
 
    # -----------------------------------------------------------

    # 3️⃣ STEP 3 — Poll every 2 sec until count increases OR timeout 60 sec

    # -----------------------------------------------------------

    start_time = time.time()

    new_count = initial_count
 
    print("Waiting for booking count to increase...")
 
    while time.time() - start_time < 60:

        try:

            current_res = requests.get(main_check_url, headers=headers, timeout=10)

            current_res.raise_for_status()

            current_bookings = current_res.json()

            new_count = len(current_bookings)
 
            if new_count > initial_count:

                print(f"Booking count increased from {initial_count} to {new_count}")

                print("Success for new booking")

                return {

                    "status": "success",

                    "message": "Booking successfully created and confirmed by count change.",

                    "initial_count": initial_count,

                    "final_count": new_count,

                    "logs": logs

                }
 
        except Exception as e:

            logs.append(f"Error while polling: {str(e)}")
 
        time.sleep(2)
 
    # -----------------------------------------------------------

    # 4️⃣ STEP 4 — Timeout

    # -----------------------------------------------------------

    print("Timeout: booking count did not increase within 60 seconds.")
 
    return {

        "status": "timeout",

        "message": "Booking creation triggered but count did not increase.",

        "initial_count": initial_count,

        "final_count": new_count,

        "logs": logs

    }
 
 
 
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
 
 
