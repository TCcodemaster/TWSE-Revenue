FROM python:3.9-slim

WORKDIR /app

# 設置環境變數
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP app.py
ENV FLASK_ENV production

# 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 創建非 root 用戶運行應用
RUN addgroup --system app && adduser --system --group app
RUN chown -R app:app /app
USER app

# 暴露連接埠
EXPOSE 8080

# 運行 Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]