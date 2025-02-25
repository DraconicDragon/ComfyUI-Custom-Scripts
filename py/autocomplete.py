import os

import folder_paths
from aiohttp import web
from server import PromptServer

dir = os.path.abspath(os.path.join(__file__, "../../user"))
if not os.path.exists(dir):
    os.mkdir(dir)
file = os.path.join(dir, "autocomplete.txt")
second_file = os.path.join(dir, "wildcards_autocomplete.txt")
files = {"autocomplete": None, "wildcards_autocomplete": None}


@PromptServer.instance.routes.get("/pysssss/autocomplete")
async def get_autocomplete(request):

    if os.path.isfile(file):
        with open(file, "r", encoding="utf-8") as f:
            files["autocomplete"] = f.read()

    # Add second file
    if os.path.isfile(second_file):
        with open(second_file, "r", encoding="utf-8") as f:
            files["wildcards_autocomplete"] = f.read()

    if any(files.values()):
        return web.json_response(files)
    return web.Response(status=404)


@PromptServer.instance.routes.post("/pysssss/autocomplete")
async def update_autocomplete(request):
    with open(file, "w", encoding="utf-8") as f:
        f.write(await request.text())
    return web.Response(status=200)


@PromptServer.instance.routes.get("/pysssss/loras")
async def get_loras(request):
    loras = folder_paths.get_filename_list("loras")
    return web.json_response(list(map(lambda a: os.path.splitext(a)[0], loras)))
