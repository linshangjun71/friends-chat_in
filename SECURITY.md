# Security / 安全说明

Do not open a public issue containing secrets, database dumps, private chat logs, recovery keys, or personal information. Use GitHub private vulnerability reporting if enabled. Otherwise ask for a private contact channel without disclosing the issue details. Upstream protocol/client vulnerabilities should be reported to the relevant upstream project.

请勿在公开 Issue 中提交密码、数据库、聊天日志、签名密钥、恢复密钥或个人信息。若仓库启用了 GitHub 私密漏洞报告，请使用该渠道；否则先请求私下联系方式，不要先公开漏洞细节。上游协议或客户端漏洞应向对应上游项目报告。

## Scope

This repository contains deployment scripts and configuration templates, not a new cryptographic protocol. No security audit or complete two-device E2EE/recovery test has been completed for this deployment kit. Default encryption is a room creation setting, not evidence that every existing room or every client is secure.

Server operators can see metadata. A compromised web server can serve malicious JavaScript that steals keys/plaintext; endpoint compromise defeats E2EE. HTTPS is mandatory, but does not eliminate this risk. Account-password resets do not recover lost message decryption keys.

数据库、真实 homeserver.yaml、state/、备份和证书私钥均不得提交。仅本机备份无法防止服务器或云账号丢失。对备份做加密、访问控制和异地保存，并在隔离环境验证恢复。
