# 身份证OCR识别服务安装指南

## 环境要求

- Python 3.7+
- 操作系统: Windows/Linux/macOS

## 安装步骤

### 1. 安装依赖

首先，安装所需的Python依赖包:

```bash
# 进入项目目录
cd sfzocr

# 安装依赖
pip install -r requirements.txt
```

注意: PaddlePaddle可能需要特定的安装步骤，具体请参考[PaddlePaddle官方文档](https://www.paddlepaddle.org.cn/install/quick)。

### 2. 配置环境变量(可选)

可以通过环境变量自定义服务配置:

```bash
# 服务配置
export DEBUG=true
export HOST=0.0.0.0
export PORT=8080
export WORKERS=4

# OCR配置
export OCR_MODEL_DIR=/path/to/models
export OCR_PROCESS_POOL_SIZE=2
export OCR_TASK_TIMEOUT=30

# 日志配置
export LOG_LEVEL=INFO
export LOG_DIR=/path/to/logs
export LOG_FILENAME=sfzocr.log
export LOG_ROTATION="20 MB"
export LOG_RETENTION="1 week"

# 安全配置
export API_KEYS=key1,key2,key3
```

## 启动服务

### 开发环境

```bash
# 进入项目目录
cd sfzocr

# 启动开发服务器
python run.py --debug
```

### 生产环境

```bash
# 进入项目目录
cd sfzocr

# 启动生产服务器
python run.py --host 0.0.0.0 --port 8080 --workers 4
```

## 常见问题

### 1. PaddleOCR安装问题

如果安装PaddleOCR时遇到问题，可以尝试:

```bash
# 先安装PaddlePaddle
pip install paddlepaddle==2.5.2

# 再安装PaddleOCR
pip install paddleocr==2.6.0.3
```

### 2. 服务启动失败

检查日志文件，查看具体错误信息:

```bash
cat logs/sfzocr.log
```

### 3. 内存不足

如果服务运行时出现内存不足的情况，可以尝试减少OCR进程池大小:

```bash
export OCR_PROCESS_POOL_SIZE=1
```

## 测试服务

服务启动后，可以通过以下方式测试:

1. 访问API文档: http://localhost:8000/docs
2. 健康检查: http://localhost:8000/api/v1/health
3. 使用curl测试API:

```bash
curl -X POST "http://localhost:8000/api/v1/ocr/idcard" \
     -H "Content-Type: application/json" \
     -d '{"image":"BASE64_IMAGE_DATA","side":"front"}'
``` 