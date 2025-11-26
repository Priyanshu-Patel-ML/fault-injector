import time

import requests

from datetime import datetime
 
def set_linger_delay(api_url: str = "http://52.234.237.145:8080/v1/fault_gen/app-fault/KAKFA_FAULT_LINGER/set"):

    """

    Calls the API to activate Kafka linger fault.

    No payload is required.

    """

    print(f"Calling API")
 
    try:

        response = requests.put(api_url, timeout=10)

        response.raise_for_status()
 
        print("Kafka linger fault successfully activated.")

        print("Sleeping for 300 secs")

        time.sleep(300)

 
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
 
 
def reset_linger_delay(api_url: str = "http://52.234.237.145:8080/v1/fault_gen/app-fault/KAKFA_FAULT_LINGER/reset"):

    """

    Calls the API to reset Kafka linger fault.

    If authentication is required, use admin/admin.

    """

    print(f"Calling API to reset Kafka linger fault")
 
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
 
 
