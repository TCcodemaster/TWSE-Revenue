# TWSE 公司月營收查詢系統 - PWA 版本

![TWSE 公司月營收查詢系統](https://img.shields.io/badge/TWSE-月營收查詢系統-blue)
![PyPI - Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0.1-green)
![PWA](https://img.shields.io/badge/PWA-Supported-orange)

這是一個用於查詢台灣上市公司月營收資料的跨平台應用程式，通過 PWA (Progressive Web App) 技術實現，能夠在桌面和移動裝置上使用。

## 功能特點

- 🔍 查詢上市公司月營收資料
- 📊 使用 Highcharts 進行數據視覺化
- 📱 響應式設計，適配各種屏幕尺寸
- 🌐 支援離線工作模式
- 💾 可安裝到桌面或移動裝置
- 📝 保存查詢歷史記錄

## 安裝與運行

### 安裝相依套件

```bash
pip install -r requirements.txt
```

### 啟動應用

```bash
python app.py
```

應用將在 <http://127.0.0.1:5000> 運行。

### 部署到生產環境

對於生產環境，建議使用 Gunicorn 作為 WSGI 伺服器：

```bash
gunicorn -w 4 app:app
```

或者，您可以使用其他 WSGI 伺服器如 uWSGI，或部署至雲平台如 Heroku、Google Cloud Platform 等。

## PWA 支援

本應用程式支援 PWA 功能，可以安裝到桌面或移動裝置：

1. 在 Chrome、Edge 或 Safari 等現代瀏覽器中打開應用
2. 在桌面瀏覽器，點擊地址欄右側的「安裝」圖標
3. 在移動瀏覽器，點擊選單中的「添加到主屏幕」選項

安裝後，應用將作為獨立應用運行，並支援部分離線功能。

## 使用指南

1. 輸入公司代號（以逗號分隔多個公司）
2. 選擇年份範圍（如 111-112）
3. 選擇月份範圍（如 1-12 或 1-3）
4. 點擊「開始查詢」按鈕
5. 查看數據表格和各種圖表分析

## 開發指南

### 文件結構

```
stock_app/
│
├── app.py                  # Flask 應用主入口
├── config.py               # 配置文件
├── requirements.txt        # 依賴包清單
│
├── static/                 # 靜態資源目錄
│   ├── css/
│   │   └── style.css       # 自定義樣式
│   ├── js/
│   │   ├── main.js         # 主要 JavaScript 功能
│   │   └── pwa-register.js # PWA 註冊
│   ├── service-worker.js   # Service Worker
│   ├── manifest.json       # PWA 清單
│   └── icons/              # PWA 圖標
│
├── templates/              # HTML 模板目錄
│   ├── base.html           # 基礎模板
│   ├── index.html          # 首頁 
│   ├── offline.html        # 離線頁面
│   ├── 404.html            # 404 錯誤頁面
│   └── 500.html            # 500 錯誤頁面
│
└── utils/                  # 工具函數目錄
    ├── __init__.py
    ├── scraper.py          # 網頁爬蟲功能
    └── data_processor.py   # 資料處理功能
```

### 緩存策略

本專案採用兩層緩存架構：

1. **記憶體緩存 (Flask-Caching)**
   - 速度最快
   - 僅在應用運行期間有效
   - 適合短期、高頻訪問數據

2. **SQLite 數據庫**
   - 存取相對較慢
   - 最持久可靠
   - 適合長期數據存儲和歷史記錄

### 技術堆疊

- **後端**: Flask, Python
- **前端**: HTML5, CSS3, JavaScript, Bootstrap 5
- **數據視覺化**: Highcharts.js
- **PWA**: Service Worker, manifest.json
- **爬蟲技術**: Requests, BeautifulSoup4

### 自定義開發

- 若要添加新功能，請在 `utils` 目錄中創建相應的模組
- 前端樣式可在 `static/css/style.css` 中自定義
- 若要修改 PWA 行為，請編輯 `static/service-worker.js` 和 `static/js/pwa-register.js`

## 注意事項

- 本應用依賴於台灣證券交易所的公開資訊觀測站，若其網站結構變更，可能需要更新爬蟲模組
- 請遵守台灣證券交易所的使用條款和相關法規
- 本應用設計用於個人使用，請勿過度頻繁地訪問目標網站

## License

MIT License
