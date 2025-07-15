#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import logging
from loguru import logger

from app.config import LOG_LEVEL, LOG_DIR, LOG_FILENAME, LOG_ROTATION, LOG_RETENTION

# 日志文件路径
log_file_path = Path(LOG_DIR) / LOG_FILENAME

# 配置loguru
logger.remove()  # 移除默认的处理器

# 添加控制台输出处理器
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True
)

# 添加文件输出处理器
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level=LOG_LEVEL,
    rotation=LOG_ROTATION,
    retention=LOG_RETENTION,
    encoding="utf-8"
)

# 创建一个拦截标准库日志的处理器
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # 获取对应的Loguru级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 查找调用者
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # 使用loguru记录日志
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# 配置标准库日志到loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# 为第三方库配置日志
for _log_name in ["uvicorn", "uvicorn.error", "fastapi"]:
    _logger = logging.getLogger(_log_name)
    _logger.handlers = [InterceptHandler()]

# 定义一个函数来获取logger
def get_logger(name: str = "sfzocr"):
    """
    获取logger实例
    
    Args:
        name: 日志名称
        
    Returns:
        loguru.logger实例
    """
    return logger.bind(name=name)

# 定义请求日志记录函数
async def log_request(request, response_status, response_time):
    """
    记录HTTP请求日志
    
    Args:
        request: FastAPI请求对象
        response_status: 响应状态码
        response_time: 响应时间(ms)
    """
    level = "INFO" if response_status < 400 else "ERROR"
    
    logger.log(
        level,
        f"Request: {request.method} {request.url.path} | Status: {response_status} | Time: {response_time:.2f}ms | "
        f"Client: {request.client.host if request.client else 'Unknown'}"
    )
