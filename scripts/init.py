#!/usr/bin/env python3
"""Initialize a NEW Ubuntu/amd64 deployment with host PostgreSQL and Synapse."""
import argparse
import ipaddress
import os
import secrets
import subprocess
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("server_ip", help="Stable public IPv4 address; immutable Matrix server name")
args = parser.parse_args()
ip = str(ipaddress.IPv4Address(args.server_ip))
if os.geteuid() != 0:
    parser.error("Run as root on the deployment server.")
state = ROOT / "state/synapse"
if state.exists():
    parser.error("state/synapse already exists. Refusing to overwrite keys or an existing installation.")
compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
image = compose["services"]["synapse"]["image"]

def sql(statement):
    return subprocess.check_output([
        "runuser", "-u", "postgres", "--", "psql", "-X",
        "-v", "ON_ERROR_STOP=1", "-At", "-c", statement
    ], cwd="/tmp", text=True).strip()

if sql("SELECT 1 FROM pg_roles WHERE rolname='friends_chat'") or sql(
    "SELECT 1 FROM pg_database WHERE datname='friends_chat'"
):
    parser.error("PostgreSQL role/database friends_chat exists; refusing to change credentials.")
subprocess.run(["docker", "image", "inspect", image], check=True, stdout=subprocess.DEVNULL)
(ROOT / "state").mkdir(mode=0o700, exist_ok=True)
os.chmod(ROOT / "state", 0o700)
state.mkdir()
subprocess.run([
    "docker", "run", "--rm", "--pull=never", "--platform=linux/amd64",
    "-v", f"{state}:/data", "-e", f"SYNAPSE_SERVER_NAME={ip}",
    "-e", "SYNAPSE_REPORT_STATS=no", image, "generate"
], check=True)
password = secrets.token_hex(32)
# Input goes through stdin, so the database password is not a process argument.
subprocess.run([
    "runuser", "-u", "postgres", "--", "psql", "-X", "-v", "ON_ERROR_STOP=1"
], input="CREATE ROLE friends_chat LOGIN PASSWORD '" + password + "';\n",
    cwd="/tmp", text=True, stdout=subprocess.DEVNULL, check=True)
subprocess.run([
    "runuser", "-u", "postgres", "--", "createdb", "--encoding=UTF8",
    "--locale=C", "--template=template0", "--owner=friends_chat", "friends_chat"
], cwd="/tmp", check=True)
p = state / "homeserver.yaml"
config = yaml.safe_load(p.read_text())
config["database"] = {"name": "psycopg2", "args": {
    "user": "friends_chat", "password": password, "dbname": "friends_chat",
    "host": "127.0.0.1", "port": 5432, "cp_min": 1, "cp_max": 5}}
config["listeners"] = [{
    "port": 8008, "type": "http", "tls": False,
    "bind_addresses": ["127.0.0.1"], "x_forwarded": True,
    "resources": [{"names": ["client"], "compress": False}]}]
config.update(
    public_baseurl=f"https://{ip}/", enable_registration=False,
    allow_guest_access=False, enable_media_repo=False,
    url_preview_enabled=False, federation_domain_whitelist=[],
    encryption_enabled_by_default_for_room_type="all", enable_metrics=False)
# Retain generated registration_shared_secret for local operator account creation.
p.write_text(yaml.safe_dump(config, sort_keys=False))
p.chmod(0o600)
print("Initialized. Secrets are only in ignored state/. Service is not started yet.")
print("If initialization failed partway, inspect state and database; do not delete keys blindly.")
