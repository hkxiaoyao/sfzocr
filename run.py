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

from app.config import HOST, PORT, WORKERS, DEBUG

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
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 内存优化：强制使用单worker以减少内存占用
    effective_workers = 1  # 强制单worker模式以优化内存使用
    
    print(f"内存优化模式启动:")
    print(f"  - Worker进程数: {effective_workers} (内存优化)")
    print(f"  - 监听地址: {args.host}:{args.port}")
    print(f"  - 调试模式: {args.debug}")
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        workers=effective_workers,  # 使用内存优化的worker数量
        reload=args.debug,  # 调试模式下启用自动重载
        log_level="debug" if args.debug else "warning",  # 降低日志级别以节省内存
    )

if __name__ == "__main__":
    main() 