from apscheduler.schedulers.asyncio import AsyncIOScheduler


# スケジューラー
Schedule = AsyncIOScheduler()
Schedule.start()


def make_response_dict(
    status=True,
    details="success",
    assign_port="",
    option=""
):
    return {
        "status": status,
        "details": details,
        "assign_port": assign_port,
        "option": option
    }


def add_stop_machine_schedule(machine_name, delay):
    from .lxd_machine import stop_machine
    if delay < 5:
        delay = 5
    try:
        Schedule.add_job(
            lambda: stop_machine(machine_name, call_from_scheduler=True),
            trigger='interval',
            seconds=delay,
            id=machine_name + "-stop-scheduled"
        )
    except BaseException:
        return make_response_dict(False, "existing_job")
    return make_response_dict()


def remove_stop_machine_schedule(machine_name):
    try:
        Schedule.remove_job(machine_name + "-stop-scheduled")
    except BaseException:
        return make_response_dict(False, "job_not_found")
    return make_response_dict()


def get_stop_machine_schedule():
    schedules = []
    for job in Schedule.get_jobs():
        schedules.append(
            {
                "Name": str(job.id),
                "Run Frequency": str(job.trigger),
                "Next Run": str(job.next_run_time)
            }
        )
    return make_response_dict(details=schedules)
