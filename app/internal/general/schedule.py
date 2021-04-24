from typing import List, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler


# スケジューラー
Schedule = AsyncIOScheduler()
Schedule.start()


def add_schedule(_id, func, delay) -> bool:
    if delay < 5:
        delay = 5
    try:
        Schedule.add_job(
            lambda: func,
            trigger='interval',
            seconds=delay,
            id=_id
        )
    except BaseException:
        return False
    return True


def remove_schedule(_id) -> bool:
    try:
        Schedule.remove_job(_id)
    except BaseException:
        return False
    return True


def get_all_schedule() -> List[Dict[str:str]]:
    schedules = []
    for job in Schedule.get_jobs():
        schedules.append(
            {
                "Name": str(job.id),
                "Run Frequency": str(job.trigger),
                "Next Run": str(job.next_run_time)
            }
        )
    return schedules
