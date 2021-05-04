from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ...internal.lxd.instance import get_all_instance
templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/html",
    responses={404: {"description": "Not found"}},
    tags=["html"],


)


@router.get("/controller/{class_id}", response_class=HTMLResponse)
async def read_item(request: Request, class_id: str):
    instances = await get_all_instance()
    instances_status = {}
    for instance in instances:
        if instance.name.startswith(class_id):
            memory = f'{int(instance.state().memory["usage"]/1024**2)}MB'
            disk = f'{int(instance.state().disk["root"]["usage"]/1024**2)}MB'
            status = {
                "status": instance.status,
                "memory": memory,
                "disk": disk}
            instances_status[instance.name] = status

    instances_status = dict(
        sorted(
            instances_status.items(),
            key=lambda x: x[0]))

    return templates.TemplateResponse(
        "controller.html", {
            "request": request,
            "class_id": class_id,
            "instances_status": instances_status
        }
    )
