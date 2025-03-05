FROM python:3.9-slim

# 設置非交互模式
ENV DEBIAN_FRONTEND=noninteractive

# 設置工作目錄
WORKDIR /app

# 設置所有環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  FLASK_APP=app.py \
  FLASK_ENV=production

# 安裝系統依賴
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl \
  gcc \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gevent

# 複製應用代碼
COPY . .

# 在應用目錄內創建必要的目錄
RUN mkdir -p /app/cache /app/data

# 創建非 root 用戶運行應用
RUN addgroup --system app && \
  adduser --system --group app && \
  chown -R app:app /app

# 切換到非 root 用戶
USER app

# 暴露連接埠
EXPOSE 8082

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8082/ || exit 1

# 啟動命令
CMD ["gunicorn", "--timeout", "120", "--workers", "2", "--worker-class", "gevent", "--worker-connections", "1000", "--bind", "0.0.0.0:8082", "app:app"]