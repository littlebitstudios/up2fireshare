import argparse
import os
from pathlib import Path
import requests
import xxhash
import yaml


_VIDEO_EXTENSIONS = {".mp4", ".m4v", ".mov", ".webm"}
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_HASH_BYTES = 16 * 1024 * 1024


def _default_config_path():
    return Path.home() / ".littlebitstudios" / "up2fireshare" / "config.yaml"


def load_config(config_path=None):
    config_file = Path(config_path).expanduser() if config_path else _default_config_path()

    if not config_file.exists():
        raise FileNotFoundError(f"Copy the example-config.yaml file from the repository to {config_file.parent}.\nRename the file to config.yaml and fill in the values for your Fireshare server.\nMake sure you specified --config if not using a config file in the default location.")

    with config_file.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    if not isinstance(config, dict):
        raise ValueError("The config file must contain a YAML mapping.")

    server = config.get("server")
    token = config.get("token")
    if not server or not token:
        raise KeyError("The config file must contain both 'server' and 'token'.")

    return {"server": str(server).rstrip("/"), "token": str(token)}


def _media_id(file_path):
    extension = Path(file_path).suffix.lower()
    if extension in _VIDEO_EXTENSIONS:
        field = "video_id"
    elif extension in _IMAGE_EXTENSIONS:
        field = "image_id"
    else:
        return None

    hasher = xxhash.xxh3_128()
    with open(file_path, "rb") as handle:
        hasher.update(handle.read(_HASH_BYTES))
    return field, hasher.hexdigest()


def upload_file(file_path, server, token, *, title=None, folder=None, game=None, tags=None):
    file_name = Path(file_path).name
    server_url = str(server).rstrip("/")
    upload_url = f"{server_url}/api/upload/token"
    payload = {}

    if title is not None:
        payload["title"] = str(title)
    if folder is not None:
        payload["folder"] = str(folder)
    if game is not None:
        payload["game"] = str(game)
    if tags is not None:
        payload["tag_ids"] = str(tags).strip()

    media_id = _media_id(file_path)
    if media_id is not None:
        id_field, file_id = media_id
        exists_response = requests.get(
            f"{server_url}/api/upload/token/exists",
            params={id_field: file_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        exists_response.raise_for_status()
        exists_result = exists_response.json()
        if exists_result.get("exists") is True:
            return exists_result

    with open(file_path, "rb") as handle:
        response = requests.post(
            upload_url,
            files={"file": (file_name, handle, "application/octet-stream")},
            data=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )

    try:
        return response.json()
    except ValueError:
        return {"status_code": response.status_code, "text": response.text}
    
def get_user_data(server, token):
    response = requests.get(f"{server}/api/upload/token", headers={"Authorization": f"Bearer {token}"})
    
    try:
        return response.json()
    except ValueError:
        return {"status_code": response.status_code, "text": response.text}


def _expand_input_files(paths, recursive=False):
    uploads = []

    for input_path in paths:
        path = Path(input_path).expanduser()
        if path.is_dir():
            candidates = path.rglob("*") if recursive else path.iterdir()
            for file_path in sorted(candidate for candidate in candidates if candidate.is_file()):
                default_folder = file_path.parent.name if recursive else path.name
                uploads.append((str(file_path), default_folder))
        else:
            uploads.append((str(path), None))

    return uploads


def main():
    parser = argparse.ArgumentParser(
        description="Upload one or more files or folders to a Fireshare instance."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="File(s) or folder(s) to upload. Whether Fireshare treats each file as video or photo depends on extension.",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="When given a folder, also upload files in its subfolders.",
    )
    parser.add_argument(
        "--name",
        "-n",
        help="Title of the upload in Fireshare. Defaults to the filename (without extension).",
    )
    parser.add_argument(
        "--tags",
        "-t",
        help="Tags to apply to uploaded clip(s), comma-separated.",
    )
    parser.add_argument(
        "--folder",
        "-f",
        help="Folder on your Fireshare server. Defaults to the provided folder's name, or the server's upload folder for files.",
    )
    parser.add_argument(
        "--game",
        "-g",
        help="Game name to assign to uploaded clip(s), case insensitive. Game must exist on your server already.",
    )
    parser.add_argument(
        "--config",
        help="Path to the YAML config file. Defaults to ~/.littlebitstudios/up2fireshare/config.yaml.",
    )

    args = parser.parse_args()
    uploads = _expand_input_files(args.files, recursive=args.recursive)
    if args.name is not None and len(uploads) > 1:
        parser.error("the title option (-n/--name) can only be used with a single file")
    if not uploads:
        print("No files found to upload.")
        return 1

    try:
        config = load_config(args.config)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1
    except (KeyError, ValueError) as exc:
        print(f"Invalid config: {exc}")
        return 1
    
    user_data=get_user_data(config.get("server"), config.get("token"))
    if user_data:
        print(f"connected to {config.get("server")} as user {user_data.get("username")}\n")

    normalized_tags = None
    if args.tags:
        normalized_tags = ",".join(part.strip() for part in args.tags.split(",") if part.strip())

    for file_path, default_folder in uploads:
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return 1

        result = upload_file(
            file_path,
            config["server"],
            config["token"],
            title=args.name,
            folder=args.folder if args.folder is not None else default_folder,
            game=args.game,
            tags=normalized_tags,
        )

        if isinstance(result, dict):
            status = (
                "already exists"
                if result.get("exists") is True
                else result.get("status") or result.get("status_code")
            )
            print(f"{os.path.basename(file_path)} -> {status}")
            if result.get("message"):
                print(result["message"])
            if result.get("error"):
                print(result["error"])
            if result.get("url"):
                print(f"view item here: {config.get("server")}{result.get("url")}")
            else:
                print(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
