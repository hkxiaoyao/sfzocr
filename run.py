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
    ID_CARD_CONFIG, OCR_PERFORMANCE_CONFIG, FOREIGN_ID_CARD_CONFIG,
    ENABLE_REQUEST_CACHE, CACHE_MAX_SIZE, CACHE_EXPIRE_TIME, 
    CACHE_KEY_METHOD, CACHE_DEBUG_RESULTS, CACHE_ENABLE_STATS,
    safe_print
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
        help=f"日志级别，可选值: DEBUG/INFO/WARNING/ERROR/CRITICAL，默认: {LOG_LEVEL}"
    )
    
    return parser.parse_args()

def display_startup_info(args):
    """显示启动配置信息"""
    # 确定实际使用的配置
    effective_workers = args.workers
    effective_log_level = args.log_level.lower() if not args.debug else "debug"
    
    safe_print("=" * 80)
    safe_print(f"🚀 {PROJECT_NAME} v{VERSION} 启动中...")
    safe_print("=" * 80)
    
    # 服务基本配置
    safe_print("📡 服务配置:")
    safe_print(f"  └─ 服务地址: http://{args.host}:{args.port}")
    safe_print(f"  └─ Worker进程数: {effective_workers}")
    safe_print(f"  └─ 调试模式: {'启用' if args.debug else '禁用'}")
    safe_print(f"  └─ 日志级别: {effective_log_level.upper()}")
    safe_print("")
    
    # 性能配置
    safe_print("⚡ 性能配置:")
    safe_print(f"  └─ 最大并发请求: {MAX_CONCURRENT_REQUESTS}")
    safe_print(f"  └─ OCR进程池大小: {OCR_PROCESS_POOL_SIZE}")
    safe_print(f"  └─ OCR任务超时: {OCR_TASK_TIMEOUT}秒")
    safe_print(f"  └─ 内存优化: {'启用' if MEMORY_OPTIMIZATION else '禁用'}")
    safe_print(f"  └─ 请求后垃圾回收: {'启用' if ENABLE_GC_AFTER_REQUEST else '禁用'}")
    safe_print("")
    
    # 缓存配置
    safe_print("🗄️ 缓存配置:")
    safe_print(f"  └─ 请求缓存: {'启用' if ENABLE_REQUEST_CACHE else '禁用'}")
    if ENABLE_REQUEST_CACHE:
        safe_print(f"  └─ 缓存容量: {CACHE_MAX_SIZE}个")
        safe_print(f"  └─ 过期时间: {CACHE_EXPIRE_TIME}秒 ({CACHE_EXPIRE_TIME//60}分钟)")
        safe_print(f"  └─ 键算法: {CACHE_KEY_METHOD.upper()}")
        safe_print(f"  └─ 缓存调试结果: {'启用' if CACHE_DEBUG_RESULTS else '禁用'}")
        safe_print(f"  └─ 缓存统计: {'启用' if CACHE_ENABLE_STATS else '禁用'}")
        # 计算缓存预估内存占用
        cache_memory_mb = CACHE_MAX_SIZE * 3  # 每项约3KB
        if cache_memory_mb >= 1024:
            safe_print(f"  └─ 预估内存占用: ~{cache_memory_mb/1024:.1f}GB")
        else:
            safe_print(f"  └─ 预估内存占用: ~{cache_memory_mb}MB")
    else:
        safe_print(f"  └─ 注意: 禁用缓存可能影响重复请求的响应速度")
    safe_print("")
    
    # OCR引擎配置
    safe_print("🔍 OCR引擎配置:")
    safe_print(f"  └─ 模型目录: {OCR_MODEL_DIR}")
    safe_print(f"  └─ 使用角度分类器: {'启用' if ID_CARD_CONFIG.get('use_angle_cls', False) else '禁用'}")
    safe_print(f"  └─ 文本检测: {'启用' if ID_CARD_CONFIG.get('det', True) else '禁用'}")
    safe_print(f"  └─ 文本识别: {'启用' if ID_CARD_CONFIG.get('rec', True) else '禁用'}")
    safe_print(f"  └─ 方向分类: {'启用' if ID_CARD_CONFIG.get('cls', True) else '禁用'}")
    
    # OCR性能优化配置
    safe_print(f"  └─ 性能优化:")
    safe_print(f"      ├─ 快速模式: {'启用' if OCR_PERFORMANCE_CONFIG.get('enable_fast_mode', False) else '禁用'}")
    safe_print(f"      ├─ 内存优化: {'启用' if OCR_PERFORMANCE_CONFIG.get('enable_memory_optimization', True) else '禁用'}")
    safe_print(f"      ├─ CPU线程数: {OCR_PERFORMANCE_CONFIG.get('cpu_threads', 4)}")
    safe_print(f"      ├─ 检测阈值: {OCR_PERFORMANCE_CONFIG.get('det_db_thresh', 0.3)}")
    safe_print(f"      ├─ 识别批次: {OCR_PERFORMANCE_CONFIG.get('rec_batch_num', 6)}")
    safe_print(f"      ├─ 最大文本长度: {OCR_PERFORMANCE_CONFIG.get('max_text_length', 25)}")
    safe_print(f"      └─ 图像大小限制: {OCR_PERFORMANCE_CONFIG.get('max_image_size', 4096)}px")
    
    # 支持的证件类型
    safe_print(f"  └─ 支持证件类型:")
    safe_print(f"      ├─ 中国居民身份证（正面/背面）")
    safe_print(f"      ├─ 新版外国人永久居留身份证")
    safe_print(f"      └─ 旧版外国人永久居留身份证")
    
    # 检查模型目录
    if os.path.exists(OCR_MODEL_DIR):
        safe_print(f"  └─ 模型路径状态: {OCR_MODEL_DIR} ✅")
    else:
        safe_print(f"  └─ 模型路径状态: {OCR_MODEL_DIR} ❌ (将使用默认模型)")
    safe_print("")
    
    # 日志配置
    safe_print("📝 日志配置:")
    safe_print(f"  └─ 日志目录: {LOG_DIR}")
    safe_print(f"  └─ 日志文件: {LOG_FILENAME}")
    safe_print(f"  └─ 文件轮转: {LOG_ROTATION}")
    safe_print(f"  └─ 保留时间: {LOG_RETENTION}")
    safe_print("")
    
    # 安全配置
    safe_print("🔐 安全配置:")
    if API_KEYS and any(key.strip() for key in API_KEYS):
        valid_keys = [key for key in API_KEYS if key.strip()]
        api_key_display = f"{valid_keys[0][:8]}..." if len(valid_keys[0]) > 8 else valid_keys[0]
        safe_print(f"  └─ API密钥验证: 启用 ({len(valid_keys)}个密钥)")
        safe_print(f"  └─ 示例密钥: {api_key_display}")
        safe_print(f"  └─ 密钥请求头: {API_KEY_HEADER}")
    else:
        safe_print(f"  └─ API密钥验证: 禁用")
        safe_print(f"  └─ ⚠️  建议: 生产环境应启用API密钥验证")
    
    safe_print(f"  └─ 允许的主机: {', '.join(ALLOWED_HOSTS[:3])}")
    if len(ALLOWED_HOSTS) > 3:
        safe_print(f"  └─              ...等{len(ALLOWED_HOSTS)}个")
    
    # CORS配置
    safe_print(f"  └─ CORS跨域:")
    if CORS_ORIGINS == ["*"]:
        safe_print(f"      ├─ 允许所有来源 (*)")
        safe_print(f"      └─ ⚠️  建议: 生产环境应限制具体域名")
    elif len(CORS_ORIGINS) == 0:
        safe_print(f"      └─ 禁用跨域访问")
    else:
        safe_print(f"      ├─ 允许域名: {len(CORS_ORIGINS)}个")
        for i, origin in enumerate(CORS_ORIGINS[:3]):
            prefix = "├─" if i < min(2, len(CORS_ORIGINS)-1) else "└─"
            safe_print(f"      {prefix} {origin}")
        if len(CORS_ORIGINS) > 3:
            safe_print(f"      └─ ...等{len(CORS_ORIGINS)}个域名")
    safe_print("")
    
    # 性能评估和建议
    safe_print("💡 性能评估:")
    estimated_memory = OCR_PROCESS_POOL_SIZE * 1.2  # 每个OCR进程约1.2GB
    total_memory = estimated_memory + (effective_workers * 0.5)  # 加上uvicorn进程内存
    
    if effective_workers == 1:
        safe_print(f"  └─ 部署模式: 开发/测试模式")
        safe_print(f"  └─ 预估内存需求: ~{total_memory:.1f}GB")
        safe_print(f"  └─ 并发能力: 低 (适合内存受限环境)")
        safe_print(f"  └─ 优化建议: 生产环境建议增加进程数")
        safe_print(f"      export WORKERS=4  或  python run.py --workers 4")
    elif effective_workers <= 4:
        safe_print(f"  └─ 部署模式: 生产标准模式")
        safe_print(f"  └─ 预估内存需求: ~{total_memory:.1f}GB")
        safe_print(f"  └─ 并发能力: 中等 (推荐)")
    elif effective_workers <= 8:
        safe_print(f"  └─ 部署模式: 高性能模式")
        safe_print(f"  └─ 预估内存需求: ~{total_memory:.1f}GB")
        safe_print(f"  └─ 并发能力: 高")
    else:
        safe_print(f"  └─ 部署模式: 超高性能模式")
        safe_print(f"  └─ 预估内存需求: ~{total_memory:.1f}GB")
        safe_print(f"  └─ 并发能力: 超高")
        safe_print(f"  └─ ⚠️  警告: 请确保服务器有足够内存支持")
    
    # 内存优化提示
    if not MEMORY_OPTIMIZATION and total_memory > 4:
        safe_print(f"  └─ 💾 建议: 启用内存优化 (export MEMORY_OPTIMIZATION=True)")
    
    safe_print("")
    safe_print("🌐 API接口文档:")
    safe_print(f"  └─ Swagger UI: http://{args.host}:{args.port}/docs")
    safe_print(f"  └─ ReDoc: http://{args.host}:{args.port}/redoc")
    safe_print(f"  └─ 健康检查: http://{args.host}:{args.port}/api/v1/health")
    safe_print("")
    
    safe_print("=" * 80)
    safe_print("🎯 服务启动完成，等待请求...")
    safe_print("=" * 80)
    safe_print("")

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