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

from app.config import HOST, PORT, WORKERS, DEBUG, LOG_LEVEL

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

def main():
    """主函数"""
    args = parse_args()
    
    # 确定实际使用的配置
    effective_workers = args.workers
    effective_log_level = args.log_level.lower() if not args.debug else "debug"
    
    print(f"🚀 身份证OCR识别服务启动:")
    print(f"  - Worker进程数: {effective_workers}")
    print(f"  - 监听地址: {args.host}:{args.port}")
    print(f"  - 调试模式: {args.debug}")
    print(f"  - 日志级别: {effective_log_level.upper()}")
    
    # 性能提示
    if effective_workers == 1:
        print(f"  💡 提示: 当前为单进程模式，适合内存受限环境")
        print(f"      如需提高并发能力，可通过环境变量或参数调整：")
        print(f"      export WORKERS=4  或  python run.py --workers 4")
    elif effective_workers > 4:
        print(f"  ⚠️  警告: 当前配置 {effective_workers} 个进程，预估内存需求约 {effective_workers * 1.5:.1f}GB")
    
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