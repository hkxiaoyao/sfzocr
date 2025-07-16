#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
身份证OCR识别服务API测试脚本
"""

import os
import sys
import json
import base64
import argparse
import requests
from pathlib import Path

def read_image_as_base64(image_path):
    """
    读取图片文件并转换为base64编码
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        base64编码的图片数据
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def test_health_api(base_url):
    """
    测试健康检查API
    
    Args:
        base_url: API基础URL
    """
    url = f"{base_url}/health"
    
    print(f"\n正在测试健康检查API: {url}")
    
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and response.json().get("code") == 0:
            print("✓ 健康检查API测试通过")
        else:
            print("✗ 健康检查API测试失败")
    except Exception as e:
        print(f"✗ 健康检查API测试异常: {str(e)}")

def test_idcard_api(base_url, image_path, side="front"):
    """
    测试身份证识别API
    
    Args:
        base_url: API基础URL
        image_path: 身份证图片路径
        side: 身份证正反面，可选值：front（正面）、back（背面）
    """
    url = f"{base_url}/ocr/idcard"
    
    print(f"\n正在测试身份证识别API: {url}")
    print(f"图片路径: {image_path}")
    print(f"身份证面: {side}")
    
    try:
        # 读取图片并转换为base64
        image_base64 = read_image_as_base64(image_path)
        
        # 构造请求数据
        data = {
            "image": image_base64,
            "side": side
        }
        
        # 发送请求
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and response.json().get("code") == 0:
            print("✓ 身份证识别API测试通过")
        else:
            print("✗ 身份证识别API测试失败")
    except Exception as e:
        print(f"✗ 身份证识别API测试异常: {str(e)}")

def test_idcard_upload_api(base_url, image_path, side="front"):
    """
    测试身份证识别文件上传API
    
    Args:
        base_url: API基础URL
        image_path: 身份证图片路径
        side: 身份证正反面，可选值：front（正面）、back（背面）
    """
    url = f"{base_url}/ocr/idcard/upload"
    
    print(f"\n正在测试身份证识别文件上传API: {url}")
    print(f"图片路径: {image_path}")
    print(f"身份证面: {side}")
    
    try:
        # 打开图片文件
        with open(image_path, "rb") as f:
            image_file = f.read()
        
        # 构造multipart/form-data请求
        files = {
            "image": (os.path.basename(image_path), image_file, "image/jpeg")
        }
        data = {
            "side": side
        }
        
        # 发送请求
        response = requests.post(url, files=files, data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and response.json().get("code") == 0:
            print("✓ 身份证识别文件上传API测试通过")
        else:
            print("✗ 身份证识别文件上传API测试失败")
    except Exception as e:
        print(f"✗ 身份证识别文件上传API测试异常: {str(e)}")

def test_batch_idcard_api(base_url, image_paths):
    """
    测试批量身份证识别API
    
    Args:
        base_url: API基础URL
        image_paths: 身份证图片路径列表，格式为[(图片路径, 面)]
    """
    url = f"{base_url}/ocr/idcard/batch"
    
    print(f"\n正在测试批量身份证识别API: {url}")
    print(f"图片数量: {len(image_paths)}")
    
    try:
        # 构造请求数据
        images = []
        for path, side in image_paths:
            image_base64 = read_image_as_base64(path)
            images.append({
                "image": image_base64,
                "side": side
            })
        
        data = {
            "images": images
        }
        
        # 发送请求
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and response.json().get("code") == 0:
            print("✓ 批量身份证识别API测试通过")
        else:
            print("✗ 批量身份证识别API测试失败")
    except Exception as e:
        print(f"✗ 批量身份证识别API测试异常: {str(e)}")

def test_batch_idcard_upload_api(base_url, front_image_path=None, back_image_path=None):
    """
    测试批量身份证识别文件上传API
    
    Args:
        base_url: API基础URL
        front_image_path: 身份证正面图片路径
        back_image_path: 身份证背面图片路径
    """
    url = f"{base_url}/ocr/idcard/batch/upload"
    
    print(f"\n正在测试批量身份证识别文件上传API: {url}")
    print(f"正面图片: {front_image_path}")
    print(f"背面图片: {back_image_path}")
    
    try:
        # 构造multipart/form-data请求
        files = {}
        
        # 添加正面图片
        if front_image_path:
            with open(front_image_path, "rb") as f:
                front_file = f.read()
            files["front_image"] = (os.path.basename(front_image_path), front_file, "image/jpeg")
        
        # 添加背面图片
        if back_image_path:
            with open(back_image_path, "rb") as f:
                back_file = f.read()
            files["back_image"] = (os.path.basename(back_image_path), back_file, "image/jpeg")
        
        # 发送请求
        response = requests.post(url, files=files)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and response.json().get("code") == 0:
            print("✓ 批量身份证识别文件上传API测试通过")
        else:
            print("✗ 批量身份证识别文件上传API测试失败")
    except Exception as e:
        print(f"✗ 批量身份证识别文件上传API测试异常: {str(e)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="身份证OCR识别服务API测试脚本")
    
    parser.add_argument(
        "--url", 
        type=str, 
        default="http://localhost:8000/api/v1",
        help="API基础URL，默认: http://localhost:8000/api/v1"
    )
    
    parser.add_argument(
        "--image", 
        type=str, 
        help="身份证图片路径，用于测试单张识别API"
    )
    
    parser.add_argument(
        "--side", 
        type=str, 
        default="front",
        choices=["front", "back"],
        help="身份证面，可选值：front（正面）、back（背面），默认: front"
    )
    
    parser.add_argument(
        "--front", 
        type=str, 
        help="身份证正面图片路径，用于测试批量识别API"
    )
    
    parser.add_argument(
        "--back", 
        type=str, 
        help="身份证背面图片路径，用于测试批量识别API"
    )
    
    parser.add_argument(
        "--health", 
        action="store_true", 
        help="测试健康检查API"
    )
    
    parser.add_argument(
        "--upload", 
        action="store_true", 
        help="使用文件上传API进行测试"
    )
    
    args = parser.parse_args()
    
    # 测试健康检查API
    if args.health or not (args.image or (args.front and args.back)):
        test_health_api(args.url)
    
    # 测试单张身份证识别API
    if args.image:
        if args.upload:
            test_idcard_upload_api(args.url, args.image, args.side)
        else:
            test_idcard_api(args.url, args.image, args.side)
    
    # 测试批量身份证识别API
    if args.front or args.back:
        if args.upload:
            test_batch_idcard_upload_api(args.url, args.front, args.back)
        else:
            if args.front and args.back:
                image_paths = [
                    (args.front, "front"),
                    (args.back, "back")
                ]
                test_batch_idcard_api(args.url, image_paths)

if __name__ == "__main__":
    main() 