#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Dict, Any, Optional

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 服务配置
API_V1_PREFIX = "/api/v1"
PROJECT_NAME = "身份证OCR识别服务"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
VERSION = "0.1.0"

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
WORKERS = int(os.getenv("WORKERS", "4"))  # 工作进程数

# OCR配置
OCR_MODEL_DIR = os.getenv("OCR_MODEL_DIR", str(BASE_DIR / "models"))
OCR_PROCESS_POOL_SIZE = int(os.getenv("OCR_PROCESS_POOL_SIZE", "4"))  # OCR处理进程池大小
OCR_TASK_TIMEOUT = int(os.getenv("OCR_TASK_TIMEOUT", "30"))  # OCR任务超时时间(秒)

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # 优化性能，减少日志输出
LOG_DIR = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))
LOG_FILENAME = os.getenv("LOG_FILENAME", "sfzocr.log")
LOG_ROTATION = os.getenv("LOG_ROTATION", "20 MB")
LOG_RETENTION = os.getenv("LOG_RETENTION", "1 week")

# 创建必要的目录
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OCR_MODEL_DIR, exist_ok=True)

# 身份证识别配置
ID_CARD_CONFIG = {
    "use_angle_cls": False,  # 禁用角度分类器以提高速度
    "det": True,            # 使用文本检测
    "rec": True,            # 使用文本识别
    "cls": True,            # 使用方向分类
    # 移除不支持的参数
    # "type": "structure",    # 结构化识别
}

# 身份证字段映射配置
ID_CARD_FIELD_MAPPING = {
    "姓名": "name",
    "性别": "sex",
    "民族": "nation",
    "出生": "birth",
    "住址": "address",
    "公民身份号码": "id_number",
    "签发机关": "issue_authority",
    "有效期限": "valid_period",
}

# CORS配置
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "*",
]

# 安全配置
ALLOWED_HOSTS = ["*"]
API_KEY_HEADER = "X-API-KEY"
API_KEYS = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []
