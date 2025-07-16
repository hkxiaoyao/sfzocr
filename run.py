#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# 确保在当前目录下运行时也能正确导入模块
if os.getcwd() != str(ROOT_DIR):
    print(f"注意: 当前工作目录为 {os.getcwd()}, 建议在 {ROOT_DIR} 目录下运行")

from app.config import (
    HOST, PORT, WORKERS, DEBUG, LOG_LEVEL, VERSION, PROJECT_NAME,
    OCR_TASK_TIMEOUT, MAX_CONCURRENT_REQUESTS, OCR_PROCESS_POOL_SIZE,
    MEMORY_OPTIMIZATION, ENABLE_GC_AFTER_REQUEST, OCR_MODEL_DIR,
    LOG_DIR, LOG_FILENAME, LOG_ROTATION, LOG_RETENTION,
    API_KEY_HEADER, API_KEYS, ALLOWED_HOSTS, CORS_ORIGINS,
    ID_CARD_CONFIG
)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="身份证OCR识别服务启动脚本")
    
    parser.add_argument(
        "--host", 
        type=str, 
        default=HOST,
        help=f"服务监听地址，默认: {HOST}"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=PORT,
        help=f"服务监听端口，默认: {PORT}"
    )
    
    parser.add_argument(
        "--workers", 
        type=int, 
        default=WORKERS,
        help=f"工作进程数，默认: {WORKERS}"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        default=DEBUG,
        help="是否启用调试模式"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default=LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"日志级别，默认: {LOG_LEVEL}"
    )
    
    return parser.parse_args()

def display_startup_info(args):
    """显示启动配置信息"""
    # 确定实际使用的配置
    effective_workers = args.workers
    effective_log_level = args.log_level.lower() if not args.debug else "debug"
    
    print("=" * 80)
    print(f"🚀 {PROJECT_NAME} v{VERSION} 启动中...")
    print("=" * 80)
    
    # 服务基本配置
    print("📡 服务配置:")
    print(f"  └─ 服务地址: http://{args.host}:{args.port}")
    print(f"  └─ Worker进程数: {effective_workers}")
    print(f"  └─ 调试模式: {'启用' if args.debug else '禁用'}")
    print(f"  └─ 日志级别: {effective_log_level.upper()}")
    print()
    
    # 性能配置
    print("⚡ 性能配置:")
    print(f"  └─ 最大并发请求: {MAX_CONCURRENT_REQUESTS}")
    print(f"  └─ OCR进程池大小: {OCR_PROCESS_POOL_SIZE}")
    print(f"  └─ OCR任务超时: {OCR_TASK_TIMEOUT}秒")
    print(f"  └─ 内存优化: {'启用' if MEMORY_OPTIMIZATION else '禁用'}")
    print(f"  └─ 请求后垃圾回收: {'启用' if ENABLE_GC_AFTER_REQUEST else '禁用'}")
    print()
    
    # OCR引擎配置
    print("🔍 OCR引擎配置:")
    print(f"  └─ 模型目录: {OCR_MODEL_DIR}")
    print(f"  └─ 使用角度分类器: {'启用' if ID_CARD_CONFIG.get('use_angle_cls', False) else '禁用'}")
    print(f"  └─ 文本检测: {'启用' if ID_CARD_CONFIG.get('det', True) else '禁用'}")
    print(f"  └─ 文本识别: {'启用' if ID_CARD_CONFIG.get('rec', True) else '禁用'}")
    print(f"  └─ 方向分类: {'启用' if ID_CARD_CONFIG.get('cls', True) else '禁用'}")
    
    # 检查模型目录
    if os.path.exists(OCR_MODEL_DIR):
        print(f"  └─ 模型路径状态: {OCR_MODEL_DIR} ✅")
    else:
        print(f"  └─ 模型路径状态: {OCR_MODEL_DIR} ❌ (将使用默认模型)")
    print()
    
    # 日志配置
    print("📝 日志配置:")
    print(f"  └─ 日志目录: {LOG_DIR}")
    print(f"  └─ 日志文件: {LOG_FILENAME}")
    print(f"  └─ 文件轮转: {LOG_ROTATION}")
    print(f"  └─ 保留时间: {LOG_RETENTION}")
    print()
    
    # 安全配置
    print("🔐 安全配置:")
    if API_KEYS and any(key.strip() for key in API_KEYS):
        valid_keys = [key for key in API_KEYS if key.strip()]
        api_key_display = f"{valid_keys[0][:8]}..." if len(valid_keys[0]) > 8 else valid_keys[0]
        print(f"  └─ API密钥验证: 启用 ({len(valid_keys)}个密钥)")
        print(f"  └─ 示例密钥: {api_key_display}")
        print(f"  └─ 密钥请求头: {API_KEY_HEADER}")
    else:
        print(f"  └─ API密钥验证: 禁用")
    
    print(f"  └─ 允许的主机: {', '.join(ALLOWED_HOSTS[:3])}")
    if len(ALLOWED_HOSTS) > 3:
        print(f"  └─              ...等{len(ALLOWED_HOSTS)}个")
    print()
    
    # 性能评估和建议
    print("💡 性能评估:")
    estimated_memory = OCR_PROCESS_POOL_SIZE * 1.2  # 每个OCR进程约1.2GB
    total_memory = estimated_memory + (effective_workers * 0.5)  # 加上uvicorn进程内存
    
    if effective_workers == 1:
        print(f"  └─ 部署模式: 开发/测试模式")
        print(f"  └─ 预估内存需求: ~{total_memory:.1f}GB")
        print(f"  └─ 并发能力: 低 (适合内存受限环境)")
        print(f"  └─ 优化建议: 生产环境建议增加进程数")
        print(f"      export WORKERS=4  或  python run.py --workers 4")
    elif effective_workers <= 4:
        print(f"  └─ 部署模式: 生产标准模式")
        print(f"  └─ 预估内存需求: ~{total_memory:.1f}GB")
        print(f"  └─ 并发能力: 中等 (推荐)")
    elif effective_workers <= 8:
        print(f"  └─ 部署模式: 高性能模式")
        print(f"  └─ 预估内存需求: ~{total_memory:.1f}GB")
        print(f"  └─ 并发能力: 高")
    else:
        print(f"  └─ 部署模式: 超高性能模式")
        print(f"  └─ 预估内存需求: ~{total_memory:.1f}GB")
        print(f"  └─ 并发能力: 超高")
        print(f"  └─ ⚠️  警告: 请确保服务器有足够内存支持")
    
    # 内存优化提示
    if not MEMORY_OPTIMIZATION and total_memory > 4:
        print(f"  └─ 💾 建议: 启用内存优化 (export MEMORY_OPTIMIZATION=True)")
    
    print()
    print("🌐 API接口文档:")
    print(f"  └─ Swagger UI: http://{args.host}:{args.port}/docs")
    print(f"  └─ ReDoc: http://{args.host}:{args.port}/redoc")
    print(f"  └─ 健康检查: http://{args.host}:{args.port}/health")
    print()
    
    print("=" * 80)
    print("🎯 服务启动完成，等待请求...")
    print("=" * 80)
    print()

def main():
    """主函数"""
    args = parse_args()
    
    # 显示启动配置信息
    display_startup_info(args)
    
    # 确定实际使用的配置
    effective_workers = args.workers
    effective_log_level = args.log_level.lower() if not args.debug else "debug"
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        workers=effective_workers,
        reload=args.debug,  # 调试模式下启用自动重载
        log_level=effective_log_level,
    )

if __name__ == "__main__":
    main() 