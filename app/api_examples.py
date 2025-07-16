#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
身份证OCR识别服务API使用示例

本文件提供了完整的API调用示例，包括：
- 单张身份证识别（JSON/文件上传）
- 批量身份证识别
- 错误处理示例
- 最佳实践建议
"""

import requests
import base64
import json
from pathlib import Path

# 服务基础URL
BASE_URL = "http://localhost:8000/api/v1"

class IDCardOCRClient:
    """身份证OCR客户端示例类"""
    
    def __init__(self, base_url=BASE_URL, api_key=None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-KEY"] = api_key
    
    def health_check(self):
        """健康检查示例"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def recognize_single_json(self, image_path, side="auto", debug=False, fast_mode=False):
        """
        单张身份证识别（JSON方式）
        
        Args:
            image_path: 图片文件路径
            side: 证件类型 (auto/front/back/foreign_new/foreign_old)
            debug: 调试模式
            fast_mode: 快速模式
        """
        # 读取并编码图片
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        data = {
            "image": image_data,
            "side": side,
            "debug": debug,
            "fast_mode": fast_mode
        }
        
        response = requests.post(
            f"{self.base_url}/ocr/idcard",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def recognize_single_upload(self, image_path, side="auto", debug=False, fast_mode=False):
        """
        单张身份证识别（文件上传方式）
        
        Args:
            image_path: 图片文件路径
            side: 证件类型
            debug: 调试模式
            fast_mode: 快速模式
        """
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'side': side,
                'debug': debug,
                'fast_mode': fast_mode
            }
            
            response = requests.post(
                f"{self.base_url}/ocr/idcard/upload",
                files=files,
                data=data
            )
        return response.json()
    
    def recognize_batch_json(self, image_paths_and_sides):
        """
        批量身份证识别（JSON方式）
        
        Args:
            image_paths_and_sides: [(path, side, fast_mode), ...]
        """
        images = []
        for path, side, fast_mode in image_paths_and_sides:
            with open(path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            images.append({
                "image": image_data,
                "side": side,
                "fast_mode": fast_mode
            })
        
        data = {"images": images}
        
        response = requests.post(
            f"{self.base_url}/ocr/idcard/batch",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def recognize_batch_upload(self, front_image=None, back_image=None, fast_mode=False):
        """
        批量身份证识别（文件上传方式）
        
        Args:
            front_image: 正面图片路径
            back_image: 背面图片路径
            fast_mode: 快速模式
        """
        files = {}
        if front_image:
            files['front_image'] = open(front_image, 'rb')
        if back_image:
            files['back_image'] = open(back_image, 'rb')
        
        data = {'fast_mode': fast_mode}
        
        try:
            response = requests.post(
                f"{self.base_url}/ocr/idcard/batch/upload",
                files=files,
                data=data
            )
            return response.json()
        finally:
            # 确保文件被关闭
            for f in files.values():
                f.close()

def example_usage():
    """API使用示例"""
    
    # 创建客户端
    client = IDCardOCRClient()
    
    print("=" * 60)
    print("身份证OCR识别服务API使用示例")
    print("=" * 60)
    
    # 1. 健康检查
    print("\n1. 健康检查")
    try:
        health = client.health_check()
        print(f"✅ 服务状态: {health['data']['status']}")
        print(f"   版本: {health['data']['version']}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return
    
    # 检查测试图片
    test_images = ["test.jpg", "test2.png"]
    available_images = [img for img in test_images if Path(img).exists()]
    
    if not available_images:
        print("\n⚠️  未找到测试图片，请确保当前目录有test.jpg或test2.png")
        return
    
    # 2. 单张识别（JSON方式）
    print(f"\n2. 单张识别（JSON方式）")
    try:
        result = client.recognize_single_json(available_images[0], side="auto")
        if result['code'] == 0:
            print(f"✅ 识别成功")
            data = result['data']
            if data:
                for key, value in data.items():
                    if value:
                        print(f"   {key}: {value}")
        else:
            print(f"❌ 识别失败: {result['message']}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 3. 单张识别（文件上传方式）
    print(f"\n3. 单张识别（文件上传方式）")
    try:
        result = client.recognize_single_upload(available_images[0], side="auto")
        if result['code'] == 0:
            print(f"✅ 识别成功")
            print(f"   识别字段数: {len([v for v in result['data'].values() if v])}")
        else:
            print(f"❌ 识别失败: {result['message']}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 4. 批量识别（如果有多张图片）
    if len(available_images) >= 2:
        print(f"\n4. 批量识别（JSON方式）")
        try:
            image_list = [
                (available_images[0], "auto", False),
                (available_images[1], "auto", True)  # 第二张使用快速模式
            ]
            result = client.recognize_batch_json(image_list)
            if result['code'] == 0:
                success_count = len([d for d in result['data'] if d])
                total_count = len(result['data'])
                print(f"✅ 批量识别完成: {success_count}/{total_count} 成功")
                if result['failed_indices']:
                    print(f"   失败索引: {result['failed_indices']}")
            else:
                print(f"❌ 批量识别失败: {result['message']}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    # 5. 错误处理示例
    print(f"\n5. 错误处理示例")
    try:
        # 尝试识别无效图片
        result = client.recognize_single_json(
            available_images[0].replace('.jpg', '_nonexistent.jpg'), 
            side="auto"
        )
        print(f"响应码: {result.get('code', 'unknown')}")
        print(f"错误信息: {result.get('message', 'unknown')}")
    except FileNotFoundError:
        print("✅ 正确处理了文件不存在的情况")
    except Exception as e:
        print(f"其他异常: {e}")
    
    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)

def api_documentation():
    """API文档和最佳实践"""
    
    doc = """
## 身份证OCR识别服务API文档

### 基础信息
- **基础URL**: http://localhost:8000/api/v1
- **认证方式**: API密钥（可选）
- **数据格式**: JSON
- **字符编码**: UTF-8

### 接口列表

#### 1. 健康检查
- **URL**: GET /health
- **功能**: 检查服务状态
- **认证**: 无需
- **响应**: 服务状态、版本信息

#### 2. 单张识别（JSON）
- **URL**: POST /ocr/idcard
- **功能**: 识别单张身份证
- **格式**: JSON请求体
- **参数**: image(base64), side, debug, fast_mode

#### 3. 单张识别（文件上传）
- **URL**: POST /ocr/idcard/upload
- **功能**: 识别单张身份证
- **格式**: multipart/form-data
- **参数**: image(file), side, debug, fast_mode

#### 4. 批量识别（JSON）
- **URL**: POST /ocr/idcard/batch
- **功能**: 批量识别身份证（最多10张）
- **格式**: JSON请求体
- **参数**: images数组

#### 5. 批量识别（文件上传）
- **URL**: POST /ocr/idcard/batch/upload
- **功能**: 批量识别正反面
- **格式**: multipart/form-data
- **参数**: front_image, back_image, fast_mode

### 证件类型
- `auto`: 自动检测（推荐）
- `front`: 中国身份证正面
- `back`: 中国身份证背面
- `foreign_new`: 新版外国人永久居留证
- `foreign_old`: 旧版外国人永久居留证

### 响应状态码
- `0`: 成功
- `1001`: 参数错误
- `1002`: 图像处理错误
- `1003`: OCR识别错误
- `9999`: 系统错误

### 参数详细说明

#### debug参数使用指南
- **开发环境**: 建议启用debug=true，便于问题诊断
- **生产环境**: 使用debug=false，返回结构化数据
- **调试场景**: 识别结果不准确时，查看原始OCR文本
- **返回差异**: debug模式返回ocr_text数组，正常模式返回结构化字段

#### fast_mode参数使用指南
- **标准模式** (fast_mode=false):
  - 准确率: 99%+
  - 识别时间: 2-3秒
  - 适用: 金融认证、法律文档、高精度要求
  
- **快速模式** (fast_mode=true):
  - 准确率: 95%+
  - 识别时间: 1-1.5秒  
  - 适用: 实时预览、批量处理、用户体验优化

#### side参数使用建议
- **auto**: 智能检测，推荐默认选择
- **front/back**: 明确知道证件正反面时使用
- **foreign_new/foreign_old**: 外国人永久居留证专用

### 最佳实践

1. **图片质量**:
   - 分辨率 ≥ 300DPI
   - 文件大小 ≤ 10MB
   - 光照充足、避免反光
   - 证件完整、清晰可见

2. **性能优化**:
   - 批量处理优于单张
   - 根据场景选择fast_mode
   - 合理设置超时时间
   - 使用auto自动检测节省开发成本

3. **错误处理**:
   - 检查响应状态码
   - 记录失败原因
   - 实现重试机制
   - debug模式排查识别问题

4. **安全建议**:
   - 配置API密钥
   - 使用HTTPS传输
   - 及时清理临时文件
   - 记录访问日志

### 集成示例

#### Python
```python
import requests
import base64

# 基础配置
url = "http://localhost:8000/api/v1/ocr/idcard"
headers = {"Content-Type": "application/json"}

# 图片编码
with open("idcard.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# 示例1：标准模式（高精度）
data = {
    "image": image_data,
    "side": "auto",        # 自动检测
    "debug": False,        # 生产模式
    "fast_mode": False     # 标准模式
}
response = requests.post(url, json=data, headers=headers)
result = response.json()

if result["code"] == 0:
    print("识别成功:", result["data"])
    # 输出: {"name": "张三", "sex": "男", ...}
else:
    print("识别失败:", result["message"])

# 示例2：快速模式（高速度）
data_fast = {
    "image": image_data,
    "side": "front",       # 明确指定正面
    "debug": False,
    "fast_mode": True      # 快速模式
}
response_fast = requests.post(url, json=data_fast, headers=headers)

# 示例3：调试模式（问题排查）
data_debug = {
    "image": image_data,
    "side": "auto",
    "debug": True,         # 调试模式
    "fast_mode": False
}
response_debug = requests.post(url, json=data_debug, headers=headers)
debug_result = response_debug.json()

if debug_result["code"] == 0:
    print("原始OCR文本:", debug_result["data"]["ocr_text"])
    # 输出: ["姓名 张三", "性别 男", "民族 汉", ...]
```

#### cURL
```bash
# 标准模式（高精度）
curl -X POST "http://localhost:8000/api/v1/ocr/idcard/upload" \\
     -F "image=@idcard.jpg" \\
     -F "side=auto" \\
     -F "debug=false" \\
     -F "fast_mode=false"

# 快速模式（高速度）
curl -X POST "http://localhost:8000/api/v1/ocr/idcard/upload" \\
     -F "image=@idcard.jpg" \\
     -F "side=front" \\
     -F "debug=false" \\
     -F "fast_mode=true"

# 调试模式（问题排查）
curl -X POST "http://localhost:8000/api/v1/ocr/idcard/upload" \\
     -F "image=@idcard.jpg" \\
     -F "side=auto" \\
     -F "debug=true" \\
     -F "fast_mode=false"
```

#### JavaScript (fetch)
```javascript
// 文件上传方式
const formData = new FormData();
formData.append('image', fileInput.files[0]);
formData.append('side', 'auto');

fetch('/api/v1/ocr/idcard/upload', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.code === 0) {
        console.log('识别成功:', data.data);
    } else {
        console.error('识别失败:', data.message);
    }
});
```

### 常见问题

**Q: 为什么识别准确率不高？**
A: 请检查图片质量，确保光照充足、证件完整、分辨率足够。

**Q: 批量处理有什么限制？**
A: 单次最多10张图片，总数据量建议不超过50MB。

**Q: 如何提高识别速度？**
A: 使用fast_mode参数，或考虑升级服务器配置。

**Q: 支持哪些图片格式？**
A: 支持JPG、PNG、BMP、TIFF等常见格式。

**Q: 如何配置API密钥？**
A: 在请求头中添加X-API-KEY字段。
"""
    
    return doc

if __name__ == "__main__":
    # 运行使用示例
    example_usage()
    
    # 显示文档（可选）
    # print(api_documentation()) 