#!/bin/bash



# 1. 主机信息
echo "===== 服务器巡检 ====="
echo "主机名：$(hostname)"
echo "运行时间：$(uptime -p)"
echo ""

# 2. CPU
echo "CPU 使用率：$(top -bn1 | grep 'Cpu' | awk '{print 100-$8 "%"}')"

# 3. 内存
echo "内存 使用率：$(free | awk 'NR==2 {print $3/$2*100 "%"}')"
echo ""

# 4. 磁盘（带颜色告警）
echo "磁盘使用率："
df -h | grep /dev/ | awk '{print $1,$5}' | while read dev use; do
    num=${use%\%}
    if [ $num -ge 80 ]; then
        echo -e "$dev $use ${RED}告警${NC}"
    elif [ $num -ge 60 ]; then
        echo -e "$dev $use ${YELLOW}提醒${NC}"
    else
        echo -e "$dev $use ${GREEN}正常${NC}"
    fi
done

echo "======================"