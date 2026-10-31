# Upstream components / 上游组件

Friends Chat is deployment glue for existing software. This repository does not vendor or redistribute Synapse, Element Web, PostgreSQL, Nginx, Docker, or Certbot binaries/source. The MIT license in this repository covers only its original scripts, templates and documentation; it does not relicense upstream components.

| Component | Purpose | Source / licensing information |
| --- | --- | --- |
| Matrix | Messaging protocol and E2EE specification | https://spec.matrix.org/ |
| Synapse | Homeserver; server-side storage and sync | https://github.com/element-hq/synapse |
| Element Web | Browser UI and Matrix encryption implementation | https://github.com/element-hq/element-web |
| PostgreSQL | Database | https://www.postgresql.org/about/licence/ |
| Nginx | HTTPS and reverse proxy | https://nginx.org/en/LICENSE |
| Docker Engine / Compose | Container runtime and orchestration | https://github.com/moby/moby / https://github.com/docker/compose |
| Certbot | Certificate issuance and renewal | https://github.com/certbot/certbot |

Use the exact upstream release's license and notices when modifying or distributing upstream components. Consult upstream requirements, including applicable source availability obligations; do not label a modified upstream client as wholly MIT-licensed.

本仓库只提供部署脚本、配置模板和文档，未将上游软件重新授权。修改或分发上游代码、客户端或镜像时，应保留对应版本的许可证、版权及通知，并履行其适用义务。
