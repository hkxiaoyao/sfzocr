#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
内存监控工具
用于监控OCR服务的内存使用情况
"""

import time
import psutil
import argparse
from typing import Dict, List

def get_process_memory_info(process_name: str = "python") -> List[Dict]:
    """
    获取指定进程的内存信息
    
    Args:
        process_name: 进程名称
        
    Returns:
        进程内存信息列表
    """
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                # 检查是否是OCR相关进程
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'uvicorn' in cmdline or 'sfzocr' in cmdline or 'main:app' in cmdline:
                    memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_mb': memory_mb,
                        'cmdline': cmdline
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return processes

def monitor_memory(interval: int = 5, threshold_mb: float = 1024):
    """
    持续监控内存使用
    
    Args:
        interval: 监控间隔（秒）
        threshold_mb: 内存警告阈值（MB）
    """
    print(f"开始监控OCR服务内存使用情况...")
    print(f"监控间隔: {interval}秒")
    print(f"警告阈值: {threshold_mb}MB")
    print("-" * 80)
    
    try:
        while True:
            # 获取系统整体内存信息
            system_memory = psutil.virtual_memory()
            system_used_mb = (system_memory.total - system_memory.available) / 1024 / 1024
            system_total_mb = system_memory.total / 1024 / 1024
            system_percent = system_memory.percent
            
            # 获取OCR进程信息
            ocr_processes = get_process_memory_info()
            
            # 计算OCR进程总内存使用
            total_ocr_memory = sum(proc['memory_mb'] for proc in ocr_processes)
            
            # 显示监控信息
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] 内存监控报告:")
            print(f"系统内存: {system_used_mb:.1f}MB / {system_total_mb:.1f}MB ({system_percent:.1f}%)")
            print(f"OCR进程总内存: {total_ocr_memory:.1f}MB")
            
            if ocr_processes:
                print("OCR进程详情:")
                for proc in ocr_processes:
                    status = "⚠️ 警告" if proc['memory_mb'] > threshold_mb else "✅ 正常"
                    print(f"  PID {proc['pid']}: {proc['memory_mb']:.1f}MB {status}")
            else:
                print("未找到运行中的OCR进程")
            
            # 检查警告条件
            if total_ocr_memory > threshold_mb:
                print(f"🔥 警告: OCR进程内存使用过高! {total_ocr_memory:.1f}MB > {threshold_mb}MB")
            
            if system_percent > 90:
                print(f"🔥 警告: 系统内存使用率过高! {system_percent:.1f}%")
            
            print("-" * 80)
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n监控已停止")

def check_memory_once():
    """
    一次性检查内存使用情况
    """
    print("OCR服务内存使用情况检查:")
    print("=" * 50)
    
    # 系统内存
    system_memory = psutil.virtual_memory()
    system_used_mb = (system_memory.total - system_memory.available) / 1024 / 1024
    system_total_mb = system_memory.total / 1024 / 1024
    
    print(f"系统内存: {system_used_mb:.1f}MB / {system_total_mb:.1f}MB ({system_memory.percent:.1f}%)")
    
    # OCR进程
    ocr_processes = get_process_memory_info()
    if ocr_processes:
        print(f"\n发现 {len(ocr_processes)} 个OCR相关进程:")
        total_memory = 0
        for proc in ocr_processes:
            print(f"  PID {proc['pid']}: {proc['memory_mb']:.1f}MB")
            total_memory += proc['memory_mb']
        print(f"\nOCR进程总内存使用: {total_memory:.1f}MB")
        
        # 评估
        if total_memory > 2048:
            print("❌ 内存使用过高，建议立即优化")
        elif total_memory > 1024:
            print("⚠️ 内存使用较高，需要关注")
        else:
            print("✅ 内存使用正常")
    else:
        print("未找到运行中的OCR进程")

def main():
    parser = argparse.ArgumentParser(description="OCR服务内存监控工具")
    parser.add_argument("--monitor", "-m", action="store_true", help="持续监控模式")
    parser.add_argument("--interval", "-i", type=int, default=5, help="监控间隔（秒），默认5秒")
    parser.add_argument("--threshold", "-t", type=float, default=1024, help="内存警告阈值（MB），默认1024MB")
    
    args = parser.parse_args()
    
    if args.monitor:
        monitor_memory(args.interval, args.threshold)
    else:
        check_memory_once()

if __name__ == "__main__":
    main() 