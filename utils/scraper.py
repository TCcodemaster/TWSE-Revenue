import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import json
import time
from functools import lru_cache

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 建立快取目錄
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(company_id, year, month):
    """獲取快取文件路徑"""
    return os.path.join(CACHE_DIR, f"{company_id}_{year}_{month}.json")

def save_to_cache(company_id, year, month, data):
    """保存數據到快取"""
    try:
        cache_path = get_cache_path(company_id, year, month)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"保存快取時出錯: {e}")

def load_from_cache(company_id, year, month):
    """從快取加載數據"""
    cache_path = get_cache_path(company_id, year, month)
    if os.path.exists(cache_path):
        try:
            # 檢查快取文件是否過期（7天）
            if time.time() - os.path.getmtime(cache_path) < 7 * 24 * 60 * 60:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"讀取快取時出錯: {e}")
    return None

@lru_cache(maxsize=128)
def fetch_url(url, timeout=5):
    """獲取URL內容，帶有重試機制和記憶體快取"""
    for attempt in range(3):  # 嘗試3次
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"第{attempt+1}次請求失敗: {url}, 錯誤: {e}")
            if attempt == 2:  # 最後一次嘗試
                logger.error(f"請求失敗: {url}, 錯誤: {e}")
                return None
            time.sleep(1)  # 等待1秒後重試

def get_company_basic_data(company_id, year, month, html_content):
    """從HTML內容解析特定公司的數據"""
    if not html_content:
        return {}

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        target_table = soup.find('table')

        if target_table:
            rows = target_table.find_all('tr')[2:]  # 忽略前兩行

            for row in rows:
                columns = row.find_all('td')
                if columns:
                    fetched_company_id = columns[0].text.strip()
                    if fetched_company_id == company_id:
                        company_name = columns[1].text.strip().encode('latin-1').decode('big5', 'ignore')
                        monthly_revenue = columns[2].text.strip()
                        last_month_revenue = columns[3].text.strip()
                        last_year_month_revenue = columns[4].text.strip()
                        monthly_growth_rate = columns[5].text.strip()
                        last_year_growth_rate = columns[6].text.strip()

                        data = {
                            '公司代號': fetched_company_id,
                            '公司名稱': company_name,
                            '當月營收': monthly_revenue,
                            '上月營收': last_month_revenue,
                            '去年當月營收': last_year_month_revenue,
                            '上月比較增減(%)': monthly_growth_rate,
                            '去年同月增減(%)': last_year_growth_rate,
                            '月份': f'{year}-{month:02d}'
                        }
                        
                        return data
    except Exception as e:
        logger.error(f"解析數據時發生錯誤: {e}")

    return {}

def process_company_data(args):
    """處理單個公司的數據，用於多線程執行"""
    company_id, year, month = args
    base_url = 'https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_{year}_{month}_0.html'
    url = base_url.format(year=year, month=month)
    
    # 嘗試從快取加載
    cached_data = load_from_cache(company_id, year, month)
    if cached_data:
        logger.info(f"從快取獲取 {company_id} {year}年{month}月 的數據")
        return cached_data
    
    # 快取不存在，抓取數據
    logger.info(f"抓取 {company_id} {year}年{month}月 的數據")
    html_content = fetch_url(url)
    data = get_company_basic_data(company_id, year, month, html_content)
    
    # 如果成功獲取數據，保存到快取
    if data:
        save_to_cache(company_id, year, month, data)
    
    return data

def get_company_data(company_ids, year_range, month_range):
    """並行抓取指定公司在指定年月範圍內的數據"""
    # 生成所有任務參數
    tasks = [(company_id, year, month) for company_id in company_ids 
             for year in year_range for month in month_range]
    
    results = []
    
    # 使用線程池並行執行
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 提交所有任務
        future_to_task = {executor.submit(process_company_data, task): task for task in tasks}
        
        # 收集結果
        for future in future_to_task:
            data = future.result()
            if data:
                results.append(data)
    
    logger.info(f"抓取完成，共獲取 {len(results)} 筆數據")
    return results