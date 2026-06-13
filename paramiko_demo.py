#!/usr/bin/env python3
"""
paramiko 远程批量巡检示例
需要在目标机器有 SSH 访问权限

安装：pip install paramiko
"""

import paramiko
import getpass
from datetime import datetime


# 要巡检的服务器列表（改成你的）
SERVERS = [
    {"host": "192.168.1.101", "port": 22, "user": "root"},
    {"host": "192.168.1.102", "port": 22, "user": "root"},
]


def ssh_exec(ssh: paramiko.SSHClient, cmd: str, timeout: int = 10) -> str:
    """通过 SSH 执行命令，返回输出"""
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip()
    except Exception as e:
        return f"[SSH 错误] {e}"


def inspect_server(ssh: paramiko.SSHClient) -> dict:
    """对一台服务器执行巡检，返回结果字典"""
    data = {}

    # 主机信息
    data["hostname"] = ssh_exec(ssh, "hostname")
    data["uptime"]   = ssh_exec(ssh, "uptime -p")

    # CPU
    raw = ssh_exec(ssh, "top -bn1 | grep 'Cpu' | awk '{print 100-$8}'")
    data["cpu"] = f"{float(raw):.1f}%" if raw and "错误" not in raw else raw

    # 内存
    raw = ssh_exec(ssh, "free | awk 'NR==2 {print $3/$2*100}'")
    data["mem"] = f"{float(raw):.1f}%" if raw and "错误" not in raw else raw

    # 磁盘
    disk_out = ssh_exec(ssh, "df -h | grep /dev/ | awk '{print $1,$5,$6}'")
    disks = []
    for line in disk_out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            disks.append({"dev": parts[0], "pct": parts[1], "mount": parts[2] if len(parts) > 2 else ""})
    data["disks"] = disks

    # 负载
    data["load"] = ssh_exec(ssh, "uptime | awk -F'load average:' '{print $2}'")

    return data


def print_report(host: str, data: dict):
    """格式化打印巡检报告"""
    print(f"\n{'='*45}")
    print(f"  {host} — {data.get('hostname', '?')}")
    print(f"{'='*45}")
    print(f"  运行时间：{data.get('uptime', 'N/A')}")
    print(f"  CPU 使用率：{data.get('cpu', 'N/A')}")
    print(f"  内存使用率：{data.get('mem', 'N/A')}")
    print(f"  系统负载：{data.get('load', 'N/A')}")
    print(f"  磁盘状态：")
    for d in data.get("disks", []):
        pct = int(d["pct"].replace("%", ""))
        if pct >= 80:
            icon = "⚠️"
        elif pct >= 60:
            icon = "⚡"
        else:
            icon = "✅"
        print(f"    {d['dev']:20s} {d['pct']:>4s}  {icon}  {d['mount']}")


def main():
    password = getpass.getpass("SSH 密码（所有服务器统一）: ")

    for svr in SERVERS:
        host = svr["host"]
        print(f"\n>>> 正在连接 {host} ...")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                hostname=host,
                port=svr["port"],
                username=svr["user"],
                password=password,
                timeout=10,
            )
            data = inspect_server(ssh)
            print_report(host, data)
        except paramiko.ssh_exception.AuthenticationException:
            print(f"  ❌ 认证失败：{host}")
        except paramiko.ssh_exception.NoValidConnectionsError:
            print(f"  ❌ 无法连接：{host}")
        except Exception as e:
            print(f"  ❌ 错误：{e}")
        finally:
            ssh.close()


if __name__ == "__main__":
    print("=== 批量远程巡检 ===")
    print(f"时间：{datetime.now():%Y-%m-%d %H:%M:%S}")
    main()
