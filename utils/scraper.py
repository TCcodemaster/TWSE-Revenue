import requests
from bs4 import BeautifulSoup
from itertools import product
from tqdm import tqdm
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_company_basic_data(company_id, url):
    """
    從指定 URL 爬取特定公司 ID 的數據
    
    Args:
        company_id (str): 公司代號
        url (str): 資料來源 URL
        
    Returns:
        dict: 包含公司數據的字典，失敗則返回空字典
    """
    data = {}

    try:
        # 發送 HTTP 請求
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 如果請求不成功，會拋出異常

        # 使用 BeautifulSoup 解析 HTML 內容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 找到指定的表格
        target_table = soup.find('table')

        # 提取表格中的數據
        if target_table:
            rows = target_table.find_all('tr')[2:]  # 忽略前兩行，因為它們是表頭

            for row in rows:
                columns = row.find_all('td')
                if columns:  # 確保這是一行數據，而不是空行
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
                            '去年同月增減(%)': last_year_growth_rate
                        }
                        
                        return data  # 找到數據後立即返回

    except requests.RequestException as e:
        logger.error(f"請求錯誤: {e}")
    except Exception as e:
        logger.error(f"處理數據時發生錯誤: {e}")

    return data  # 如果找不到指定公司 ID 的數據，返回空字典

def get_company_data(company_ids, year_range, month_range):
    """
    爬取指定公司在指定年月範圍內的數據
    
    Args:
        company_ids (list): 公司代號列表
        year_range (list): 年份範圍
        month_range (list): 月份範圍
        
    Returns:
        list: 包含所有公司數據的列表
    """
    data = []
    base_url = 'https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_{year}_{month}_0.html'

    # 估算迴圈的總長度
    total_iterations = len(company_ids) * len(year_range) * len(month_range)
    
    logger.info(f"開始爬取數據，共 {total_iterations} 個請求...")

    # 使用 product 函數生成所有可能的組合
    for company_id, year, month in product(company_ids, year_range, month_range):
        url = base_url.format(year=year, month=month)
        logger.info(f"爬取 {company_id} {year}年{month}月 的數據")
        
        company_data = get_company_basic_data(company_id, url)

        if company_data:
            company_data['月份'] = f'{year}-{month:02d}'
            data.append(company_data)

    logger.info(f"爬取完成，共獲取 {len(data)} 筆數據")
    return data