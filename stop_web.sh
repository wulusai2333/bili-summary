#!/bin/bash
# 精确关闭 8765 端口上的 Web 服务，不影响其他 Python 进程。
# 用法: ./stop_web.sh   (可用 PORT 环境变量覆盖端口)
PORT="${PORT:-8765}"

pids=$(ss -tlnp 2>/dev/null | awk -v p=":$PORT$" '
  $4 ~ p {
    if (match($0, /pid=[0-9]+/)) {
      print substr($0, RSTART + 4, RLENGTH - 4)
    }
  }' | sort -u)

if [ -z "$pids" ]; then
    echo "[Web] 端口 $PORT 没有运行中的服务"
    exit 0
fi

echo "[Web] 关闭端口 $PORT 的进程: $pids"
kill $pids
sleep 1

if ss -tln 2>/dev/null | grep -q ":$PORT$"; then
    echo "[Web] 进程未退出，强制结束"
    kill -9 $pids
    sleep 1
fi

echo "[Web] 已关闭"
