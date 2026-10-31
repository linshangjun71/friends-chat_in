#!/usr/bin/env python3
"""Extract a trusted Element release locally; write a single-server configuration."""
import argparse
import ipaddress
import json
import tarfile
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("archive", type=Path)
parser.add_argument("server_ip")
parser.add_argument("--destination", type=Path, default=Path("/var/www/friends-chat-web"))
args = parser.parse_args()
ip = str(ipaddress.IPv4Address(args.server_ip))
dest = args.destination.resolve()
if dest.exists() and any(dest.iterdir()):
    parser.error("Destination must be empty; stage upgrades separately.")
dest.mkdir(parents=True, exist_ok=True)
with tarfile.open(args.archive, "r:gz") as archive:
    # Python 3.12's data filter prevents escaping the extraction directory.
    archive.extractall(dest, filter="data")
children = list(dest.iterdir())
if len(children) != 1 or not children[0].is_dir():
    raise SystemExit("Expected one top-level Element release directory.")
release = children[0]
if not (release / "index.html").is_file():
    raise SystemExit("Element index.html missing.")
for child in release.iterdir():
    child.rename(dest / child.name)
release.rmdir()
config = {
    "default_server_config": {"m.homeserver": {
        "base_url": f"https://{ip}", "server_name": ip}},
    "disable_custom_urls": True,
    "disable_guests": True,
    "disable_3pid_login": True,
    "force_verification": True,
    "brand": "Friends Chat",
    "integrations_ui_url": "",
    "integrations_rest_url": "",
    "integrations_widgets_urls": [],
    "default_federate": False,
    "default_theme": "light",
    "room_directory": {"servers": [ip]},
    "element_call": {"disable": True},
    "show_labs_settings": False,
}
(dest / "config.json").write_text(json.dumps(config, indent=2) + "\n")
print(f"Element prepared at {dest}; enable HTTPS separately.")
