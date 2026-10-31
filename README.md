# Friends Chat

[简体中文](README.md) · [English](README.en.md)

面向朋友小群体的自托管文字聊天部署项目，基于 **Matrix + Synapse + Element Web**。朋友打开 HTTPS 网页、登录账号即可使用，无需安装 Docker 或连接私人网络。

> 这是现有开源组件的部署配置与运维脚本，不是独立开发的聊天客户端，也没有自行设计加密算法。项目处于早期阶段，尚未完成安全审计或双设备端到端加密、密钥恢复的完整验证。

## 功能与范围

- 私聊、小群和离线消息同步由 Matrix / Element 提供。
- 本机新建房间默认开启端到端加密；客户端负责密钥管理、加解密和设备验证。
- 关闭公众注册和游客访问，通过服务器脚本创建朋友账号。
- 禁用 Synapse 媒体仓库，定位为文字聊天；Element 的部分附件或通话按钮仍可能显示，本项目未修改上游界面。
- 不提供联邦入口；出站联邦白名单为空。
- 支持公网 IPv4 + HTTPS，不强制依赖域名。IP 证书需要可靠的自动续期。
- Synapse 设置 1GiB 内存、1 CPU 限额，Docker 日志轮转；这些限制不包含宿主机 PostgreSQL 等服务。

## 架构与加密

```text
浏览器 A（Element：明文 → 加密）
                 │ HTTPS + 加密事件
                 ▼
        Nginx :443 → Synapse 127.0.0.1:8008
                              │
                    PostgreSQL 127.0.0.1:5432
                 │ HTTPS + 加密事件
                 ▼
浏览器 B（Element：密文 → 解密）
```

Matrix 的经典加密体系使用 **Olm** 建立设备间加密会话并分发房间密钥，使用 **Megolm** 加密房间消息。具体实现和协议演进由上游客户端及 SDK 管理。登录密码用于账号认证，不等于消息解密密钥。HTTPS 与端到端加密分别保护网络连接和消息内容。

服务器通常无法解密正确加密的消息内容，但可以看到账号、房间成员、连接 IP 和时间等元数据。不要假设房间名称等状态信息被端到端加密。浏览器代码由服务器提供，服务器被攻破时，恶意网页代码可能窃取明文或密钥；设备失陷同样会破坏保护边界。详见 [SECURITY.md](SECURITY.md) 和 [官方加密说明](https://matrix.org/docs/matrix-concepts/end-to-end-encryption/)。

## 当前验证状态

| 项目 | 状态 |
| --- | --- |
| 原型 Synapse 启动、PostgreSQL 连接 | 已验证 |
| 原型 HTTPS 网页与 Matrix versions 接口 | 已验证 |
| 原型证书签发、续期定时器与 Nginx reload 钩子配置 | 已完成配置；实际自动续期周期尚未观察 |
| 原型本机备份文件可读性 | 已检查；不是完整恢复测试 |
| 仓库脚本在全新服务器上的完整重部署 | 尚未验证 |
| 两个独立设备/账号加密收发、交叉验证、密钥恢复 | 尚未完成 |
| 负载测试、安全审计 | 尚未完成 |

不要把这张表当作安全认证或生产可用性保证。

## 部署前提

- **全新测试环境**：Ubuntu 24.04 LTS、x86_64/amd64，Python 3.12。当前脚本不承诺支持 ARM 服务器或其他系统。
- 已安装 Docker Engine 与 Compose 插件：[官方安装文档](https://docs.docker.com/engine/install/ubuntu/)。
- PostgreSQL 只监听本机，且允许本机 TCP 密码认证；脚本使用 Ubuntu 的 postgres 系统账号。
- 稳定的公网 IPv4、云防火墙允许入站 TCP 80/443。不要开放 5432/8008，SSH 规则独立管理。
- 能访问 GHCR、GitHub Releases、证书机构；下载失败时可以可信电脑中转。
- 2 核 / 4GB 可以作为小规模测试起点，不是经过压测的容量承诺。宿主机其他应用会影响资源余量。

Matrix 的 `server_name` 初始化后不能直接更改。IP 改变时，更新网页地址和证书不足以迁移账号身份；长期使用前应选择稳定名称并规划迁移。IP 方案也不替代云服务商规则及适用的上线要求。

## 在新服务器上部署

**已在使用的聊天服务器不要运行 `init.py`，也不要用仓库覆盖真实配置。** 本仓库是脱敏的可复用部署起点，不是运行实例的备份。

### 1. 安装依赖并获取项目

先按 Docker 官方文档安装 Docker/Compose，再执行：

```bash
sudo apt update
sudo apt install -y postgresql nginx python3-yaml curl git
sudo systemctl enable --now postgresql nginx
sudo git clone https://github.com/linshangjun71/friends-chat_in.git /opt/friends-chat
cd /opt/friends-chat
```

下面的示例 IP 必须替换为你的真实公网 IPv4；变量仅在当前终端生效。

```bash
CHAT_IP=203.0.113.10
sudo docker pull --platform linux/amd64 ghcr.io/element-hq/synapse@sha256:3c2900775df229b91ae0f21f2c98070e0da48d4e135a9c5b567b029be57fdb56
sudo python3 scripts/init.py "$CHAT_IP"
sudo docker compose up -d
curl --max-time 10 http://127.0.0.1:8008/_matrix/client/versions
```

镜像以原型所用的发布摘要固定，不代表它永久是最新或无漏洞的版本。升级前核对上游安全公告、备份并在测试环境验证。`init.py` 创建 `friends_chat` 数据库与专用角色，自动生成密码并写到忽略目录 `state/`；已有状态或同名数据库时会拒绝继续。中途失败应检查状态，不能盲目删除密钥重新初始化。

### 2. 准备 Element Web

从 [Element 官方发布页](https://github.com/element-hq/element-web/releases) 获取发布包。此处固定原型版本 `v1.12.33`；部署前评估上游更新与安全公告。

```bash
curl -fL --retry 2 \
  https://github.com/element-hq/element-web/releases/download/v1.12.33/element-v1.12.33.tar.gz \
  -o /tmp/element-v1.12.33.tar.gz
sudo python3 scripts/prepare-web.py /tmp/element-v1.12.33.tar.gz "$CHAT_IP"
```

目标目录须为空，避免将旧版资产混入新版。不要使用来历不明的镜像站或关闭 TLS 校验。中转下载说明见 [docs/offline-transfer.md](docs/offline-transfer.md)。

### 3. 配置 HTTP 证书验证入口

```bash
sudo mkdir -p /var/www/friends-chat-acme/.well-known/acme-challenge
sed "s/__SERVER_IP__/$CHAT_IP/g" templates/nginx-acme.conf | sudo tee /etc/nginx/sites-available/friends-chat >/dev/null
sudo ln -s /etc/nginx/sites-available/friends-chat /etc/nginx/sites-enabled/friends-chat
sudo nginx -t && sudo systemctl reload nginx
```

如同名站点文件已存在，先检查和备份，不要覆盖其他业务。该验证路径必须能从公网 80 端口访问。

### 4. 申请 IP 证书并开启 HTTPS

使用支持 IP 地址的 Certbot 5.4+。例如通过官方 Snap 包安装后，确认版本：

```bash
sudo snap install --classic certbot
/snap/bin/certbot --version
sudo /snap/bin/certbot certonly \
  --preferred-profile shortlived --webroot \
  -w /var/www/friends-chat-acme \
  --ip-address "$CHAT_IP" --cert-name friends-chat
```

交互时自行阅读并决定是否接受证书机构协议及邮箱选项。IP 证书有效期短；详见 [Let's Encrypt 官方说明](https://letsencrypt.org/2026/03/11/shorter-certs-certbot)。签发成功后：

```bash
sed "s/__SERVER_IP__/$CHAT_IP/g" templates/nginx-https.conf | sudo tee /etc/nginx/sites-available/friends-chat >/dev/null
sudo nginx -t && sudo systemctl reload nginx
sudo install -m 755 templates/renew-nginx.sh /etc/letsencrypt/renewal-hooks/deploy/friends-chat-nginx
sudo systemctl list-timers --all | grep certbot
sudo /snap/bin/certbot renew --dry-run --run-deploy-hooks
curl --max-time 15 "https://$CHAT_IP/_matrix/client/versions"
```

检查续期模拟及钩子均成功。不要使用 `curl -k` 或忽略浏览器证书警告来代替修复证书。Certbot 不是安装后就永久免维护：保持验证路径可达，并监控证书到期及续期失败。

### 5. 创建账号并聊天

```bash
sudo bash scripts/add-user.sh admin
sudo bash scripts/add-user.sh friend
```

密码在终端中交互输入两次，不显示字符；`Passwords do not match` 表示两次不一致，重新执行即可。脚本创建普通聊天账号，用户名 `admin` 本身不授予服务器管理员权限。

打开 `https://你的公网IP/`，选择中文并登录；邀请朋友账号建立私聊或私密群。欢迎页可能仍显示创建账户按钮，但服务端关闭了公开注册。首次使用保存恢复密钥，添加新设备时完成设备验证。密码重置无法恢复丢失的消息密钥。

## 运维

```bash
sudo docker compose ps
sudo docker compose logs --tail=60 synapse
sudo bash scripts/backup.sh
```

备份默认写到 `/var/backups/friends-chat/`，包含数据库、服务配置和服务器签名密钥，**不得上传 GitHub**。脚本不会自动删除旧备份，也不会建立定时任务或异地存储；需要运维者安排周期、存储限额和受保护的异地副本。还应妥善备份 Nginx 实际配置和证书配置。本机备份不等于灾难恢复，也不代替用户恢复密钥；在隔离环境完成恢复演练后再依赖它。

首次上线前逐项完成：两个账号/设备互发消息、核对房间加密状态、设备交叉验证、离线同步、恢复密钥恢复、证书续期模拟、备份恢复。当前项目不宣称这些已经全部通过。

## 仓库结构

```text
compose.yaml                  # 固定镜像、资源限制、本机网络
.env.example                  # 参考变量；脚本不自动读取它
scripts/init.py               # 新实例初始化，生成真实秘密到 state/
scripts/prepare-web.py        # 解压官方客户端并生成默认服务器配置
scripts/add-user.sh           # 交互创建普通账号
scripts/backup.sh             # 手动本机备份
templates/nginx-*.conf        # 证书验证及 HTTPS 反向代理模板
templates/renew-nginx.sh       # 续期后重新加载 Nginx
SECURITY.md                   # 威胁边界与漏洞报告
THIRD_PARTY.md                # 上游组件与许可范围
```

本仓库不包含服务器真实 IP、云账号信息、实际账号密码、用户数据、签名密钥或证书私钥。不要将运行目录整包公开，`.gitignore` 不能阻止 GitHub 网页手动上传秘密文件。

## 许可证与贡献

本仓库原创脚本、模板和文档采用 [MIT](LICENSE)。上游组件继续适用各自许可证；MIT 不覆盖 Synapse、Element 或其修改版本，参见 [THIRD_PARTY.md](THIRD_PARTY.md)。欢迎通过 Issue/PR 提交脱敏的复现步骤、兼容性改进和文档修正；私密数据或安全问题请按 [SECURITY.md](SECURITY.md) 处理。
