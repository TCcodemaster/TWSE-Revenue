import time
import functools
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def timer_decorator(log_level='info', log_args=False):
    """
    計時裝飾器：測量函數執行時間並記錄到日誌
    
    Args:
        log_level (str): 日誌級別 ('debug', 'info', 'warning', 'error')
        log_args (bool): 是否記錄函數參數
    
    Returns:
        function: 裝飾器函數
    
    Example:
        @timer_decorator(log_level='info', log_args=True)
        def my_function(x, y):
            # 函數內容
            return x + y
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 記錄開始時間
            start_time = time.time()
            
            # 記錄函數執行開始
            func_name = func.__qualname__  # 獲取完整函數名（包括類名）
            module_name = func.__module__  # 獲取模組名
            
            # 準備日誌訊息
            start_msg = f"開始執行 {module_name}.{func_name}"
            
            # 如果需要記錄參數
            if log_args and (args or kwargs):
                args_str = ', '.join(repr(arg) for arg in args)
                kwargs_str = ', '.join(f"{k}={repr(v)}" for k, v in kwargs.items())
                params = []
                if args_str:
                    params.append(args_str)
                if kwargs_str:
                    params.append(kwargs_str)
                params_str = ', '.join(params)
                start_msg += f" 參數：{params_str}"
            
            # 根據指定級別記錄日誌
            log_func = getattr(logger, log_level.lower(), logger.info)
            log_func(start_msg)
            
            try:
                # 執行被裝飾的函數
                result = func(*args, **kwargs)
                
                # 計算執行時間
                end_time = time.time()
                execution_time = end_time - start_time
                
                # 記錄執行結束和時間
                log_func(f"完成執行 {module_name}.{func_name} - 耗時: {execution_time:.6f} 秒")
                
                return result
            except Exception as e:
                # 計算執行時間（即使發生異常）
                end_time = time.time()
                execution_time = end_time - start_time
                
                # 記錄異常信息
                logger.error(f"執行 {module_name}.{func_name} 時發生錯誤 - 耗時: {execution_time:.6f} 秒 - 錯誤: {str(e)}")
                
                # 重新拋出異常
                raise
        
        return wrapper
    
    # 支持不帶參數的裝飾器用法
    if callable(log_level):
        func = log_level
        log_level = 'info'
        return decorator(func)
    
    return decorator
