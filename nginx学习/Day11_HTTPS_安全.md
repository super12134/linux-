# Day 11 — Nginx HTTPS + 安全

> 学习日期：2026-06-09

---

## 目录

1. [HTTPS 基础概念](#1-https-基础概念)
2. [Let's Encrypt + acme.sh 免费证书](#2-lets-encrypt--acmesh-免费证书)
3. [Nginx HTTPS 配置](#3-nginx-https-配置)
4. [HTTP → HTTPS 强制跳转](#4-http--https-强制跳转)
5. [限流（limit_req）](#5-限流limit_req)
6. [gzip 压缩](#6-gzip-压缩)
7. [安全相关配置](#7-安全相关配置)
8. [实操：完整配置示例](#8-实操完整配置示例)
9. [验证与排障](#9-验证与排障)

---

## 1. HTTPS 基础概念

### 为什么需要 HTTPS？

| 特性 | HTTP | HTTPS |
|------|------|-------|
| 加密 | 明文传输 | TLS/SSL 加密 |
| 端口 | 80 | 443 |
| 数据完整性 | 可被篡改 | 防篡改 |
| 身份验证 | 无 | 证书验证身份 |
| SEO | 不友好 | 加分 |
| 浏览器标记 | "不安全" | 锁图标 |

### TLS 握手简要流程

```
Client                          Server
  |                                |
  |── ClientHello (TLS版本、密码套件) →|
  |← ServerHello + 证书 + 公钥 ────|
  |── 用公钥加密 pre-master secret →|
  |← 双方生成对称密钥 ──────────────|
  |── 加密通信开始 ────────────────→|
```

### 证书类型

| 类型 | 价格 | 适用场景 |
|------|------|----------|
| DV (域名验证型) | 免费 | 个人网站、博客 |
| OV (组织验证型) | 收费 | 企业网站 |
| EV (扩展验证型) | 收费 | 银行、金融 |
| 自签名证书 | 免费 | 内网测试 |

> **我们的选择**：Let's Encrypt 提供免费 DV 证书，90 天有效期，支持自动续签。

---

## 2. Let's Encrypt + acme.sh 免费证书

### 2.1 acme.sh 简介

[acme.sh](https://github.com/acmesh-official/acme.sh) 是一个纯 Shell 脚本的 ACME 客户端，支持：
- 自动申请、续签 Let's Encrypt 证书
- 支持多种 DNS API（阿里云、DNSPod、Cloudflare 等）
- 支持 HTTP 和 DNS 两种验证方式
- 安装后自动配置定时任务续签

### 2.2 安装 acme.sh

```bash
# 安装（推荐 curl 方式）
curl https://get.acme.sh | sh -s email=your@email.com

# 或者用 wget
wget -O -  https://get.acme.sh | sh -s email=your@email.com
```

安装后会：
1. 创建 `~/.acme.sh/` 目录
2. 添加 alias 到 `~/.bashrc`
3. 配置定时任务（每天检查续签）

```bash
# 查看定时任务
crontab -l | grep acme

# 输出示例：
# 0 0 * * * /root/.acme.sh/acme.sh --cron --home /root/.acme.sh > /dev/null
```

### 2.3 申请证书的方式

#### 方式一：HTTP 验证（推荐，要求 80 端口可达）

```bash
# 使用 standalone 模式（acme.sh 自己启动临时服务器）
# 需要 80 端口未被占用
acme.sh --issue -d yourdomain.com --standalone

# 如果 Nginx 已经在用 80 端口，使用 webroot 模式
acme.sh --issue -d yourdomain.com --webroot /var/www/html

# 或者使用 nginx 模式（acme.sh 自动操作 nginx）
service nginx stop  # 先停掉 nginx 释放 80 端口
acme.sh --issue -d yourdomain.com --standalone
```

#### 方式二：DNS 验证（推荐泛域名证书）

```bash
# 手动 DNS 验证（需要去 DNS 管理面板添加 TXT 记录）
acme.sh --issue -d *.yourdomain.com --dns --yes-I-know-dns-manual-mode-enough-go-ahead

# 自动 DNS API（推荐，以阿里云为例）
export Ali_Key="你的AccessKeyId"
export Ali_Secret="你的AccessKeySecret"
acme.sh --issue -d *.yourdomain.com --dns dns_ali
```

### 2.4 安装证书到 Nginx

```bash
# 创建证书存放目录
mkdir -p /etc/nginx/ssl

# 安装证书（acme.sh 会复制到目标路径，并记录位置）
acme.sh --install-cert -d yourdomain.com \
  --key-file       /etc/nginx/ssl/yourdomain.com.key \
  --fullchain-file /etc/nginx/ssl/yourdomain.com.crt \
  --reloadcmd     "service nginx force-reload"

# --key-file: 私钥文件
# --fullchain-file: 包含完整证书链的证书文件
# --reloadcmd: 续签成功后执行的命令（重载 nginx）
```

### 2.5 证书续签（自动）

acme.sh 安装时会自动设置 crontab，证书会在到期前自动续签。

```bash
# 手动续签
acme.sh --renew -d yourdomain.com

# 强制续签（即使未到期）
acme.sh --renew -d yourdomain.com --force
```

---

## 3. Nginx HTTPS 配置

### 3.1 基础 HTTPS Server 块

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # 证书配置
    ssl_certificate     /etc/nginx/ssl/yourdomain.com.crt;
    ssl_certificate_key /etc/nginx/ssl/yourdomain.com.key;

    # 协议与加密套件
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;

    # 其他优化
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # 站点内容
    root /var/www/html;
    index index.html index.htm;

    location / {
        try_files $uri $uri/ =404;
    }

    access_log /var/log/nginx/yourdomain_access.log;
    error_log  /var/log/nginx/yourdomain_error.log;
}
```

### 3.2 SSL 配置参数详解

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `ssl_protocols` | 允许的 TLS 协议版本 | `TLSv1.2 TLSv1.3` |
| `ssl_ciphers` | 加密套件 | mozilla 推荐列表 |
| `ssl_prefer_server_ciphers` | 优先服务端加密套件 | `on` |
| `ssl_session_cache` | SSL 会话缓存 | `shared:SSL:10m` |
| `ssl_session_timeout` | 会话超时时间 | `1d`（一天） |
| `ssl_session_tickets` | 会话票据 | `off`（更好的安全性） |

> 使用 [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/) 生成推荐的 SSL 配置。

### 3.3 使用 http2 提升性能

`listen 443 ssl http2;` 中的 `http2` 启用 HTTP/2，优势：
- 多路复用（一个连接并发多个请求）
- 头部压缩（HPACK）
- 服务端推送（Server Push）
- 二进制分帧

---

## 4. HTTP → HTTPS 强制跳转

### 4.1 最常用方式：return 301

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # 301 永久重定向到 HTTPS
    return 301 https://$server_name$request_uri;

    # 或者保留主机名（处理多个域名的情况）
    # return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    # ... SSL 配置 ...
}
```

### 4.2 302 临时跳转

```nginx
# 302 临时重定向（调试或迁移期间使用）
return 302 https://$server_name$request_uri;
```

### 4.3 带 HSTS 的 301 跳转

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # HSTS：告诉浏览器永远使用 HTTPS 访问
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # ... 其余配置 ...
}
```

### 4.4 301 vs 302

| 状态码 | 含义 | 浏览器行为 | SEO |
|--------|------|-----------|-----|
| 301 | 永久重定向 | 缓存跳转，下次直接访问新地址 | 权重转移到新地址 |
| 302 | 临时重定向 | 不缓存，每次先访问原地址 | 权重留在原地址 |

> **生产环境用 301**。测试/迁移期间用 302。

---

## 5. 限流（limit_req）

### 5.1 基本原理

Nginx 使用 **漏桶算法（Leaky Bucket）** 实现请求限流：

```
请求到达 → [桶] → 按固定速率处理 → 后端
           ↑
        超出桶容量则拒绝（503）
```

### 5.2 基本配置

```nginx
http {
    # 定义限流区域
    # $binary_remote_addr：按 IP 限流
    # zone=mylimit:10m：10MB 空间存储状态
    # rate=10r/s：每秒 10 个请求
    limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;

    server {
        location / {
            # 应用限流
            limit_req zone=mylimit burst=20 nodelay;

            proxy_pass http://backend;
        }
    }
}
```

### 5.3 参数详解

| 参数 | 说明 | 示例 |
|------|------|------|
| `rate=10r/s` | 平均速率，每秒 10 个请求 | `10r/s`, `30r/m` |
| `burst=20` | 突发容量，允许最多 20 个排队 | 超出直接返回 503 |
| `nodelay` | 排队请求不延迟处理 | 不加则排队请求会被延迟 |

**rate 的解析：**
- `10r/s` → 每 100ms 处理 1 个请求
- `30r/m` → 每 2s 处理 1 个请求

### 5.4 burst 行为演示

假设 `rate=10r/s burst=20`：

```
时刻 0:  请求 ├┤ (正常，漏桶以 10r/s 流出)
时刻 1:  请求 ├██████████┤ (桶满了，之后的请求排队)
时刻 2:  请求 ├████████████████████┤ (桶容量 20，未满继续排队)
时刻 3:  请求 ┤ (桶爆了，返回 503)
```

- **不加 `nodelay`**：排队请求按 rate 的速率依次处理（延迟大）
- **加 `nodelay`**：排队请求立即处理，但超出 burst 的直接拒绝

### 5.5 限流响应处理

```nginx
# 限流发生时返回的响应码
limit_req_status 503;

# 或者自定义错误页面
error_page 503 /custom_503.html;

location = /custom_503.html {
    root /var/www/html;
    internal;
}
```

### 5.6 按 URL 限流

```nginx
# 按 IP + 请求路径限流
limit_req_zone $binary_remote_addr$uri zone=bylogin:10m rate=5r/m;

location /api/login {
    limit_req zone=bylogin burst=3;
    proxy_pass http://backend;
}
```

### 5.7 多个限流规则叠加

```nginx
# 全局限流
limit_req_zone $binary_remote_addr zone=global:10m rate=100r/s;
# API 限流更严格
limit_req_zone $binary_remote_addr zone=api:10m rate=20r/s;

server {
    location / {
        limit_req zone=global burst=50 nodelay;
        proxy_pass http://backend;
    }

    location /api/ {
        limit_req zone=api burst=5 nodelay;
        limit_req zone=global burst=50 nodelay;  # 同时满足两个规则
        proxy_pass http://backend;
    }
}
```

---

## 6. gzip 压缩

### 6.1 基本原理

gzip 在 Nginx 响应客户端时动态压缩内容，减少传输大小：

```
原始 HTML (100KB) → gzip 压缩 → 压缩后 (20KB) → 浏览器解压 → 原始 HTML
                    CPU 换带宽             ↓
                                       用户感知更快
```

### 6.2 基本配置

```nginx
http {
    # 开启 gzip
    gzip on;

    # 压缩级别 1-9（1 最快/压缩率最低，9 最慢/压缩率最高）
    gzip_comp_level 5;

    # 最小压缩阈值（小于此大小的不压缩）
    gzip_min_length 1000;

    # 压缩的 MIME 类型
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml text/javascript image/svg+xml;

    # 添加 Vary: Accept-Encoding 头（告知 CDN）
    gzip_vary on;

    # 禁用 gzip 的 User-Agent
    gzip_disable "msie6";

    # 是否压缩代理请求（设置为 any 表示所有代理请求都压缩）
    gzip_proxied any;
}
```

### 6.3 参数详解

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `gzip_comp_level` | 压缩级别（1-9） | **5**（平衡 CPU 和压缩率） |
| `gzip_min_length` | 最小压缩大小（字节） | **1000**（<1KB 的文件压缩收益小） |
| `gzip_types` | 压缩的 MIME 类型 | text/css, js, json, xml, svg |
| `gzip_vary` | 添加 Vary 头 | **on** |
| `gzip_disable` | 禁用的 UA | `msie6` |
| `gzip_proxied` | 代理压缩行为 | `any` |

### 6.4 压缩效果对比

| 文件类型 | 原始大小 | Gzip 后 | 节省 |
|---------|---------|---------|------|
| HTML | 50 KB | 12 KB | 76% |
| CSS | 30 KB | 6 KB | 80% |
| JavaScript | 100 KB | 30 KB | 70% |
| JSON API | 200 KB | 25 KB | 87% |
| PNG/JPEG | — | — | **不压缩**（已压缩） |

> **注意**：不要对图片（jpg/png/gif）、视频（mp4）、已压缩文件（zip）启用 gzip，它们已经压缩过，再压也没效果，白费 CPU。

### 6.5 预压缩（静态 gzip）

对于频繁访问的静态文件，可以预先压缩好，Nginx 直接发送：

```bash
# 预先压缩静态文件
gzip -k /var/www/html/style.css  # 生成 style.css.gz
```

```nginx
location /static/ {
    gzip_static on;   # 优先发送 .gz 文件
    gzip_proxied expired no-cache no-store private auth;
}
```

> `gzip_static` 模块需要编译安装 ngx_http_gzip_static_module。

### 6.6 验证 gzip 是否生效

```bash
# 查看响应头
curl -H "Accept-Encoding: gzip" -I http://yourdomain.com/style.css

# 响应头中应有：
# Content-Encoding: gzip
# Vary: Accept-Encoding

# 或者浏览器 DevTools → Network → Response Headers
```

---

## 7. 安全相关配置

### 7.1 HSTS（HTTP Strict Transport Security）

```nginx
# 告诉浏览器：未来 xxx 秒内强制使用 HTTPS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# max-age: 有效期（秒），63072000 = 2 年
# includeSubDomains: 包含所有子域名
# preload: 申请加入浏览器内置 HSTS 预加载列表
```

### 7.2 安全响应头

```nginx
# 防止 XSS 攻击
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options SAMEORIGIN;
add_header X-XSS-Protection "1; mode=block";

# 内容安全策略
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;";

# 防止 MIME 类型混淆
add_header X-Content-Type-Options nosniff;
```

### 7.3 隐藏 Nginx 版本号

```nginx
# 在 http 块中配置
server_tokens off;
```

效果：
```
# 之前
Server: nginx/1.24.0

# 之后
Server: nginx
```

### 7.4 限制连接数

```nginx
http {
    # 按 IP 限制并发连接数
    limit_conn_zone $binary_remote_addr zone=addr:10m;

    server {
        # 每个 IP 最多 10 个并发连接
        limit_conn addr 10;

        # 限制请求速率（已在第 5 节介绍）
        limit_req zone=mylimit burst=20 nodelay;
    }
}
```

### 7.5 SSL/TLS 安全加固

```nginx
# 使用安全的加密套件
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

# 关闭不安全的协议
ssl_protocols TLSv1.2 TLSv1.3;

# 优先使用服务端定义的加密套件
ssl_prefer_server_ciphers on;

# 启用 OCSP Stapling（提高 TLS 握手性能）
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 1.1.1.1 valid=300s;
resolver_timeout 5s;
```

### 7.6 证书链完整性

```nginx
ssl_certificate     /etc/nginx/ssl/fullchain.pem;  # 包含中间证书
ssl_certificate_key /etc/nginx/ssl/privkey.pem;
```

验证证书链：
```bash
openssl s_client -connect yourdomain.com:443 -showcerts
```

---

## 8. 实操：完整配置示例

### 8.1 完整 nginx.conf

```nginx
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
    multi_accept on;
    use epoll;
}

http {
    ## 基础设置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ## 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log  /var/log/nginx/error.log warn;

    ## Gzip 压缩
    gzip on;
    gzip_comp_level 5;
    gzip_min_length 1000;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml text/javascript image/svg+xml;
    gzip_vary on;
    gzip_disable "msie6";
    gzip_proxied any;

    ## 限流配置
    limit_req_zone $binary_remote_addr zone=global:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_conn_zone $binary_remote_addr zone=addr:10m;

    ## SSL 会话缓存（全局）
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    ## HTTP → HTTPS 跳转
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    ## HTTPS 站点
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ## SSL 证书
        ssl_certificate     /etc/nginx/ssl/yourdomain.com.crt;
        ssl_certificate_key /etc/nginx/ssl/yourdomain.com.key;

        ## SSL 协议与加密
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers on;
        ssl_stapling on;
        ssl_stapling_verify on;
        resolver 8.8.8.8 1.1.1.1 valid=300s;
        resolver_timeout 5s;

        ## 安全头
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options SAMEORIGIN;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy "strict-origin-when-cross-origin";

        ## 站点根目录
        root /var/www/yourdomain.com/html;
        index index.html index.htm;

        ## 全局限流
        limit_req zone=global burst=50 nodelay;
        limit_conn addr 10;

        ## 静态资源（长缓存 + gzip）
        location /static/ {
            expires 30d;
            add_header Cache-Control "public, immutable";
            access_log off;
            try_files $uri $uri/ =404;
        }

        ## 登录接口（严格限流）
        location /api/login {
            limit_req zone=login burst=3 nodelay;
            proxy_pass http://backend:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        ## API 代理
        location /api/ {
            proxy_pass http://backend:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        ## 默认处理
        location / {
            try_files $uri $uri/ /index.html;
        }

        ## 禁止访问隐藏文件
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }

        ## 日志
        access_log /var/log/nginx/yourdomain_access.log;
        error_log  /var/log/nginx/yourdomain_error.log;
    }
}
```

### 8.2 快速部署脚本

```bash
#!/bin/bash
# 一键部署 HTTPS 站点脚本
# 使用方法: ./deploy_ssl.sh yourdomain.com

DOMAIN=$1
EMAIL="admin@${DOMAIN}"

if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 yourdomain.com"
    exit 1
fi

# 1. 安装 acme.sh
echo ">>> 安装 acme.sh..."
curl https://get.acme.sh | sh -s email=$EMAIL

# 2. 申请证书（standalone 模式，需要先停 nginx）
echo ">>> 申请证书..."
systemctl stop nginx
/root/.acme.sh/acme.sh --issue -d $DOMAIN --standalone

# 3. 创建 SSL 目录并安装证书
echo ">>> 安装证书..."
mkdir -p /etc/nginx/ssl
/root/.acme.sh/acme.sh --install-cert -d $DOMAIN \
    --key-file       /etc/nginx/ssl/${DOMAIN}.key \
    --fullchain-file /etc/nginx/ssl/${DOMAIN}.crt \
    --reloadcmd     "systemctl force-reload nginx"

# 4. 生成 HTTPS 配置
echo ">>> 写入 Nginx 配置..."
cat > /etc/nginx/conf.d/${DOMAIN}.conf << CONF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate     /etc/nginx/ssl/${DOMAIN}.crt;
    ssl_certificate_key /etc/nginx/ssl/${DOMAIN}.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;

    root /var/www/${DOMAIN}/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ =404;
    }

    access_log /var/log/nginx/${DOMAIN}_access.log;
    error_log  /var/log/nginx/${DOMAIN}_error.log;
}
CONF

# 5. 检查配置并启动
echo ">>> 检查并重启 Nginx..."
nginx -t && systemctl start nginx

echo ">>> 部署完成！https://${DOMAIN}"
```

---

## 9. 验证与排障

### 9.1 SSL 验证工具

```bash
# 1. 查看证书信息
openssl s_client -connect yourdomain.com:443 -showcerts

# 2. 检查 SSL 配置
# 在线工具：https://www.ssllabs.com/ssltest/

# 3. 检查 Nginx 配置是否正确
nginx -t

# 4. 查看证书过期时间
openssl x509 -in /etc/nginx/ssl/yourdomain.com.crt -noout -dates

# 5. 检查域名解析
dig yourdomain.com
nslookup yourdomain.com
```

### 9.2 常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 证书安全警告 | 证书链不完整 | 使用 fullchain.pem |
| Mixed Content | 页面中有 HTTP 资源 | 将 `http://` 改为 `https://` 或 `//` |
| 无法申请证书 | 80 端口被占用 | 使用 standalone 前停 nginx |
| 证书未自动续签 | crontab 问题 | 检查 `crontab -l`，手动重跑 cron |
| SSL_ERROR_BAD_CERT_DOMAIN | 域名不匹配 | 申请证书时加上所有域名 |
| 301 重定向循环 | Cloudflare CDN 配置问题 | Cloudflare SSL 设置为 Full 或 Full (strict) |
| 403 Forbidden | 权限问题 | 检查 SSL 私钥权限 `chmod 600` |

### 9.3 证书到期检查脚本

```bash
#!/bin/bash
# 检查证书是否即将过期，提前提醒

DOMAINS=("yourdomain.com" "anotherdomain.com")
WARN_DAYS=30

for domain in "${DOMAINS[@]}"; do
    cert_file="/etc/nginx/ssl/${domain}.crt"
    if [ -f "$cert_file" ]; then
        expiry=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)
        expiry_epoch=$(date -d "$expiry" +%s)
        now_epoch=$(date +%s)
        days_left=$(( ($expiry_epoch - $now_epoch) / 86400 ))

        if [ $days_left -lt $WARN_DAYS ]; then
            echo "⚠️  $domain 证书将在 ${days_left} 天后过期！($expiry)"
        else
            echo "✅  $domain 证书有效期还有 ${days_left} 天"
        fi
    else
        echo "❌  $domain 未找到证书文件"
    fi
done
```

---

## 总结

```
Day 11 核心知识点：

┌──────────────────────────────────┐
│          HTTPS 配置               │
│  ┌────────────────────────────┐  │
│  │ Let's Encrypt + acme.sh    │  │
│  │   └ 免费 DV 证书           │  │
│  │   └ 90 天自动续签           │  │
│  ├────────────────────────────┤  │
│  │ HTTP → HTTPS 跳转          │  │
│  │   └ return 301             │  │
│  │   └ HSTS 策略              │  │
│  ├────────────────────────────┤  │
│  │ 限流 (limit_req)           │  │
│  │   └ 漏桶算法               │  │
│  │   └ rate / burst / nodelay │  │
│  ├────────────────────────────┤  │
│  │ gzip 压缩                  │  │
│  │   └ 压缩级别 1-9          │  │
│  │   └ 文本类资源优先         │  │
│  ├────────────────────────────┤  │
│  │ 安全加固                   │  │
│  │   └ 安全响应头            │  │
│  │   └ 隐藏版本号            │  │
│  │   └ 强加密套件            │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

### 学习要点回顾

| 模块 | 已掌握 | 需复习 |
|------|--------|--------|
| acme.sh 安装和使用 | □ | □ |
| 证书申请（HTTP/DNS 验证） | □ | □ |
| HTTPS server 块配置 | □ | □ |
| 301/302 跳转 | □ | □ |
| HSTS 策略 | □ | □ |
| limit_req 限流 | □ | □ |
| burst 和 nodelay 原理 | □ | □ |
| gzip 压缩配置 | □ | □ |
| 安全响应头 | □ | □ |
| SSL 安全加固 | □ | □ |

---

**Next → Day 12: Nginx 反向代理 + 负载均衡进阶**
