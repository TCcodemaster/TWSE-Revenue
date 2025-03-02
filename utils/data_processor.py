from itertools import groupby
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_range(input_range):
    """
    解析用户输入的范围
    
    Args:
        input_range (list): 包含范围字符串的列表，如 ["111-112"]
        
    Returns:
        list: 解析后的整数列表
    """
    result = []
    for part in input_range:
        if '-' in part:
            start, end = map(int, part.split('-'))
            result.extend(range(start, end + 1))
        else:
            result.append(int(part))
    return result

def calculate_yearly_averages(sorted_data, year_range):
    """
    計算每年度的平均營收
    
    Args:
        sorted_data (list): 排序後的公司資料列表
        year_range (list): 年份範圍
        
    Returns:
        dict: 以公司代號為鍵，包含年度平均營收的字典
    """
    result = {}
    
    # 按公司代號分組
    for company_id, group in groupby(sorted_data, key=lambda x: x['公司代號']):
        group_list = list(group)
        
        # 初始化該公司的年度資料
        if company_id not in result:
            result[company_id] = {}
        
        # 計算每年度的平均值
        yearly_data = {year: [] for year in year_range}
        
        for company in group_list:
            year = int(company['月份'].split('-')[0])
            
            # 確保年份在範圍內
            if year in yearly_data:
                try:
                    # 去除逗號並轉換為浮點數
                    revenue = float(company['當月營收'].replace(',', ''))
                    yearly_data[year].append(revenue)
                except (ValueError, KeyError) as e:
                    logger.warning(f"處理 {company_id} {year} 年數據時出錯: {e}")
        
        # 計算平均值
        for year, revenues in yearly_data.items():
            if revenues:  # 確保有數據才計算平均值
                result[company_id][year] = sum(revenues) / len(revenues)
            else:
                result[company_id][year] = 0
    
    return result

def prepare_chart_data(sorted_data, chart_type='revenue'):
    """
    準備 Highcharts 圖表所需的數據格式
    
    Args:
        sorted_data (list): 排序後的公司資料列表
        chart_type (str): 圖表類型，可選 'revenue', 'growth_rate', 'yearly'
        
    Returns:
        dict: 圖表所需的數據
    """
    chart_data = {'categories': [], 'series': []}
    
    # 按公司代號分組
    company_groups = {}
    for item in sorted_data:
        company_id = item['公司代號']
        if company_id not in company_groups:
            company_groups[company_id] = []
        company_groups[company_id].append(item)
    
    # 確保每個組都按月份排序
    for company_id, group in company_groups.items():
        company_groups[company_id] = sorted(group, key=lambda x: x['月份'])
    
    # 收集所有月份作為類別
    all_months = set()
    for group in company_groups.values():
        all_months.update(item['月份'] for item in group)
    
    # 將月份轉換為排序後的列表
    chart_data['categories'] = sorted(list(all_months))
    
    # 根據圖表類型準備系列數據
    for company_id, group in company_groups.items():
        company_name = group[0]['公司名稱'] if group else company_id
        
        if chart_type == 'revenue':
            # 營收數據
            revenue_data = []
            for month in chart_data['categories']:
                found = False
                for item in group:
                    if item['月份'] == month:
                        revenue_data.append(float(item['當月營收'].replace(',', '')))
                        found = True
                        break
                if not found:
                    revenue_data.append(None)  # 使用 None 表示缺失數據
            
            chart_data['series'].append({
                'name': f"{company_id} {company_name}",
                'data': revenue_data
            })
            
        elif chart_type == 'growth_rate':
            # 增長率數據
            growth_data = []
            for month in chart_data['categories']:
                found = False
                for item in group:
                    if item['月份'] == month:
                        try:
                            growth_data.append(float(item['上月比較增減(%)']))
                        except ValueError:
                            growth_data.append(None)
                        found = True
                        break
                if not found:
                    growth_data.append(None)
            
            chart_data['series'].append({
                'name': f"{company_id} {company_name}",
                'data': growth_data
            })
    
    return chart_data

def prepare_yearly_comparison_data(sorted_data, company_id):
    """
    準備單一公司的年度比較數據
    
    Args:
        sorted_data (list): 排序後的公司資料列表
        company_id (str): 要比較的公司代號
        
    Returns:
        dict: 年度比較圖表所需的數據
    """
    # 過濾選定公司的數據
    company_data = [item for item in sorted_data if item['公司代號'] == company_id]
    
    if not company_data:
        return None
    
    # 按年份分組
    year_groups = {}
    for item in company_data:
        year = item['月份'].split('-')[0]
        if year not in year_groups:
            year_groups[year] = []
        year_groups[year].append(item)
    
    # 準備圖表數據
    chart_data = {
        'categories': [f"{i:02d}" for i in range(1, 13)],  # 1-12 月
        'series': []
    }
    
    # 為每一年準備一個數據系列
    for year, group in year_groups.items():
        # 按月份排序
        group = sorted(group, key=lambda x: int(x['月份'].split('-')[1]))
        
        # 收集每月數據
        monthly_data = [None] * 12  # 初始化 12 個月的數據為 None
        
        for item in group:
            month_idx = int(item['月份'].split('-')[1]) - 1  # 轉為 0-based index
            if 0 <= month_idx < 12:  # 確保索引有效
                try:
                    monthly_data[month_idx] = float(item['當月營收'].replace(',', ''))
                except ValueError:
                    pass  # 保持為 None
        
        chart_data['series'].append({
            'name': f"{year} 年",
            'data': monthly_data
        })
    
    return chart_data