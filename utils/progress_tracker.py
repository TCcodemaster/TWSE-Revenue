import threading
import time
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局進度追蹤器
progress = {
    'percentage': 0,
    'completed': 0,
    'total': 0,
    'current_company': '',
    'status': 'idle',  # idle, running, completed, error
    'last_update': time.time(),
    'lock': threading.Lock()
}

def initialize(total_tasks):
    """初始化進度追蹤"""
    with progress['lock']:
        progress.update({
            'percentage': 0,
            'completed': 0,
            'total': total_tasks,
            'current_company': '準備中...',
            'status': 'running',
            'last_update': time.time()
        })
        logger.info(f"初始化進度追蹤: {total_tasks} 個任務")

def update_company(company_id, year=None, month=None):
    """更新當前處理的公司資訊"""
    with progress['lock']:
        if year and month:
            progress['current_company'] = f"{company_id} {year}年{month}月"
        else:
            progress['current_company'] = company_id
        progress['last_update'] = time.time()

def increment():
    """增加已完成的任務數"""
    with progress['lock']:
        progress['completed'] += 1
        total = progress['total'] or 1  # 避免除零錯誤
        progress['percentage'] = min(99, round((progress['completed'] / total) * 100, 1))
        progress['last_update'] = time.time()

def complete():
    """標記任務已完成"""
    with progress['lock']:
        progress['completed'] = progress['total']
        progress['percentage'] = 100
        progress['status'] = 'completed'
        progress['current_company'] = '已完成'
        progress['last_update'] = time.time()
        logger.info("任務已完成")

def error(error_message):
    """標記發生錯誤"""
    with progress['lock']:
        progress['status'] = 'error'
        progress['last_update'] = time.time()
        logger.error(f"任務執行錯誤: {error_message}")

def get_status():
    """獲取當前進度狀態"""
    with progress['lock']:
        return {
            'percentage': progress['percentage'],
            'completed': progress['completed'],
            'total': progress['total'],
            'current_company': progress['current_company'],
            'status': progress['status'],
            'last_update': progress['last_update'],
            'time_since_update': f"{time.time() - progress['last_update']:.1f}秒"
        }