#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试真实外国人身份证英文姓名提取
"""

import sys
import base64
from pathlib import Path

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.core.ocr_engine import extract_id_card_info

def test_with_actual_image():
    """使用实际图像测试"""
    print("🧪 使用实际图像测试外国人身份证识别")
    print("=" * 60)
    
    # 检查是否有外国人身份证测试图像
    test_images = [
        "wgsfzj.png",  # 从git status可以看到有这个文件
        "wgsfzx.png"   # 还有这个文件
    ]
    
    for image_file in test_images:
        if Path(image_file).exists():
            print(f"\n📷 测试图像: {image_file}")
            print("-" * 30)
            
            # 读取图像
            try:
                with open(image_file, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode()
                
                # 先测试调试模式，看原始OCR输出
                print("🔍 调试模式 - 原始OCR输出:")
                debug_result = extract_id_card_info(image_data, card_type="foreign_old", debug=True)
                
                if "ocr_text" in debug_result:
                    print("📋 识别到的文本:")
                    for i, text in enumerate(debug_result["ocr_text"]):
                        print(f"  [{i}] {text}")
                    
                    # 检查是否有潜在的英文姓名
                    print("\n🔍 分析英文姓名候选:")
                    for text in debug_result["ocr_text"]:
                        if len(text) > 8 and text.isupper():
                            print(f"  ✓ 候选: {text}")
                else:
                    print("❌ 调试结果中没有OCR文本")
                
                # 测试正式识别
                print("\n🎯 正式识别 - 旧版模式:")
                result_old = extract_id_card_info(image_data, card_type="foreign_old", debug=False)
                
                print("📊 旧版识别结果:")
                for key, value in result_old.items():
                    status = "✅" if value else "❌"
                    print(f"  {status} {key}: {value}")
                
                # 测试新版模式
                print("\n🎯 正式识别 - 新版模式:")
                result_new = extract_id_card_info(image_data, card_type="foreign_new", debug=False)
                
                print("📊 新版识别结果:")
                for key, value in result_new.items():
                    status = "✅" if value else "❌"
                    print(f"  {status} {key}: {value}")
                
                # 测试自动检测
                print("\n🎯 正式识别 - 自动检测:")
                result_auto = extract_id_card_info(image_data, card_type="auto", debug=False)
                
                print("📊 自动检测结果:")
                for key, value in result_auto.items():
                    status = "✅" if value else "❌"
                    print(f"  {status} {key}: {value}")
                
                return result_old, result_new, result_auto
                
            except Exception as e:
                print(f"❌ 处理图像 {image_file} 时出错: {e}")
        else:
            print(f"⚠️  图像文件不存在: {image_file}")
    
    print("\n❌ 没有找到可用的测试图像")
    return None, None, None

if __name__ == "__main__":
    test_with_actual_image() 