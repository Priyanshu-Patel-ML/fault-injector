from mongodb_actions import exec_mongo_command


def probe_max_connections(expected_connections: int = None) -> bool:
    """Probe MongoDB connections by querying serverStatus inside pod"""

    mongo_command = "db.serverStatus().connections"
    output = exec_mongo_command(mongo_command)
    if output is None:
        print("Failed to get serverStatus connections")
        return False

    # Output example parsing (very basic)
    import re
    try:
        current_match = re.search(r'"current" : (\d+)', output)
        available_match = re.search(r'"available" : (\d+)', output)
        current = int(current_match.group(1)) if current_match else None
        available = int(available_match.group(1)) if available_match else None
        print(f"Mongo connections - current: {current}, available: {available}")

        if expected_connections is not None and available is not None:
            if available < expected_connections:
                print(f"Available connections {available} < expected {expected_connections}")
                return False
        return True
    except Exception as e:
        print(f"Failed to parse serverStatus output: {e}")
        return False


def probe_runtime_parameters() -> bool:
    """Probe available runtime parameters"""

    mongo_command = "db.adminCommand({getParameter:'*'})"
    output = exec_mongo_command(mongo_command)
    if output is None:
        print("Failed to get parameters")
        return False
    print("Runtime parameters retrieved (raw output):")
    print(output)
    # For detailed parsing you can add JSON extraction here if desired
    return True
