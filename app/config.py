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
from pathlib import Path
from typing import Dict, Any, Optional, List

# ============================================================================
# 🔧 环境变量加载
# ============================================================================

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    
    # 项目根目录
    BASE_DIR = Path(__file__).resolve().parent.parent
    
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
            print(f"✅ 已加载环境配置文件: {env_file}")
            env_loaded = True
            break
    
    if not env_loaded:
        print("💡 未找到 .env 配置文件，使用默认配置和系统环境变量")
        
except ImportError:
    print("⚠️  python-dotenv 未安装，请运行: pip install python-dotenv")
    print("   将使用系统环境变量和默认配置")
    BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# 基础配置（一般不需要修改）
# ============================================================================

# API版本前缀
API_V1_PREFIX = "/api/v1"

# 项目名称和版本
PROJECT_NAME = "身份证OCR识别服务"
VERSION = "0.1.3"

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
# �� 高性能：10-20  💾 内存受限：2-5  🔧 生产环境：5-10
# 计算公式：OCR_PROCESS_POOL_SIZE * 2 = 推荐并发数
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "3"))

# 请求处理完成后是否强制垃圾回收
# 📌 性能影响：会稍微增加响应时间，但能有效降低内存占用
# 🚀 高性能：False  💾 内存受限：True  🔧 生产环境：True
ENABLE_GC_AFTER_REQUEST = os.getenv("ENABLE_GC_AFTER_REQUEST", "True").lower() in ("true", "1", "t")

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
# 📁 目录初始化
# ============================================================================

# 创建必要的目录
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OCR_MODEL_DIR, exist_ok=True)

# ============================================================================
# 🔧 服务器配置建议
# ============================================================================

def get_performance_recommendations() -> Dict[str, str]:
    """
    根据当前配置返回性能优化建议
    
    Returns:
        Dict[str, str]: 配置建议字典
    """
    recommendations = {}
    
    # 检查工作进程数配置
    if WORKERS == 1:
        recommendations["WORKERS"] = "单进程模式，适合内存受限环境。高性能服务器建议设置为CPU核心数。"
    elif WORKERS > 4:
        recommendations["WORKERS"] = f"当前{WORKERS}个进程，确保有足够内存（约{WORKERS * 1.5:.1f}GB）。"
    
    # 检查OCR进程池配置
    memory_usage = OCR_PROCESS_POOL_SIZE * 1.2  # 每个进程约1.2GB
    if memory_usage > 8:
        recommendations["OCR_PROCESS_POOL_SIZE"] = f"当前配置需要约{memory_usage:.1f}GB内存，请确保服务器有足够内存。"
    
    # 检查并发配置
    if MAX_CONCURRENT_REQUESTS < OCR_PROCESS_POOL_SIZE:
        recommendations["MAX_CONCURRENT_REQUESTS"] = "并发请求数小于OCR进程数，可能影响处理效率。"
    
    # 检查内存优化配置
    if not MEMORY_OPTIMIZATION and memory_usage > 4:
        recommendations["MEMORY_OPTIMIZATION"] = "内存使用较高，建议启用内存优化。"
    
    return recommendations

# ============================================================================
# 📊 配置摘要信息
# ============================================================================

def print_config_summary():
    """打印当前配置摘要"""
    print(f"""
    
🚀 {PROJECT_NAME} v{VERSION} 配置摘要
    
📊 性能配置：
   - 工作进程数: {WORKERS}
   - OCR进程池: {OCR_PROCESS_POOL_SIZE}
   - 最大并发: {MAX_CONCURRENT_REQUESTS}
   - 预估内存: {OCR_PROCESS_POOL_SIZE * 1.2:.1f}GB
   
🔧 优化配置：
   - 内存优化: {'启用' if MEMORY_OPTIMIZATION else '禁用'}
   - 垃圾回收: {'启用' if ENABLE_GC_AFTER_REQUEST else '禁用'}
   - 日志级别: {LOG_LEVEL}
   
🔒 安全配置：
   - API密钥: {'已配置' if API_KEYS else '未配置'}
   - 调试模式: {'启用' if DEBUG else '禁用'}
   
💡 优化建议：
""")
    
    recommendations = get_performance_recommendations()
    if recommendations:
        for key, suggestion in recommendations.items():
            print(f"   - {key}: {suggestion}")
    else:
        print("   - 当前配置合理，无特殊建议。")
    
    print("\n" + "="*60)

# 如果直接运行此文件，显示配置摘要
if __name__ == "__main__":
    print_config_summary()
