import os
import re

import folder_paths
import yaml
from aiohttp import web
from server import PromptServer

dir = os.path.abspath(os.path.join(__file__, "../../user"))
if not os.path.exists(dir):
    os.mkdir(dir)
file = os.path.join(dir, "autocomplete.txt")
second_file = os.path.join(dir, "wildcards_autocomplete.txt")
files = {"autocomplete": None, "wildcards_autocomplete": None}

# region wildcard autocmplt gen
wildcards_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "ComfyUI-Impact-Pack", "wildcards")
)
autocomplete_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "user", "wildcards_autocomplete.txt"))

wildcard_dict = {}


def wildcard_normalize(x):
    return x.replace("\\", "/").replace(" ", "-").lower()


def read_wildcard(k, v):
    if isinstance(v, list):
        k = wildcard_normalize(k)
        wildcard_dict[k] = v
    elif isinstance(v, dict):
        for k2, v2 in v.items():
            new_key = f"{k}/{k2}"
            new_key = wildcard_normalize(new_key)
            read_wildcard(new_key, v2)
    elif isinstance(v, (str, int, float)):
        k = wildcard_normalize(k)
        wildcard_dict[k] = [str(v)]


def read_wildcard_dict(wildcard_path):
    for root, dirs, files in os.walk(wildcard_path, followlinks=True):
        for file in files:
            file_path = os.path.join(root, file)

            # Process TXT files
            if file.endswith(".txt"):
                rel_path = os.path.relpath(file_path, wildcard_path)
                key = wildcard_normalize(os.path.splitext(rel_path)[0])

                try:
                    # Try multiple encodings
                    for encoding in ["utf-8", "ISO-8859-1", "cp1252"]:
                        try:
                            with open(file_path, "r", encoding=encoding) as f:
                                lines = [
                                    x.strip()
                                    for x in f.read().splitlines()
                                    if x.strip() and not x.strip().startswith("#")
                                ]
                            if lines:
                                wildcard_dict[key] = lines
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Fallback to error-tolerant reading
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = [
                                x.strip() for x in f.read().splitlines() if x.strip() and not x.strip().startswith("#")
                            ]
                        if lines:
                            wildcard_dict[key] = lines
                            print(f"Loaded {file_path} with errors ignored")
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue

            # Process YAML files
            elif file.endswith(".yaml") or file.endswith(".yml"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        yaml_data = yaml.load(f, Loader=yaml.FullLoader)
                    for k, v in (yaml_data or {}).items():
                        read_wildcard(k, v)
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue


def generate_autocomplete_file():
    # Get all wildcard entries as __key__ format
    wildcard_list = [f"__{k}__" for k in wildcard_dict.keys()]

    # Sort alphabetically
    wildcard_list.sort()

    # Write to autocomplete file
    with open(autocomplete_path, "w", encoding="utf-8") as f:
        f.write("\n".join(wildcard_list))

    print(f"Generated wildcards_autocomplete.txt with {len(wildcard_list)} entries")


# endregion


@PromptServer.instance.routes.post("/pysssss/generate-wildcards")
async def generate_wildcards(request):
    try:
        wildcard_dict.clear()
        read_wildcard_dict(wildcards_path)
        generate_autocomplete_file()
        return web.json_response({"status": "success", "count": len(wildcard_dict)})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


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
