# 可信电脑中转 / Trusted-computer transfer

## Synapse image

On a trusted computer with Docker running (including Apple silicon Macs), download the server's **amd64** variant. Keep the platform flag on export as well:

```bash
docker pull --platform linux/amd64 ghcr.io/element-hq/synapse@sha256:3c2900775df229b91ae0f21f2c98070e0da48d4e135a9c5b567b029be57fdb56
docker tag ghcr.io/element-hq/synapse@sha256:3c2900775df229b91ae0f21f2c98070e0da48d4e135a9c5b567b029be57fdb56 friends-chat-synapse:transfer
docker save --platform linux/amd64 -o synapse-amd64.tar friends-chat-synapse:transfer
gzip synapse-amd64.tar
```

Upload through authenticated SSH/SCP or the cloud provider's authenticated file manager. Do not enable root password login just to transfer a file. Compare SHA-256 checksums on both ends (`shasum -a 256 FILE` on macOS, `sha256sum FILE` on Ubuntu).

```bash
sudo docker load -i synapse-amd64.tar.gz
sudo docker image inspect friends-chat-synapse:transfer --format '{{.Os}}/{{.Architecture}}'
```

Expected: `linux/amd64`. An imported archive may not retain the upstream repository digest reference. After verifying the transfer, set `services.synapse.image` in the server's local `compose.yaml` to the local image ID returned by `docker image inspect friends-chat-synapse:transfer --format '{{.Id}}'`. `init.py` reads that Compose value and does not pull images.

中文：Mac 下载时与导出时都要指定 `linux/amd64`。上传后校验 SHA-256 并导入。离线导入可能不保留远端摘要引用，可在服务器本地 Compose 中填写导入镜像的完整 ID；不要把尚未完成的压缩包当作成功导出。确认导入后可清理中转文件和电脑上的临时 Docker 安装，不要清理服务器运行所需的数据。

## Element Web

Download the official release archive on the trusted computer, transfer it, compare checksums and run `scripts/prepare-web.py` on the server. Never upload an archive containing your browser profile or server credentials. Matching transfer checksums detect transfer errors; they do not independently establish upstream authenticity.

中文：从 Element 官方发布页下载客户端发布包，再上传服务器。两端哈希一致只验证传输未变化，不替代对下载来源及上游签名的验证。
