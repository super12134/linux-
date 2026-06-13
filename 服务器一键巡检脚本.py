#!/usr/bin/env python3
"""
服务器一键巡检脚本 (Python 版)
用 os / subprocess / shutil 重写第一周的 Shell 巡检脚本
"""

import os
import subprocess
import shutil


def run_cmd(cmd: str) -> str:
    """执行 shell 命令并返回 stdout（自动去除尾部空白）"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "超时"
    except Exception as e:
        return f"错误: {e}"


def get_host_info():
    """1. 主机信息"""
    print("=" * 40)
    print("         服务器巡检报告")
    print("=" * 40)

    hostname = run_cmd("hostname")
    uptime_raw = run_cmd("uptime -p")
    print(f"  主机名：{hostname}")
    print(f"  运行时间：{uptime_raw}")


def get_cpu_usage() -> float:
    """2. CPU 使用率"""
    raw = run_cmd("top -bn1 | grep 'Cpu' | awk '{print 100-$8}'")
    try:
        val = float(raw)
        print(f"  CPU 使用率：{val:.1f}%")
        return val
    except (ValueError, TypeError):
        print(f"  CPU 使用率：获取失败 ({raw})")
        return 0.0


def get_mem_usage() -> float:
    """3. 内存使用率"""
    raw = run_cmd("free | awk 'NR==2 {print $3/$2*100}'")
    try:
        val = float(raw)
        print(f"  内存使用率：{val:.1f}%")
        return val
    except (ValueError, TypeError):
        print(f"  内存使用率：获取失败 ({raw})")
        return 0.0


def get_disk_usage():
    """4. 磁盘使用率（带颜色告警）"""
    print("  磁盘使用率：")
    raw = run_cmd("df -h | grep /dev/")
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        device = parts[0]
        pct_str = parts[4].replace("%", "")
        if not pct_str.isdigit():
            continue
        pct = int(pct_str)

        if pct >= 80:
            status = "⚠️ 告警"
        elif pct >= 60:
            status = "⚡ 提醒"
        else:
            status = "✅ 正常"

        # 同时显示挂载点（第 5 列之后）
        mount = parts[5] if len(parts) > 5 else ""
        print(f"    {device}  {pct}%  [{status}]  {mount}")


def check_load():
    """5. 系统负载（额外增加的检查）"""
    load = run_cmd("uptime | awk -F'load average:' '{print $2}'")
    print(f"  系统负载：{load}")


def check_disk_inode():
    """6. inode 使用率（磁盘满的另一种可能）"""
    print("  inode 使用率：")
    raw = run_cmd("df -i | grep /dev/")
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        device = parts[0]
        pct_str = parts[4].replace("%", "")
        if not pct_str.isdigit():
            continue
        pct = int(pct_str)
        if pct >= 80:
            status = "⚠️ 告警"
        elif pct >= 60:
            status = "⚡ 提醒"
        else:
            status = "✅ 正常"
        print(f"    {device}  {pct}%  [{status}]")


def main():
    get_host_info()
    print()
    get_cpu_usage()
    print()
    get_mem_usage()
    print()
    get_disk_usage()
    print()
    check_load()
    print()
    check_disk_inode()
    print()
    print("=" * 40)
    print("         巡检完成")
    print("=" * 40)


if __name__ == "__main__":
    main()
