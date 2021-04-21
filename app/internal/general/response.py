def make_response_dict(
    status: bool = True,
    details: str = "success",
    assign_port: int = 0,
    option=""
):
    return {
        "status": status,
        "details": details,
        "assign_port": assign_port,
        "option": option
    }
