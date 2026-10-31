# Friends Chat

[简体中文](README.md) · [English](README.en.md)

A self-hosted text chat deployment kit for small groups of friends, built on **Matrix, Synapse and Element Web**. Friends open an HTTPS page and sign in; they do not need Docker or a private network client.

> This project provides deployment configuration and operational scripts for existing open-source software. It is not an independently developed chat client or a new encryption algorithm. It is an early-stage project without a security audit or a completed two-device E2EE and key recovery acceptance test.

## Features and scope

- Matrix / Element provide direct messages, small groups and offline message synchronization.
- Locally created rooms default to end-to-end encryption. Clients handle keys, encryption, decryption and device verification.
- Public registration and guest access are disabled. The server operator creates accounts with a script.
- Synapse's media repository is disabled for text-focused use. Some attachment or call buttons may remain visible in the unmodified upstream Element UI.
- No federation endpoint is exposed; the outbound federation allowlist is empty.
- Public IPv4 HTTPS is supported without requiring a domain. IP certificates require reliable automatic renewal.
- Synapse is limited to 1 GiB RAM and 1 CPU, with Docker log rotation. Host PostgreSQL and other services are outside these limits.

## Architecture and encryption

```text
Browser A (Element: plaintext → encryption)
                 │ HTTPS + encrypted events
                 ▼
        Nginx :443 → Synapse 127.0.0.1:8008
                              │
                    PostgreSQL 127.0.0.1:5432
                 │ HTTPS + encrypted events
                 ▼
Browser B (Element: ciphertext → decryption)
```

The classic Matrix E2EE stack uses **Olm** for encrypted device-to-device sessions and room-key distribution, and **Megolm** for room message encryption. Upstream clients and SDKs own the implementation and protocol evolution. The account login password is not the message decryption key. HTTPS protects the transport; E2EE protects message content.

Servers generally cannot decrypt correctly encrypted messages, but can observe metadata such as accounts, room membership, connection IPs and timing. Do not assume room names or other state are end-to-end encrypted. A compromised web server can deliver malicious JavaScript that steals keys or plaintext; a compromised endpoint also defeats this protection. See [SECURITY.md](SECURITY.md) and the [official Matrix encryption guide](https://matrix.org/docs/matrix-concepts/end-to-end-encryption/).

## Validation status

| Item | Status |
| --- | --- |
| Prototype Synapse startup and PostgreSQL connectivity | Verified |
| Prototype HTTPS page and Matrix versions endpoint | Verified |
| Prototype certificate issuance, renewal timer and Nginx reload hook | Configured; an actual automatic renewal cycle has not been observed |
| Prototype local backup archive readability | Checked; not a complete restore test |
| Full redeployment of this repository on a fresh server | Not yet verified |
| Two independent devices/accounts: encrypted exchange, verification and key recovery | Not yet completed |
| Load testing and security audit | Not yet completed |

This table is not a security certification or a production readiness guarantee.

## Requirements

- A **fresh test environment**: Ubuntu 24.04 LTS, x86_64/amd64 and Python 3.12. ARM servers and other distributions are not currently supported by these scripts.
- Docker Engine and the Compose plugin: [official installation guide](https://docs.docker.com/engine/install/ubuntu/).
- PostgreSQL listening only on loopback, with local TCP password authentication. Scripts use Ubuntu's postgres system account.
- A stable public IPv4 and inbound cloud firewall access on TCP 80/443. Do not expose 5432/8008; manage SSH separately.
- Access to GHCR, GitHub Releases and the certificate authority. Trusted-computer transfer is an alternative when downloads fail.
- 2 vCPU / 4 GB RAM is a starting point for small tests, not a load-tested capacity claim. Other host applications reduce available resources.

Matrix's `server_name` cannot simply be changed after initialization. If an IP changes, updating the website and certificate does not migrate account identities. Choose a stable identity and plan migrations before long-term use. IP access does not replace applicable hosting-provider or deployment requirements.

## Deploy on a fresh server

**Do not run `init.py` on an existing chat server or overwrite live configuration with this repository.** This is a sanitized deployment starting point, not a backup of a running instance.

### 1. Install dependencies and get the project

Install Docker / Compose following Docker's official guide, then run:

```bash
sudo apt update
sudo apt install -y postgresql nginx python3-yaml curl git
sudo systemctl enable --now postgresql nginx
sudo git clone https://github.com/linshangjun71/friends-chat_in.git /opt/friends-chat
cd /opt/friends-chat
```

Replace the documentation IP below with your actual public IPv4. The variable applies only to the current shell.

```bash
CHAT_IP=203.0.113.10
sudo docker pull --platform linux/amd64 ghcr.io/element-hq/synapse@sha256:3c2900775df229b91ae0f21f2c98070e0da48d4e135a9c5b567b029be57fdb56
sudo python3 scripts/init.py "$CHAT_IP"
sudo docker compose up -d
curl --max-time 10 http://127.0.0.1:8008/_matrix/client/versions
```

The image is pinned to the prototype's release digest; this does not mean it remains current or vulnerability-free. Review upstream security advisories, back up and test before upgrades. `init.py` creates a dedicated `friends_chat` database and role and generates a password inside ignored `state/`. It refuses to overwrite existing state or a same-named database/role. If initialization fails partway, inspect state instead of blindly deleting keys.

### 2. Prepare Element Web

Obtain the release archive from [Element's official releases](https://github.com/element-hq/element-web/releases). The example pins the prototype version, `v1.12.33`; review upstream updates and advisories before deployment.

```bash
curl -fL --retry 2 \
  https://github.com/element-hq/element-web/releases/download/v1.12.33/element-v1.12.33.tar.gz \
  -o /tmp/element-v1.12.33.tar.gz
sudo python3 scripts/prepare-web.py /tmp/element-v1.12.33.tar.gz "$CHAT_IP"
```

The destination must be empty to avoid mixing old and new assets. Do not use untrusted mirrors or disable TLS verification. See [docs/offline-transfer.md](docs/offline-transfer.md) for transferring downloads from a trusted computer.

### 3. Configure the HTTP certificate challenge

```bash
sudo mkdir -p /var/www/friends-chat-acme/.well-known/acme-challenge
sed "s/__SERVER_IP__/$CHAT_IP/g" templates/nginx-acme.conf | sudo tee /etc/nginx/sites-available/friends-chat >/dev/null
sudo ln -s /etc/nginx/sites-available/friends-chat /etc/nginx/sites-enabled/friends-chat
sudo nginx -t && sudo systemctl reload nginx
```

Inspect and back up existing site files before replacing them; do not overwrite another application. The challenge path must be reachable publicly on port 80.

### 4. Obtain an IP certificate and enable HTTPS

Use Certbot 5.4+ with IP support. For example, install the official Snap and check the version:

```bash
sudo snap install --classic certbot
/snap/bin/certbot --version
sudo /snap/bin/certbot certonly \
  --preferred-profile shortlived --webroot \
  -w /var/www/friends-chat-acme \
  --ip-address "$CHAT_IP" --cert-name friends-chat
```

Read and decide whether to accept the certificate authority's agreement and email options interactively. IP certificates are short-lived; see [Let's Encrypt's official instructions](https://letsencrypt.org/2026/03/11/shorter-certs-certbot). After successful issuance:

```bash
sed "s/__SERVER_IP__/$CHAT_IP/g" templates/nginx-https.conf | sudo tee /etc/nginx/sites-available/friends-chat >/dev/null
sudo nginx -t && sudo systemctl reload nginx
sudo install -m 755 templates/renew-nginx.sh /etc/letsencrypt/renewal-hooks/deploy/friends-chat-nginx
sudo systemctl list-timers --all | grep certbot
sudo /snap/bin/certbot renew --dry-run --run-deploy-hooks
curl --max-time 15 "https://$CHAT_IP/_matrix/client/versions"
```

Verify both the renewal simulation and reload hook. Do not substitute `curl -k` or bypass a browser certificate warning for fixing TLS. Keep the challenge endpoint reachable and monitor expiry and renewal failures; installing Certbot does not remove operational responsibility.

### 5. Create accounts and chat

```bash
sudo bash scripts/add-user.sh admin
sudo bash scripts/add-user.sh friend
```

Passwords are entered twice interactively without visible characters. `Passwords do not match` means the entries differ; rerun the command. The script creates ordinary chat accounts. The username `admin` does not grant server administrator privileges.

Open `https://your-public-ip/`, choose a language and sign in. Invite another local account to a direct message or private group. The welcome screen may still show a create-account button, but server-side public registration is disabled. Save your recovery key and verify additional devices. A password reset does not recover lost message keys.

## Operations

```bash
sudo docker compose ps
sudo docker compose logs --tail=60 synapse
sudo bash scripts/backup.sh
```

Backups go to `/var/backups/friends-chat/` and include the database, configuration and server signing keys. **Never publish them to GitHub.** The script does not automatically remove backups, schedule jobs or configure off-server storage. Operators must choose a schedule, storage limits and protected off-server copies. Preserve the actual Nginx and certificate configuration separately. A local backup is not disaster recovery or a replacement for users' recovery keys. Perform a restore drill in an isolated environment before relying on backups.

Before use, test two accounts/devices, room encryption status, device verification, offline sync, recovery-key restoration, certificate renewal and backup restoration. This project does not claim that all these checks have passed.

## Repository layout

```text
compose.yaml                  # Pinned image, resource limits, host networking
.env.example                  # Reference variables; not automatically loaded
scripts/init.py               # Fresh-instance initialization; secrets go in state/
scripts/prepare-web.py        # Extract upstream client and set the default server
scripts/add-user.sh           # Interactive ordinary-account creation
scripts/backup.sh             # Manual local backup
templates/nginx-*.conf        # ACME and HTTPS reverse-proxy templates
templates/renew-nginx.sh       # Reload Nginx after renewal
SECURITY.md                   # Threat boundaries and vulnerability reporting
THIRD_PARTY.md                # Upstream components and license scope
```

This repository contains no live server IP, cloud account information, real passwords, user data, signing keys or TLS private keys. Do not publish a running server directory. `.gitignore` cannot prevent manually uploading secret files through GitHub's website.

## License and contributing

Original scripts, templates and documentation are [MIT-licensed](LICENSE). Upstream components retain their own licenses; MIT does not cover Synapse, Element or modifications to those projects. See [THIRD_PARTY.md](THIRD_PARTY.md). Issues and PRs with sanitized reproduction steps, compatibility improvements and documentation fixes are welcome. Handle private data and security reports according to [SECURITY.md](SECURITY.md).
