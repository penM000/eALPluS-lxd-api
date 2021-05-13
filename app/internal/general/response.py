def make_response_dict(
    status: bool = True,
    details: str = "success",
    assign_port: int = 0,
    assign_ip: str = "",
    option=""
):
    return {
        "status": status,
        "details": details,
        "assign_port": assign_port,
        "assign_ip": assign_ip,
        "option": option
    }
