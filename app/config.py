#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
身份证OCR识别服务配置文件

本配置文件包含了所有可调整的配置项，根据服务器性能和业务需求进行优化。
配置项通过环境变量覆盖默认值，便于不同环境的部署。

性能调优说明：
- 🚀 高性能服务器：增加进程数、并发数、减少内存优化
- 💾 内存受限服务器：减少进程数、启用内存优化、调整日志级别
- 🔧 生产环境：关闭DEBUG、增加超时时间、配置API密钥
"""

import os
import psutil
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# ============================================================================
# 🔧 环境变量加载
# ============================================================================

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 定义安全打印函数
def safe_print(text):
    """安全打印函数，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 移除表情符号，使用简单字符
        emoji_replacements = {
            "🚀": "[START]",
            "📡": "[SERVICE]", 
            "⚡": "[PERFORMANCE]",
            "🔍": "[OCR]",
            "📝": "[LOG]",
            "🔐": "[SECURITY]",
            "💡": "[INFO]",
            "🌐": "[API]",
            "🎯": "[READY]",
            "✅": "[OK]",
            "❌": "[ERROR]",
            "⚠️": "[WARNING]",
            "💾": "[MEMORY]",
            "🔧": "[CONFIG]",
            "🗄️": "[CACHE]"
        }
        
        safe_text = text
        for emoji, replacement in emoji_replacements.items():
            safe_text = safe_text.replace(emoji, replacement)
        
        try:
            print(safe_text)
        except UnicodeEncodeError:
            # 如果还是有问题，使用ASCII编码
            print(safe_text.encode('ascii', errors='ignore').decode('ascii'))

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv

    # 查找 .env 文件
    env_files = [
        BASE_DIR / ".env",           # 项目根目录
        BASE_DIR / "config.env",     # 配置文件
        Path.cwd() / ".env",         # 当前工作目录
    ]
    
    env_loaded = False
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file)
            safe_print(f"✅ 已加载环境配置文件: {env_file}")
            env_loaded = True
            break
    
    if not env_loaded:
        safe_print("💡 未找到 .env 配置文件，使用默认配置和系统环境变量")
        
except ImportError:
    safe_print("⚠️  python-dotenv 未安装，请运行: pip install python-dotenv")
    safe_print("   将使用系统环境变量和默认配置")
    BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# 基础配置（一般不需要修改）
# ============================================================================

# API版本前缀
API_V1_PREFIX = "/api/v1"

# 项目名称和版本
PROJECT_NAME = "身份证OCR识别服务"
VERSION = "0.1.4"

# ============================================================================
# 🔧 服务器性能相关配置（重点调优）
# ============================================================================

# 是否启用调试模式
# 📌 性能影响：DEBUG模式会输出更多日志，影响性能
# 🚀 高性能：False  💾 内存受限：False  🔧 生产环境：False
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# 服务监听地址
# 📌 说明：0.0.0.0 监听所有网卡，127.0.0.1 仅本地访问
HOST = os.getenv("HOST", "0.0.0.0")

# 服务监听端口
PORT = int(os.getenv("PORT", "8000"))

# Uvicorn工作进程数
# 📌 性能影响：影响并发处理能力和内存占用
# 🚀 高性能：CPU核心数 * 2（如：8）  💾 内存受限：1-2  🔧 生产环境：CPU核心数
# ⚠️  注意：每个进程都会加载OCR模型，内存占用约1-2GB
WORKERS = int(os.getenv("WORKERS", "1"))

# ============================================================================
# 🧠 OCR引擎性能配置（核心调优）
# ============================================================================

# OCR模型文件目录
# 📌 说明：模型文件路径，确保有足够的磁盘空间（约500MB-1GB）
OCR_MODEL_DIR = os.getenv("OCR_MODEL_DIR", str(BASE_DIR / "models"))

# OCR处理进程池大小
# 📌 性能影响：影响并发OCR处理能力和内存占用
# 🚀 高性能：4-8  💾 内存受限：1-2  🔧 生产环境：2-4
# ⚠️  重要：每个进程占用约1GB内存，根据可用内存调整
# 计算公式：可用内存(GB) / 1.5 = 推荐进程数
OCR_PROCESS_POOL_SIZE = int(os.getenv("OCR_PROCESS_POOL_SIZE", "2"))

# OCR任务超时时间（秒）
# 📌 性能影响：防止任务卡死，影响用户体验
# 🚀 高性能：15-30  💾 内存受限：30-60  🔧 生产环境：30
OCR_TASK_TIMEOUT = int(os.getenv("OCR_TASK_TIMEOUT", "30"))

# ============================================================================
# 💾 内存优化配置（内存受限服务器重点关注）
# ============================================================================

# 是否启用内存优化
# 📌 性能影响：启用后会定期清理内存，轻微影响性能但大幅降低内存占用
# 🚀 高性能：False  💾 内存受限：True  🔧 生产环境：True
MEMORY_OPTIMIZATION = os.getenv("MEMORY_OPTIMIZATION", "True").lower() in ("true", "1", "t")

# 最大并发请求数
# 📌 性能影响：限制同时处理的请求数量，防止内存溢出
# 🚀 高性能：10-20  💾 内存受限：2-5  🔧 生产环境：5-10
# 计算公式：OCR_PROCESS_POOL_SIZE * 2 = 推荐并发数
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "3"))

# 请求处理完成后是否强制垃圾回收
# 📌 性能影响：会稍微增加响应时间，但能有效降低内存占用
# 🚀 高性能：False  💾 内存受限：True  🔧 生产环境：True
ENABLE_GC_AFTER_REQUEST = os.getenv("ENABLE_GC_AFTER_REQUEST", "True").lower() in ("true", "1", "t")

# ============================================================================
# 🗄️ 请求缓存配置（性能优化）
# ============================================================================

# 是否启用请求缓存
# 📌 性能影响：缓存可以显著提高重复请求的响应速度，但会占用内存
# 🚀 高性能：True  💾 内存受限：False  🔧 生产环境：True
# 说明：缓存相同图片的OCR识别结果，避免重复计算
ENABLE_REQUEST_CACHE = os.getenv("ENABLE_REQUEST_CACHE", "False").lower() in ("true", "1", "t")

# 缓存最大数量
# 📌 性能影响：每个缓存项约占用1-5KB内存（不包括图片）
# 🚀 高性能：1000-5000  💾 内存受限：100-500  🔧 生产环境：1000-2000
# 计算公式：可用内存(MB) / 2 = 推荐缓存数量
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))

# 缓存过期时间（秒）
# 📌 性能影响：影响缓存的有效性和内存占用时间
# 🚀 高性能：1800-3600（30分钟-1小时）  💾 内存受限：600-1800（10-30分钟）  🔧 生产环境：3600-7200（1-2小时）
# 说明：超过此时间的缓存项将被自动清理
CACHE_EXPIRE_TIME = int(os.getenv("CACHE_EXPIRE_TIME", "3600"))

# 缓存键计算方式
# 📌 性能影响：影响缓存命中率和计算开销
# 可选值：md5（快速）, sha256（安全）, content_hash（内容相关）
# 🚀 高性能：md5  💾 内存受限：md5  🔧 生产环境：sha256
CACHE_KEY_METHOD = os.getenv("CACHE_KEY_METHOD", "md5")

# 是否缓存调试模式的结果
# 📌 说明：调试模式返回原始OCR文本，通常不需要缓存
# 🚀 高性能：False  💾 内存受限：False  🔧 生产环境：False
CACHE_DEBUG_RESULTS = os.getenv("CACHE_DEBUG_RESULTS", "False").lower() in ("true", "1", "t")

# 缓存统计信息记录
# 📌 性能影响：记录缓存命中率等统计信息，轻微影响性能
# 🚀 高性能：True  💾 内存受限：False  🔧 生产环境：True
CACHE_ENABLE_STATS = os.getenv("CACHE_ENABLE_STATS", "True").lower() in ("true", "1", "t")

# ============================================================================
# 📝 日志配置（影响磁盘I/O和内存）
# ============================================================================

# 日志级别
# 📌 性能影响：DEBUG > INFO > WARNING > ERROR，级别越低日志越多
# 🚀 高性能：INFO  💾 内存受限：WARNING  🔧 生产环境：WARNING
# 可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")

# 日志文件目录
LOG_DIR = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))

# 日志文件名
LOG_FILENAME = os.getenv("LOG_FILENAME", "sfzocr.log")

# 日志文件轮转大小
# 📌 性能影响：影响磁盘空间占用和I/O性能
# 🚀 高性能：50 MB  💾 内存受限：20 MB  🔧 生产环境：50 MB
LOG_ROTATION = os.getenv("LOG_ROTATION", "20 MB")

# 日志文件保留时间
# 📌 性能影响：影响磁盘空间占用
# 🚀 高性能：2 weeks  💾 内存受限：1 week  🔧 生产环境：1 month
LOG_RETENTION = os.getenv("LOG_RETENTION", "1 week")

# ============================================================================
# 🔒 安全配置
# ============================================================================

# API密钥验证头部名称
API_KEY_HEADER = "X-API-KEY"

# API密钥列表（通过环境变量配置，多个密钥用逗号分隔）
# 📌 安全建议：生产环境必须配置强密钥
# 🔧 生产环境：必须配置（如：export API_KEYS="key1,key2,key3"）
# 🧪 测试环境：可以不配置
API_KEYS = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []

# 允许的主机名（FastAPI ALLOWED_HOSTS）
ALLOWED_HOSTS = ["*"]  # 生产环境建议配置具体域名

# ============================================================================
# 🌐 网络配置
# ============================================================================

# CORS跨域配置
# 📌 安全建议：生产环境应配置具体的前端域名
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "*",  # 生产环境建议移除或替换为具体域名
]

# ============================================================================
# 🎯 OCR引擎具体配置
# ============================================================================

# 🚀 OCR性能优化配置 - v0.1.4新增
OCR_PERFORMANCE_CONFIG = {
    # 🏃‍♂️ 快速模式：牺牲少量精度换取更快的识别速度
    "enable_fast_mode": os.getenv("OCR_FAST_MODE", "false").lower() == "true",     # true false
    
    # 📏 图像预处理优化
    "max_image_size": int(os.getenv("OCR_MAX_IMAGE_SIZE", "1600")),  # 最大图像尺寸（像素）
    "resize_quality": int(os.getenv("OCR_RESIZE_QUALITY", "85")),   # 图像压缩质量（0-100）
    
    # 🔧 PaddleOCR性能参数
    "det_limit_side_len": int(os.getenv("OCR_DET_LIMIT_SIDE_LEN", "960")),  # 检测模型输入尺寸限制
    "rec_batch_num": int(os.getenv("OCR_REC_BATCH_NUM", "6")),              # 识别批次大小
    "max_text_length": int(os.getenv("OCR_MAX_TEXT_LENGTH", "25")),         # 最大文本长度
    "cpu_threads": int(os.getenv("OCR_CPU_THREADS", "4")),                  # CPU线程数
    
    # 🎯 检测和识别阈值优化
    "det_db_thresh": float(os.getenv("OCR_DET_DB_THRESH", "0.3")),          # 检测阈值
    "det_db_box_thresh": float(os.getenv("OCR_DET_DB_BOX_THRESH", "0.6")),  # 检测框阈值
    "drop_score": float(os.getenv("OCR_DROP_SCORE", "0.5")),                # 识别置信度阈值
    
    # 💾 内存优化
    "enable_memory_optimization": MEMORY_OPTIMIZATION,
    "clear_cache_after_recognition": ENABLE_GC_AFTER_REQUEST,
}

# PaddleOCR配置参数
# 📌 性能影响：这些参数直接影响OCR识别速度和准确率
ID_CARD_CONFIG = {
    # 是否使用角度分类器（影响识别速度）
    # 🚀 高性能：False（更快）  🎯 高精度：True（更准确）
    "use_angle_cls": False,
    
    # 是否启用文本检测
    "det": True,
    
    # 是否启用文本识别  
    "rec": True,
    
    # 是否启用方向分类
    # 📌 性能影响：启用会稍微影响速度但提高准确率
    "cls": True,
}

# 身份证字段映射配置（OCR识别结果到JSON字段的映射）
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

# ============================================================================
# 🆔 外国人永久居留身份证配置
# ============================================================================

# 外国人永久居留身份证字段映射配置
FOREIGN_ID_CARD_FIELD_MAPPING = {
    # 新版外国人永久居留身份证字段映射
    "new": {
        "中文姓名": "chinese_name",
        "英文姓名": "english_name", 
        "姓名": "chinese_name",  # 备用映射
        "Name": "english_name",   # 备用映射
        "性别": "sex",
        "Sex": "sex",
        "出生日期": "birth_date",
        "出生": "birth_date",
        "Date of Birth": "birth_date",
        "国籍": "nationality",
        "Nationality": "nationality",
        "永久居留证号码": "residence_number",
        "证件号码": "residence_number",
        "签发机关": "issue_authority",
        "签发日期": "issue_date",
        "有效期限": "valid_until",
        "有效期至": "valid_until",
    },
    # 旧版外国人永久居留身份证字段映射
    "old": {
        "中文姓名": "chinese_name",
        "英文姓名": "english_name",
        "姓名": "chinese_name",
        "Name": "english_name",
        "性别": "sex",
        "Sex": "sex",
        "出生日期": "birth_date",
        "出生": "birth_date",
        "Date of Birth": "birth_date",
        "国籍": "nationality", 
        "Nationality": "nationality",
        "永久居留证号码": "residence_number",
        "证件号码": "residence_number",
        "签发机关": "issue_authority",
        "签发日期": "issue_date",
        "有效期限": "valid_until",
        "有效期至": "valid_until",
    }
}

# 外国人永久居留身份证OCR配置
FOREIGN_ID_CARD_CONFIG = {
    # 新版外国人永久居留身份证配置
    "new": {
        "use_angle_cls": True,    # 新版可能需要角度分类
        "det": True,
        "rec": True,
        "cls": True,
        "lang": "ch",             # 主要语言为中文
        "enable_english": True,   # 启用英文识别
    },
    # 旧版外国人永久居留身份证配置
    "old": {
        "use_angle_cls": False,   # 旧版通常不需要角度分类
        "det": True,
        "rec": True,
        "cls": True,
        "lang": "ch",             # 主要语言为中文
        "enable_english": True,   # 启用英文识别
    }
}

# ============================================================================
# 📁 目录初始化
# ============================================================================

# 创建必要的目录
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OCR_MODEL_DIR, exist_ok=True)

# ============================================================================
# 🔧 服务器配置建议
# ============================================================================

def get_system_info() -> Dict[str, Any]:
    """
    获取系统硬件信息
    
    Returns:
        Dict[str, Any]: 系统信息字典
    """
    try:
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        disk_usage = psutil.disk_usage('/')
        
        return {
            "cpu_cores": cpu_count,
            "cpu_logical": psutil.cpu_count(logical=True),
            "memory_total_gb": memory.total / (1024**3),
            "memory_available_gb": memory.available / (1024**3),
            "memory_percent": memory.percent,
            "disk_total_gb": disk_usage.total / (1024**3),
            "disk_free_gb": disk_usage.free / (1024**3),
            "disk_percent": (disk_usage.used / disk_usage.total) * 100,
            "platform": platform.system(),
            "platform_version": platform.release(),
            "python_version": platform.python_version(),
        }
    except Exception as e:
        return {
            "error": f"无法获取系统信息: {e}",
            "cpu_cores": 4,  # 默认值
            "memory_total_gb": 8.0,  # 默认值
            "memory_available_gb": 4.0,  # 默认值
        }

def analyze_configuration() -> Dict[str, Any]:
    """
    分析当前配置的合理性
    
    Returns:
        Dict[str, Any]: 配置分析结果
    """
    system_info = get_system_info()
    analysis = {
        "status": "optimal",  # optimal, warning, critical
        "issues": [],
        "suggestions": [],
        "warnings": [],
        "memory_analysis": {},
        "performance_score": 100,  # 0-100分
    }
    
    # 内存分析
    ocr_memory_usage = OCR_PROCESS_POOL_SIZE * 1.2  # 每个OCR进程约1.2GB
    worker_memory_usage = WORKERS * 0.5  # 每个Worker进程约0.5GB
    total_estimated_memory = ocr_memory_usage + worker_memory_usage + 1.0  # 系统预留1GB
    
    memory_ratio = total_estimated_memory / system_info.get("memory_total_gb", 8.0)
    
    analysis["memory_analysis"] = {
        "ocr_memory_gb": ocr_memory_usage,
        "worker_memory_gb": worker_memory_usage,
        "total_estimated_gb": total_estimated_memory,
        "system_total_gb": system_info.get("memory_total_gb", 8.0),
        "system_available_gb": system_info.get("memory_available_gb", 4.0),
        "usage_ratio": memory_ratio,
        "recommended_max_memory": system_info.get("memory_total_gb", 8.0) * 0.8,  # 建议最大使用80%内存
    }
    
    # 检查内存配置
    if memory_ratio > 0.9:
        analysis["status"] = "critical"
        analysis["issues"].append(f"💀 严重: 预估内存使用{total_estimated_memory:.1f}GB超过系统总内存{system_info.get('memory_total_gb', 8.0):.1f}GB的90%")
        analysis["suggestions"].append("立即减少OCR进程数或Worker进程数")
        analysis["performance_score"] -= 30
    elif memory_ratio > 0.8:
        analysis["status"] = "warning"
        analysis["warnings"].append(f"⚠️  警告: 预估内存使用{total_estimated_memory:.1f}GB接近系统总内存{system_info.get('memory_total_gb', 8.0):.1f}GB的80%")
        analysis["suggestions"].append("建议启用内存优化或适当减少进程数")
        analysis["performance_score"] -= 15
    
    # 检查可用内存
    if total_estimated_memory > system_info.get("memory_available_gb", 4.0):
        analysis["warnings"].append(f"⚠️  当前可用内存{system_info.get('memory_available_gb', 4.0):.1f}GB可能不足")
        analysis["suggestions"].append("建议释放系统内存或重启服务器")
    
    # CPU配置分析
    cpu_cores = system_info.get("cpu_cores", 4)
    if WORKERS > cpu_cores * 2:
        analysis["warnings"].append(f"⚠️  Worker进程数({WORKERS})超过CPU核心数({cpu_cores})的2倍")
        analysis["suggestions"].append(f"建议将Worker进程数设置为{cpu_cores}-{cpu_cores*2}之间")
        analysis["performance_score"] -= 10
    elif WORKERS == 1 and cpu_cores > 2:
        analysis["suggestions"].append(f"可以增加Worker进程数到{min(cpu_cores, 4)}以提高并发能力")
    
    # OCR进程配置分析
    if OCR_PROCESS_POOL_SIZE > cpu_cores:
        analysis["warnings"].append(f"⚠️  OCR进程数({OCR_PROCESS_POOL_SIZE})超过CPU核心数({cpu_cores})")
        analysis["suggestions"].append(f"建议将OCR进程数设置为{min(cpu_cores, 4)}")
        analysis["performance_score"] -= 10
    
    # 并发配置分析
    optimal_concurrent = OCR_PROCESS_POOL_SIZE * 2
    if MAX_CONCURRENT_REQUESTS < OCR_PROCESS_POOL_SIZE:
        analysis["warnings"].append(f"⚠️  最大并发数({MAX_CONCURRENT_REQUESTS})小于OCR进程数({OCR_PROCESS_POOL_SIZE})")
        analysis["suggestions"].append(f"建议将最大并发数设置为{optimal_concurrent}")
        analysis["performance_score"] -= 5
    elif MAX_CONCURRENT_REQUESTS > optimal_concurrent:
        analysis["suggestions"].append(f"可以将最大并发数从{MAX_CONCURRENT_REQUESTS}调整为{optimal_concurrent}以获得更好的性能平衡")
    
    # 内存优化配置分析
    if not MEMORY_OPTIMIZATION and total_estimated_memory > 4:
        analysis["suggestions"].append("建议启用内存优化以降低内存占用")
        analysis["performance_score"] -= 5
    
    # 缓存配置分析
    if ENABLE_REQUEST_CACHE:
        cache_memory_usage = CACHE_MAX_SIZE * 0.003  # 每个缓存项约3KB
        analysis["memory_analysis"]["cache_memory_gb"] = cache_memory_usage
        total_estimated_memory += cache_memory_usage  # 更新总内存使用量
        analysis["memory_analysis"]["total_estimated_gb"] = total_estimated_memory
        
        # 重新计算内存使用率
        memory_ratio = total_estimated_memory / system_info.get("memory_total_gb", 8.0)
        analysis["memory_analysis"]["usage_ratio"] = memory_ratio
        
        if cache_memory_usage > 1.0:  # 缓存占用超过1GB
            analysis["warnings"].append(f"⚠️  缓存预估占用{cache_memory_usage:.1f}GB内存，建议减少缓存数量")
            analysis["suggestions"].append(f"建议将缓存数量从{CACHE_MAX_SIZE}调整为{int(CACHE_MAX_SIZE * 0.5)}")
            analysis["performance_score"] -= 5
        
        if memory_ratio > 0.7 and CACHE_MAX_SIZE > 500:
            analysis["suggestions"].append("内存使用率较高，建议减少缓存数量或禁用缓存")
    else:
        analysis["suggestions"].append("建议启用请求缓存以提高重复请求的响应速度")
    
    # 磁盘空间检查
    disk_free_gb = system_info.get("disk_free_gb", 100)
    if disk_free_gb < 5:
        analysis["status"] = "warning"
        analysis["warnings"].append(f"⚠️  磁盘剩余空间不足({disk_free_gb:.1f}GB)")
        analysis["suggestions"].append("清理磁盘空间，建议保留至少10GB可用空间")
        analysis["performance_score"] -= 10
    
    # 确定最终状态
    if analysis["issues"]:
        analysis["status"] = "critical"
    elif analysis["warnings"]:
        analysis["status"] = "warning"
    
    return analysis

def get_performance_recommendations() -> Dict[str, Any]:
    """
    根据当前配置和系统环境返回详细的性能优化建议
    
    Returns:
        Dict[str, Any]: 完整的性能分析和建议
    """
    system_info = get_system_info()
    config_analysis = analyze_configuration()
    
    recommendations = {
        "system_info": system_info,
        "config_analysis": config_analysis,
        "optimization_suggestions": {},
        "deployment_recommendations": {},
        "environment_variables": {},
        "immediate_actions": [],
    }
    
    # 生成具体的优化建议
    memory_total = system_info.get("memory_total_gb", 8.0)
    cpu_cores = system_info.get("cpu_cores", 4)
    
    # 根据内存大小给出建议
    if memory_total >= 16:
        # 高配置服务器
        recommendations["optimization_suggestions"]["high_memory"] = {
            "workers": min(cpu_cores, 8),
            "ocr_process_pool_size": min(cpu_cores, 6),
            "max_concurrent_requests": min(cpu_cores * 2, 12),
            "memory_optimization": False,
            "enable_request_cache": True,
            "cache_max_size": 5000,
            "cache_expire_time": 3600,
            "description": "高配置服务器，优先性能"
        }
        recommendations["deployment_recommendations"]["type"] = "高性能部署"
    elif memory_total >= 8:
        # 中等配置服务器
        recommendations["optimization_suggestions"]["medium_memory"] = {
            "workers": min(cpu_cores, 4),
            "ocr_process_pool_size": min(cpu_cores, 3),
            "max_concurrent_requests": min(cpu_cores * 2, 8),
            "memory_optimization": True,
            "enable_request_cache": True,
            "cache_max_size": 1000,
            "cache_expire_time": 1800,
            "description": "中等配置服务器，平衡性能和内存"
        }
        recommendations["deployment_recommendations"]["type"] = "标准部署"
    else:
        # 低配置服务器
        recommendations["optimization_suggestions"]["low_memory"] = {
            "workers": 1,
            "ocr_process_pool_size": 1,
            "max_concurrent_requests": 2,
            "memory_optimization": True,
            "enable_request_cache": False,
            "cache_max_size": 100,
            "cache_expire_time": 600,
            "description": "低配置服务器，优先节省内存"
        }
        recommendations["deployment_recommendations"]["type"] = "节能部署"
        recommendations["immediate_actions"].append("考虑升级服务器内存到8GB以上")
    
    # 生成环境变量建议
    optimal_config = recommendations["optimization_suggestions"].get(
        "high_memory" if memory_total >= 16 else "medium_memory" if memory_total >= 8 else "low_memory"
    )
    
    if optimal_config:
        recommendations["environment_variables"] = {
            "WORKERS": optimal_config["workers"],
            "OCR_PROCESS_POOL_SIZE": optimal_config["ocr_process_pool_size"],
            "MAX_CONCURRENT_REQUESTS": optimal_config["max_concurrent_requests"],
            "MEMORY_OPTIMIZATION": str(optimal_config["memory_optimization"]).lower(),
            "ENABLE_GC_AFTER_REQUEST": "true" if optimal_config["memory_optimization"] else "false",
            "ENABLE_REQUEST_CACHE": str(optimal_config["enable_request_cache"]).lower(),
            "CACHE_MAX_SIZE": optimal_config["cache_max_size"],
            "CACHE_EXPIRE_TIME": optimal_config["cache_expire_time"],
        }
    
    # 添加紧急行动建议
    if config_analysis["status"] == "critical":
        recommendations["immediate_actions"].extend([
            "立即重启服务以释放内存",
            "检查是否有其他高内存占用程序运行",
            "考虑使用swap空间作为临时缓解方案"
        ])
    
    # 添加长期优化建议
    recommendations["long_term_suggestions"] = [
        "定期监控内存使用情况",
        "配置监控告警系统",
        "定期清理日志文件",
        "考虑使用容器化部署以更好地控制资源使用",
    ]
    
    if memory_total < 8:
        recommendations["long_term_suggestions"].append("升级服务器内存到8GB以上")
    
    if cpu_cores < 4:
        recommendations["long_term_suggestions"].append("升级CPU到4核心以上")
    
    return recommendations

def print_config_summary():
    """打印详细的当前配置摘要"""
    system_info = get_system_info()
    recommendations = get_performance_recommendations()
    config_analysis = recommendations["config_analysis"]
    
    print("\n" + "=" * 80)
    print(f"📊 {PROJECT_NAME} v{VERSION} 详细配置摘要")
    print("=" * 80)
    
    # 系统信息
    print("\n🖥️  系统环境:")
    if "error" not in system_info:
        print(f"   ├─ 操作系统: {system_info['platform']} {system_info['platform_version']}")
        print(f"   ├─ Python版本: {system_info['python_version']}")
        print(f"   ├─ CPU核心数: {system_info['cpu_cores']} 物理核心 / {system_info['cpu_logical']} 逻辑核心")
        print(f"   ├─ 总内存: {system_info['memory_total_gb']:.1f}GB")
        print(f"   ├─ 可用内存: {system_info['memory_available_gb']:.1f}GB ({100-system_info['memory_percent']:.1f}%)")
        print(f"   └─ 磁盘空间: {system_info['disk_free_gb']:.1f}GB 可用 / {system_info['disk_total_gb']:.1f}GB 总计")
    else:
        print(f"   └─ ⚠️  {system_info['error']}")
    
    # 当前配置
    print(f"\n🔧 当前服务配置:")
    print(f"   ├─ 服务地址: {HOST}:{PORT}")
    print(f"   ├─ Worker进程数: {WORKERS}")
    print(f"   ├─ OCR进程池大小: {OCR_PROCESS_POOL_SIZE}")
    print(f"   ├─ 最大并发请求: {MAX_CONCURRENT_REQUESTS}")
    print(f"   ├─ OCR任务超时: {OCR_TASK_TIMEOUT}秒")
    print(f"   ├─ 调试模式: {'启用' if DEBUG else '禁用'}")
    print(f"   └─ 日志级别: {LOG_LEVEL}")
    
    # 内存分析
    memory_analysis = config_analysis["memory_analysis"]
    print(f"\n💾 内存使用分析:")
    print(f"   ├─ OCR进程内存: {memory_analysis['ocr_memory_gb']:.1f}GB")
    print(f"   ├─ Worker进程内存: {memory_analysis['worker_memory_gb']:.1f}GB")
    if "cache_memory_gb" in memory_analysis:
        print(f"   ├─ 缓存内存: {memory_analysis['cache_memory_gb']:.3f}GB")
    print(f"   ├─ 预估总使用: {memory_analysis['total_estimated_gb']:.1f}GB")
    print(f"   ├─ 系统总内存: {memory_analysis['system_total_gb']:.1f}GB")
    print(f"   ├─ 内存使用率: {memory_analysis['usage_ratio']*100:.1f}%")
    print(f"   └─ 建议最大使用: {memory_analysis['recommended_max_memory']:.1f}GB")
    
    # 优化配置
    print(f"\n⚡ 优化配置:")
    print(f"   ├─ 内存优化: {'启用' if MEMORY_OPTIMIZATION else '禁用'}")
    print(f"   ├─ 垃圾回收: {'启用' if ENABLE_GC_AFTER_REQUEST else '禁用'}")
    print(f"   ├─ 请求缓存: {'启用' if ENABLE_REQUEST_CACHE else '禁用'}")
    if ENABLE_REQUEST_CACHE:
        print(f"   ├─ 缓存数量: {CACHE_MAX_SIZE}个")
        print(f"   ├─ 缓存过期: {CACHE_EXPIRE_TIME}秒")
        print(f"   ├─ 缓存算法: {CACHE_KEY_METHOD}")
    print(f"   ├─ 角度分类器: {'启用' if ID_CARD_CONFIG.get('use_angle_cls', False) else '禁用'}")
    print(f"   └─ 日志轮转: {LOG_ROTATION}")
    
    # 安全配置
    print(f"\n🔒 安全配置:")
    if API_KEYS and any(key.strip() for key in API_KEYS):
        valid_keys = [key for key in API_KEYS if key.strip()]
        print(f"   ├─ API密钥验证: 启用 ({len(valid_keys)}个密钥)")
        print(f"   └─ 请求头: {API_KEY_HEADER}")
    else:
        print(f"   └─ API密钥验证: 禁用")
    
    # 配置状态评估
    print(f"\n📈 配置状态评估:")
    status_icon = {"optimal": "✅", "warning": "⚠️ ", "critical": "❌"}
    status_text = {"optimal": "优秀", "warning": "需要关注", "critical": "需要立即处理"}
    
    print(f"   ├─ 整体状态: {status_icon[config_analysis['status']]} {status_text[config_analysis['status']]}")
    print(f"   ├─ 性能评分: {config_analysis['performance_score']}/100")
    print(f"   └─ 部署类型: {recommendations['deployment_recommendations'].get('type', '未知')}")
    
    # 问题和警告
    if config_analysis["issues"]:
        print(f"\n❌ 严重问题:")
        for issue in config_analysis["issues"]:
            print(f"   └─ {issue}")
    
    if config_analysis["warnings"]:
        print(f"\n⚠️  警告信息:")
        for warning in config_analysis["warnings"]:
            print(f"   └─ {warning}")
    
    # 优化建议
    if config_analysis["suggestions"]:
        print(f"\n💡 优化建议:")
        for i, suggestion in enumerate(config_analysis["suggestions"], 1):
            print(f"   {i}. {suggestion}")
    
    # 推荐配置
    if "environment_variables" in recommendations:
        print(f"\n🎯 推荐配置 (环境变量):")
        for key, value in recommendations["environment_variables"].items():
            current_value = globals().get(key, "未知")
            status = "✅" if str(current_value).lower() == str(value).lower() else "📝"
            print(f"   ├─ {key}={value} {status}")
        
        print(f"\n   快速应用命令:")
        env_vars = " ".join([f"{k}={v}" for k, v in recommendations["environment_variables"].items()])
        print(f"   └─ {env_vars} python run.py")
    
    # 立即行动建议
    if recommendations.get("immediate_actions"):
        print(f"\n🚨 立即行动建议:")
        for i, action in enumerate(recommendations["immediate_actions"], 1):
            print(f"   {i}. {action}")
    
    # 长期建议
    if recommendations.get("long_term_suggestions"):
        print(f"\n🔮 长期优化建议:")
        for i, suggestion in enumerate(recommendations["long_term_suggestions"], 1):
            print(f"   {i}. {suggestion}")
    
    print("\n" + "=" * 80)
    print()

def get_deployment_guide() -> str:
    """
    获取部署指南
    
    Returns:
        str: 部署指南文本
    """
    recommendations = get_performance_recommendations()
    system_info = recommendations["system_info"]
    memory_total = system_info.get("memory_total_gb", 8.0)
    
    guide = f"""
🚀 部署配置指南

根据您的服务器配置({memory_total:.1f}GB内存)，推荐以下部署方案:

"""
    
    if memory_total >= 16:
        guide += """
🏆 高性能部署方案:
   export WORKERS=6
   export OCR_PROCESS_POOL_SIZE=4
   export MAX_CONCURRENT_REQUESTS=10
   export MEMORY_OPTIMIZATION=false
   export LOG_LEVEL=INFO
   python run.py

   特点: 高并发、高性能、适合生产环境
"""
    elif memory_total >= 8:
        guide += """
⚖️  标准部署方案:
   export WORKERS=3
   export OCR_PROCESS_POOL_SIZE=2
   export MAX_CONCURRENT_REQUESTS=6
   export MEMORY_OPTIMIZATION=true
   export LOG_LEVEL=WARNING
   python run.py

   特点: 性能与内存平衡、适合中等负载
"""
    else:
        guide += """
💾 节能部署方案:
   export WORKERS=1
   export OCR_PROCESS_POOL_SIZE=1
   export MAX_CONCURRENT_REQUESTS=2
   export MEMORY_OPTIMIZATION=true
   export ENABLE_GC_AFTER_REQUEST=true
   export LOG_LEVEL=ERROR
   python run.py

   特点: 低内存占用、适合资源受限环境
"""
    
    guide += """
📝 监控建议:
   - 使用 htop 或 top 监控内存使用
   - 使用 tail -f logs/sfzocr.log 查看日志
   - 定期检查 /health 接口状态
   - 配置内存告警阈值为80%
"""
    
    return guide

def generate_env_file():
    """生成.env配置文件"""
    safe_print("\n" + "=" * 60)
    safe_print("📄 生成.env配置文件")
    safe_print("=" * 60)
    
    recommendations = get_performance_recommendations()
    
    if "environment_variables" not in recommendations:
        safe_print("❌ 无法获取推荐配置")
        return
    
    env_content = f"""# {PROJECT_NAME} v{VERSION} 配置文件
# 自动生成

# 🚀 性能配置
"""
    
    for key, value in recommendations["environment_variables"].items():
        env_content += f"{key}={value}\n"
    
    env_content += f"""
# 🔒 安全配置 (生产环境请取消注释并设置强密钥)
# API_KEYS=your_secret_key_1,your_secret_key_2

# 📝 日志配置
# LOG_LEVEL=WARNING
# LOG_ROTATION=20 MB
# LOG_RETENTION=1 week

# 🌐 网络配置
# HOST=0.0.0.0
# PORT=8000

# 💾 路径配置
# OCR_MODEL_DIR=./models
# LOG_DIR=./logs
"""
    
    env_file = Path(".env")
    if env_file.exists():
        backup_file = Path(".env.backup")
        env_file.rename(backup_file)
        safe_print(f"✅ 已备份现有配置文件为: {backup_file}")
    
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(env_content)
    
    safe_print(f"✅ 已生成配置文件: {env_file}")
    safe_print(f"\n📋 配置内容:")
    safe_print(env_content)
    safe_print("=" * 60)

def show_system_info():
    """显示系统信息"""
    safe_print("\n" + "=" * 60)
    safe_print("🖥️  系统环境信息")
    safe_print("=" * 60)
    
    system_info = get_system_info()
    
    if "error" not in system_info:
        safe_print(f"操作系统: {system_info['platform']} {system_info['platform_version']}")
        safe_print(f"Python版本: {system_info['python_version']}")
        safe_print(f"CPU核心数: {system_info['cpu_cores']} 物理核心 / {system_info['cpu_logical']} 逻辑核心")
        safe_print(f"总内存: {system_info['memory_total_gb']:.1f}GB")
        safe_print(f"可用内存: {system_info['memory_available_gb']:.1f}GB ({100-system_info['memory_percent']:.1f}%)")
        safe_print(f"磁盘空间: {system_info['disk_free_gb']:.1f}GB 可用 / {system_info['disk_total_gb']:.1f}GB 总计")
    else:
        safe_print(f"⚠️  {system_info['error']}")
    
    safe_print("=" * 60)

def show_performance_analysis():
    """显示详细性能分析"""
    safe_print("\n" + "=" * 60)
    safe_print("📊 性能分析报告")
    safe_print("=" * 60)
    
    recommendations = get_performance_recommendations()
    config_analysis = recommendations["config_analysis"]
    
    # 配置状态
    status_icon = {"optimal": "✅", "warning": "⚠️ ", "critical": "❌"}
    status_text = {"optimal": "优秀", "warning": "需要关注", "critical": "需要立即处理"}
    
    safe_print(f"\n整体状态: {status_icon[config_analysis['status']]} {status_text[config_analysis['status']]}")
    safe_print(f"性能评分: {config_analysis['performance_score']}/100")
    safe_print(f"部署类型: {recommendations['deployment_recommendations'].get('type', '未知')}")
    
    # 内存分析
    memory_analysis = config_analysis["memory_analysis"]
    safe_print(f"\n💾 内存使用分析:")
    safe_print(f"   预估总使用: {memory_analysis['total_estimated_gb']:.1f}GB")
    safe_print(f"   系统总内存: {memory_analysis['system_total_gb']:.1f}GB")
    safe_print(f"   内存使用率: {memory_analysis['usage_ratio']*100:.1f}%")
    
    # 问题和警告
    if config_analysis["issues"]:
        safe_print(f"\n❌ 严重问题:")
        for issue in config_analysis["issues"]:
            safe_print(f"   • {issue}")
    
    if config_analysis["warnings"]:
        safe_print(f"\n⚠️  警告信息:")
        for warning in config_analysis["warnings"]:
            safe_print(f"   • {warning}")
    
    # 优化建议
    if config_analysis["suggestions"]:
        safe_print(f"\n💡 优化建议:")
        for i, suggestion in enumerate(config_analysis["suggestions"], 1):
            safe_print(f"   {i}. {suggestion}")
    
    # 推荐配置
    if "environment_variables" in recommendations:
        safe_print(f"\n🎯 推荐环境变量配置:")
        for key, value in recommendations["environment_variables"].items():
            safe_print(f"   export {key}={value}")
        
        env_vars = " ".join([f"{k}={v}" for k, v in recommendations["environment_variables"].items()])
        safe_print(f"\n📋 快速应用命令:")
        safe_print(f"   {env_vars} python run.py")
    
    # 立即行动建议
    if recommendations.get("immediate_actions"):
        safe_print(f"\n🚨 立即行动建议:")
        for i, action in enumerate(recommendations["immediate_actions"], 1):
            safe_print(f"   {i}. {action}")
    
    safe_print("=" * 60)

def show_deployment_guide():
    """显示部署指南"""
    safe_print("\n" + "=" * 60)
    safe_print("🚀 部署配置指南")
    safe_print("=" * 60)
    
    guide = get_deployment_guide()
    safe_print(guide)
    
    safe_print("=" * 60)

def validate_configuration():
    """验证当前配置"""
    safe_print("\n" + "=" * 60)
    safe_print("🔍 配置验证")
    safe_print("=" * 60)
    
    analysis = analyze_configuration()
    
    safe_print(f"配置状态: {analysis['status'].upper()}")
    safe_print(f"性能评分: {analysis['performance_score']}/100")
    
    if analysis["status"] == "optimal":
        safe_print("✅ 配置验证通过，当前配置合理")
    elif analysis["status"] == "warning":
        safe_print("⚠️  配置存在潜在问题，建议优化")
    else:
        safe_print("❌ 配置存在严重问题，需要立即处理")
    
    if analysis["issues"]:
        safe_print(f"\n严重问题 ({len(analysis['issues'])}个):")
        for issue in analysis["issues"]:
            safe_print(f"   • {issue}")
    
    if analysis["warnings"]:
        safe_print(f"\n警告信息 ({len(analysis['warnings'])}个):")
        for warning in analysis["warnings"]:
            safe_print(f"   • {warning}")
    
    if analysis["suggestions"]:
        safe_print(f"\n优化建议 ({len(analysis['suggestions'])}个):")
        for suggestion in analysis["suggestions"]:
            safe_print(f"   • {suggestion}")
    
    safe_print("=" * 60)

def main():
    """配置管理命令行工具主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description=f"{PROJECT_NAME} v{VERSION} 配置管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python -m app.config --summary          # 显示完整配置摘要
  python -m app.config --system-info      # 显示系统信息
  python -m app.config --performance      # 显示性能分析
  python -m app.config --deployment       # 显示部署指南
  python -m app.config --validate         # 验证配置
  python -m app.config --generate-env     # 生成.env文件
  python -m app.config --all              # 显示所有信息
        """
    )
    
    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="显示完整配置摘要"
    )
    
    parser.add_argument(
        "--system-info", "-i",
        action="store_true",
        help="显示系统信息"
    )
    
    parser.add_argument(
        "--performance", "-p",
        action="store_true",
        help="显示性能分析报告"
    )
    
    parser.add_argument(
        "--deployment", "-d",
        action="store_true",
        help="显示部署配置指南"
    )
    
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="验证当前配置"
    )
    
    parser.add_argument(
        "--generate-env", "-g",
        action="store_true",
        help="生成.env配置文件"
    )
    
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="显示所有信息"
    )
    
    args = parser.parse_args()
    
    # 如果没有指定任何参数，显示配置摘要
    if not any(vars(args).values()):
        print_config_summary()
        print(get_deployment_guide())
        return
    
    safe_print(f"\n🔧 {PROJECT_NAME} v{VERSION} 配置管理工具")
    
    try:
        if args.all or args.summary:
            print_config_summary()
        
        if args.all or args.system_info:
            show_system_info()
        
        if args.all or args.performance:
            show_performance_analysis()
        
        if args.all or args.deployment:
            show_deployment_guide()
        
        if args.all or args.validate:
            validate_configuration()
        
        if args.generate_env:
            generate_env_file()
            
    except KeyboardInterrupt:
        safe_print("\n\n⏸️  操作已取消")
    except Exception as e:
        safe_print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

# 如果直接运行此文件，执行命令行工具
if __name__ == "__main__":
    main()
