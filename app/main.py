from fastapi import FastAPI
from starlette.responses import RedirectResponse

from .routers.apis import lxd
from .routers.html import html


app = FastAPI()

app.include_router(lxd.router)
app.include_router(html.router)


@app.get("/")
async def redirect():
    #url = app.url_path_for("docs")

    response = RedirectResponse(
        url="https://ealplus.shinshu-u.ac.jp/connection")
    return response


@app.get("/fast")
async def fast():
    return None
