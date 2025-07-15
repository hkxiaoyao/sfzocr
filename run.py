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
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        workers=args.workers if not args.debug else 1,  # 调试模式下只使用一个工作进程
        reload=args.debug,  # 调试模式下启用自动重载
        log_level="debug" if args.debug else "info",
    )

if __name__ == "__main__":
    main() 