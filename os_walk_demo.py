#!/usr/bin/env python3
"""
os 模块实操：文件系统遍历工具
"""
import os


def walk_dir(root: str, depth: int = 0, max_depth: int = 3):
    """递归遍历目录，限制深度"""
    if depth > max_depth:
        return
    try:
        entries = os.listdir(root)
    except PermissionError:
        return

    for name in entries:
        path = os.path.join(root, name)
        indent = "  " * depth
        if os.path.islink(path):
            print(f"{indent}🔗 {name} -> {os.readlink(path)}")
        elif os.path.isfile(path):
            size = os.path.getsize(path)
            print(f"{indent}📄 {name}  ({size:,} bytes)")
        elif os.path.isdir(path):
            print(f"{indent}📁 {name}/")
            walk_dir(path, depth + 1, max_depth)


def find_large_files(root: str, min_mb: int = 100):
    """查找大于指定大小的文件"""
    print(f"\n>>> 查找 {root} 下大于 {min_mb}MB 的文件\n")
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                size_mb = os.path.getsize(fp) / (1024 * 1024)
                if size_mb > min_mb:
                    print(f"  {size_mb:.1f} MB  {fp}")
            except (PermissionError, FileNotFoundError):
                continue


if __name__ == "__main__":
    # 示例：遍历 /etc 深度 2
    walk_dir("/etc", max_depth=2)
    # 示例：找大文件
    # find_large_files("/var", min_mb=50)
