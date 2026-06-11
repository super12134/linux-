#!/bin/bash
# 用 Maven 容器编译 jar，然后构建 Docker 镜像（JRE only）
set -e

echo "=== 1/2 用 Maven 容器编译 .jar ==="
docker run --rm \
  -v "$PWD":/project \
  -w /project \
  -v maven-repo:/root/.m2 \
  maven:3.9-eclipse-temurin-17 \
  mvn clean package -DskipTests

echo ""
echo "=== 2/2 构建并启动 Docker 容器 ==="
docker compose build --no-cache
docker compose up -d

echo ""
echo "完成！应用运行在 http://localhost:8080"
