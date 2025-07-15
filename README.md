# 身份证OCR识别服务

这是一个基于Python的身份证OCR识别服务端，提供REST API接口，支持并发处理。

## 功能特点

- 身份证正面识别（姓名、性别、民族、出生日期、住址、身份证号）
- 身份证背面识别（签发机关、有效期限）
- 高并发支持
- RESTful API接口
- 详细的日志记录

## 技术栈

- FastAPI: Web框架
- PaddleOCR: OCR引擎
- OpenCV: 图像处理
- Uvicorn: ASGI服务器

## 安装

1. 克隆仓库
```bash
git clone https://github.com/yourusername/sfzocr.git
cd sfzocr
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

1. 启动服务
```bash
cd sfzocr
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

2. API文档
启动服务后，访问 http://localhost:8000/docs 查看API文档

## API示例

### 身份证识别

```
POST /api/v1/ocr/idcard
```

请求体:
```json
{
  "image": "base64编码的图片数据"
}
```

响应:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "name": "张三",
    "sex": "男",
    "nation": "汉",
    "birth": "1990年01月01日",
    "address": "北京市朝阳区...",
    "id_number": "110101199001010123",
    "issue_authority": "北京市公安局", // 如果提供了背面图片
    "valid_period": "2010.01.01-2020.01.01" // 如果提供了背面图片
  }
}
```

## 许可证

MIT
