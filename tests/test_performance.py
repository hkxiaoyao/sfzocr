#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能优化测试脚本 - v0.1.4
"""

import time
import requests
import base64
import json
from typing import Dict, Any

def test_api_performance():
    """测试API性能优化功能"""
    
    # 创建一个测试图片的base64数据（模拟）
    test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    api_url = "http://localhost:8000/api/v1/ocr/idcard"
    
    print("🚀 OCR性能优化测试 - v0.1.4")
    print("=" * 50)
    
    # 测试1：普通模式
    print("\n1. 测试普通模式...")
    normal_payload = {
        "image": test_image_data,
        "side": "auto",
        "fast_mode": False
    }
    
    start_time = time.time()
    try:
        response = requests.post(api_url, json=normal_payload, timeout=30)
        normal_time = time.time() - start_time
        print(f"   ✅ 普通模式耗时: {normal_time:.3f}秒")
        print(f"   ✅ 状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 普通模式测试失败: {e}")
        return
    
    # 测试2：快速模式
    print("\n2. 测试快速模式...")
    fast_payload = {
        "image": test_image_data,
        "side": "auto", 
        "fast_mode": True
    }
    
    start_time = time.time()
    try:
        response = requests.post(api_url, json=fast_payload, timeout=30)
        fast_time = time.time() - start_time
        print(f"   ✅ 快速模式耗时: {fast_time:.3f}秒")
        print(f"   ✅ 状态码: {response.status_code}")
        if normal_time > 0:
            improvement = (normal_time - fast_time) / normal_time * 100
            print(f"   🚀 性能提升: {improvement:.1f}%")
    except Exception as e:
        print(f"   ❌ 快速模式测试失败: {e}")
    
    # 测试3：缓存功能（重复请求）
    print("\n3. 测试缓存功能...")
    start_time = time.time()
    try:
        response = requests.post(api_url, json=normal_payload, timeout=30)
        cache_time = time.time() - start_time
        print(f"   ✅ 缓存请求耗时: {cache_time:.3f}秒")
        print(f"   ✅ 状态码: {response.status_code}")
        if normal_time > 0:
            cache_improvement = (normal_time - cache_time) / normal_time * 100
            print(f"   🗄️ 缓存加速: {cache_improvement:.1f}%")
    except Exception as e:
        print(f"   ❌ 缓存测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("✅ 性能测试完成！")

def test_upload_performance():
    """测试文件上传接口的性能优化"""
    
    upload_url = "http://localhost:8000/api/v1/ocr/idcard/upload"
    
    print("\n🔧 文件上传性能测试")
    print("-" * 30)
    
    # 创建一个小的测试图片文件
    test_image_content = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
    
    # 测试普通模式
    print("1. 测试上传普通模式...")
    files = {'image': ('test.png', test_image_content, 'image/png')}
    data = {'side': 'auto', 'fast_mode': 'false'}
    
    start_time = time.time()
    try:
        response = requests.post(upload_url, files=files, data=data, timeout=30)
        normal_upload_time = time.time() - start_time
        print(f"   ✅ 普通上传耗时: {normal_upload_time:.3f}秒")
        print(f"   ✅ 状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 普通上传测试失败: {e}")
        return
    
    # 测试快速模式
    print("2. 测试上传快速模式...")
    files = {'image': ('test.png', test_image_content, 'image/png')}
    data = {'side': 'auto', 'fast_mode': 'true'}
    
    start_time = time.time()
    try:
        response = requests.post(upload_url, files=files, data=data, timeout=30)
        fast_upload_time = time.time() - start_time
        print(f"   ✅ 快速上传耗时: {fast_upload_time:.3f}秒")
        print(f"   ✅ 状态码: {response.status_code}")
        if normal_upload_time > 0:
            upload_improvement = (normal_upload_time - fast_upload_time) / normal_upload_time * 100
            print(f"   🚀 上传加速: {upload_improvement:.1f}%")
    except Exception as e:
        print(f"   ❌ 快速上传测试失败: {e}")

def test_config_display():
    """测试配置显示功能"""
    
    print("\n⚙️ 配置信息测试")
    print("-" * 30)
    
    try:
        from app.config import OCR_PERFORMANCE_CONFIG, VERSION
        print(f"版本: {VERSION}")
        print("性能配置:")
        for key, value in OCR_PERFORMANCE_CONFIG.items():
            print(f"  - {key}: {value}")
    except Exception as e:
        print(f"❌ 配置读取失败: {e}")

if __name__ == "__main__":
    print("🎯 身份证OCR性能优化测试套件")
    print("请确保服务已启动在 http://localhost:8000")
    print()
    
    # 测试配置显示
    test_config_display()
    
    # 等待用户确认服务已启动
    input("按回车键开始测试...")
    
    try:
        # 测试API性能
        test_api_performance()
        
        # 测试文件上传性能
        test_upload_performance()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试已中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中出现错误: {e}")
    
    print("\n🎉 测试结束！") 