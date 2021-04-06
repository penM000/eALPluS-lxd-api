from fastapi import Depends, FastAPI
from starlette.responses import RedirectResponse

from .routers.apis import lxd


app = FastAPI()

app.include_router(lxd.router)




@app.get("/")
async def redirect():
    #url = app.url_path_for("docs")
    response = RedirectResponse(url="/docs")
    return response