import requests
 
 
def set_linger_delay(api_url: str = "http://48.194.77.240:8080/v1/fault_gen/app-fault/KAKFA_FAULT_LINGER/set"):

    """

    Calls the API to activate Kafka linger fault.

    No payload is required.

    """

    try:

        response = requests.put(api_url, timeout=10)

        response.raise_for_status()

        return {

            "status": "success",

            "message": "Kafka linger fault set"

        }

    except Exception as e:

        return {

            "status": "failed",

            "error": str(e)

        }
 
 
def inject_linger_delay(api_url: str, payload: dict, token: str, number_of_request: int = 1):

    headers = {

        "Authorization": f"Bearer {token}",

        "Content-Type": "application/json"

    }
 
    results = []
 
    for i in range(number_of_request):

        try:

            response = requests.post(api_url, json=payload, headers=headers, timeout=10)

            response.raise_for_status()
 
            results.append({

                "request": i + 1,

                "status": "success",

                "response": response.text

            })

        except Exception as e:

            results.append({

                "request": i + 1,

                "status": "failed",

                "error": str(e)

            })
 
    return {

        "total_requests": number_of_request,

        "results": results

    }
 
 
def reset_linger_delay(api_url: str = "http://48.194.77.240:8080/v1/fault_gen/app-fault/KAKFA_FAULT_LINGER/reset"):

    """

    Calls the API to reset Kafka linger fault.

    If authentication is required, use admin/admin.

    """

    try:

        response = requests.put(api_url, timeout=10)

        response.raise_for_status()

        return {

            "status": "success",

            "message": "Kafka linger fault reset"

        }

    except Exception as e:

        return {

            "status": "failed",

            "error": str(e)

        }

 
