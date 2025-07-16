# 身份证OCR识别服务

这是一个基于Python的身份证OCR识别服务端，提供REST API接口，支持高并发处理和性能优化。

## 📚 目录

1. [项目介绍](#项目介绍)
2. [功能特点](#功能特点)
3. [环境要求](#环境要求)
4. [快速开始](#-快速开始)
5. [配置管理](#-配置管理)
6. [性能优化](#-性能优化)
7. [API接口](#api接口)
8. [部署指南](#-部署指南)
9. [故障排查](#-故障排查)
10. [开发说明](#开发说明)

## 项目介绍

这是一个基于Python开发的身份证OCR识别服务，可以通过API接口识别身份证上的文字信息，支持并发处理多个请求。

### 主要功能
- 🇨🇳 **中国身份证识别**：正面（姓名、性别、民族、出生日期、住址、身份证号）、背面（签发机关、有效期限）
- 🌍 **外国人永久居留身份证识别**：支持新版和旧版外国人永久居留身份证
- 🤖 **智能自动检测**：无需手动指定证件类型，系统自动识别证件种类
- 📦 **批量处理**：支持批量识别多张证件图片
- 🔌 **REST API接口**：提供标准化API，方便集成到其他系统
- 📄 **多种上传方式**：支持Base64编码和文件上传两种方式提交图片

### 技术栈
- **FastAPI**: 现代高性能Web框架
- **PaddleOCR**: 百度开源OCR引擎
- **OpenCV**: 图像处理库
- **Uvicorn**: 高性能ASGI服务器
- **Loguru**: 现代Python日志库

## 功能特点

- 🎯 **高精度识别**：基于PaddleOCR的专业证件识别
- 🤖 **智能自动检测**：无需指定证件类型，系统自动识别中国身份证和外国人永久居留身份证
- 🌍 **多证件支持**：支持中国身份证、新版/旧版外国人永久居留身份证
- 🚀 **高并发支持**：多进程架构，支持高并发请求处理
- 🔧 **性能可调**：丰富的配置选项，适应不同硬件环境
- 📝 **RESTful API**：标准化接口，易于集成
- 📊 **详细日志**：完整的请求日志和错误跟踪
- 💾 **内存优化**：智能内存管理，适合资源受限环境
- 🔒 **安全认证**：支持API密钥验证
- 📱 **多种格式**：支持Base64和文件上传两种方式
- 🔄 **向后兼容**：完全兼容现有API调用方式

## 环境要求

### 🔧 基础要求
- Python 3.7或更高版本
- Windows、Linux或macOS操作系统

### 💾 硬件要求（根据使用场景选择）

| 使用场景 | CPU | 内存 | 并发能力 | 适用说明 |
|----------|-----|------|----------|----------|
| 🧪 开发测试 | 2核+ | 2-4GB | 2并发 | 功能验证、开发调试 |
| 💾 内存受限 | 4核+ | 4-8GB | 4并发 | 小型部署、内存有限 |
| 🔧 生产推荐 | 4-8核 | 8-16GB | 8并发 | 一般生产环境 |
| 🚀 高性能 | 8核+ | 16GB+ | 16并发+ | 高并发生产环境 |

## 🚀 快速开始

### 1. 安装Python环境

如果您还没有安装Python，请先从[Python官网](https://www.python.org/downloads/)下载并安装Python 3.7或更高版本。

### 2. 下载项目代码

将项目代码下载到本地，或者直接使用git克隆：

```bash
git clone https://github.com/hkxiaoyao/sfzocr.git
cd sfzocr
```

### 3. 安装依赖包

在项目根目录下执行以下命令安装所需的依赖包：

```bash
pip install -r requirements.txt
```

> ⏰ **安装提示**：安装过程可能需要几分钟时间，特别是PaddlePaddle和PaddleOCR这两个包比较大。如果安装PaddlePaddle时遇到问题，可以参考[PaddlePaddle官方安装指南](https://www.paddlepaddle.org.cn/install/quick)。

### 4. 快速启动

```bash
# 开发环境启动
python run.py --debug

# 生产环境启动
python run.py --host 0.0.0.0 --port 8000 --workers 4
```

### 5. 验证服务

服务启动后，可以通过以下方式验证：

```bash
# 访问API文档
open http://localhost:8000/docs

open http://localhost:8000/redoc
# 健康检查
curl http://localhost:8000/api/v1/health

# 测试API
curl -X POST "http://localhost:8000/api/v1/ocr/idcard" \
     -H "Content-Type: application/json" \
     -d '{"image":"BASE64_IMAGE_DATA"}'
```

## 🔧 配置管理

### 配置管理工具

本服务提供了强大的配置管理工具，所有功能已整合到 `app/config.py` 中，支持智能配置分析和优化建议：

```bash
# 查看完整配置摘要（默认行为）
python -m app.config

# 显示系统信息
python -m app.config --system-info

# 性能分析报告
python -m app.config --performance

# 部署配置指南
python -m app.config --deployment

# 验证当前配置
python -m app.config --validate

# 生成优化配置文件
python -m app.config --generate-env

# 显示所有信息
python -m app.config --all
```

### 智能配置分析

配置管理工具提供以下功能：

- 🔍 **智能分析**：自动检测系统硬件环境，分析配置合理性
- 📊 **性能评估**：提供0-100分的配置评分和优化建议
- 🎯 **个性化建议**：根据服务器规格提供量身定制的配置方案
- 🚀 **一键部署**：生成优化的.env配置文件和部署命令
- 📈 **实时监控**：持续监控配置状态和性能表现

### 配置文件说明

可以通过创建 `.env` 文件来自定义配置：

```bash
# 🚀 性能配置
WORKERS=4                          # Worker进程数
OCR_PROCESS_POOL_SIZE=3           # OCR进程池大小
MAX_CONCURRENT_REQUESTS=8         # 最大并发请求数
OCR_TASK_TIMEOUT=30               # OCR任务超时时间

# 💾 内存优化配置
MEMORY_OPTIMIZATION=true          # 启用内存优化
ENABLE_GC_AFTER_REQUEST=true      # 请求后垃圾回收

# 📝 日志配置
LOG_LEVEL=WARNING                 # 日志级别
LOG_ROTATION=20 MB               # 日志轮转大小
LOG_RETENTION=1 week             # 日志保留时间

# 🔒 安全配置
API_KEYS=your_secret_key_1,your_secret_key_2

# 🌐 网络配置
HOST=0.0.0.0                     # 监听地址
PORT=8000                        # 监听端口

# 💾 路径配置
OCR_MODEL_DIR=./models           # OCR模型目录
LOG_DIR=./logs                   # 日志目录
```

## ⚡ 性能优化

### 三档配置方案

系统根据服务器规格自动推荐相应方案：

#### 🏆 高性能方案（内存 ≥ 16GB）
适用于高并发生产环境，内存充足：
```bash
export WORKERS=6
export OCR_PROCESS_POOL_SIZE=4
export MAX_CONCURRENT_REQUESTS=10
export MEMORY_OPTIMIZATION=false
export LOG_LEVEL=INFO
```
- **特点**：高并发、高性能
- **内存需求**：~8-12GB
- **并发能力**：16+ 并发

#### ⚖️ 标准方案（内存 8-16GB）
适用于中等负载、标准生产环境：
```bash
export WORKERS=3
export OCR_PROCESS_POOL_SIZE=2
export MAX_CONCURRENT_REQUESTS=6
export MEMORY_OPTIMIZATION=true
export LOG_LEVEL=WARNING
```
- **特点**：性能与内存平衡
- **内存需求**：~4-6GB
- **并发能力**：8 并发

#### 💾 节能方案（内存 < 8GB）
适用于资源受限环境、测试环境：
```bash
export WORKERS=1
export OCR_PROCESS_POOL_SIZE=1
export MAX_CONCURRENT_REQUESTS=2
export MEMORY_OPTIMIZATION=true
export ENABLE_GC_AFTER_REQUEST=true
export LOG_LEVEL=ERROR
```
- **特点**：低内存占用
- **内存需求**：~1-2GB
- **并发能力**：2 并发

### 内存优化

针对内存受限环境的特殊优化：

| 配置项 | 优化前 | 优化后 | 降幅 |
|--------|--------|--------|------|
| Worker进程 | 4 | 1 | 75% |
| OCR进程池 | 4 | 2 | 50% |  
| 总进程数 | 16 | 2 | 87.5% |
| 预计内存 | 8-10GB | 1-1.5GB | 85% |

### 性能监控

```bash
# 内存使用监控
python memory_monitor.py

# 持续监控
python memory_monitor.py --monitor --interval 10 --threshold 1024

# 性能分析
python -m app.config --performance
```

## API接口

### 基础接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/docs` | GET | API文档 |
| `/api/v1/ocr/idcard` | POST | 身份证识别（JSON） |
| `/api/v1/ocr/idcard/upload` | POST | 身份证识别（文件上传） |
| `/api/v1/ocr/batch` | POST | 批量识别 |

### 示例代码

#### Python示例
```python
import requests
import base64

# 读取图片并转换为base64
with open("idcard.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# 发送识别请求
response = requests.post(
    "http://localhost:8000/api/v1/ocr/idcard",
    json={"image": image_data}
)

result = response.json()
print(result)
```

#### curl示例
```bash
# Base64方式
curl -X POST "http://localhost:8000/api/v1/ocr/idcard" \
     -H "Content-Type: application/json" \
     -d '{"image":"BASE64_IMAGE_DATA"}'

# 文件上传方式
curl -X POST "http://localhost:8000/api/v1/ocr/idcard/upload" \
     -F "file=@idcard.jpg"
```

### 返回格式

```json
{
  "success": true,
  "data": {
    "card_type": "FRONT",
    "card_info": {
      "name": "张三",
      "sex": "男",
      "nation": "汉",
      "birth": "1990年1月1日",
      "address": "北京市朝阳区某某街道",
      "id_number": "110101199001011234"
    }
  },
  "message": "识别成功",
  "request_id": "uuid-string"
}
```

## 🚀 部署指南

### Docker部署

```bash
# 构建镜像
docker build -t sfzocr:latest .

# 运行容器
docker run -d \
  --name sfzocr \
  -p 8000:8000 \
  -e WORKERS=4 \
  -e OCR_PROCESS_POOL_SIZE=3 \
  sfzocr:latest
```

### 生产环境部署

#### 1. 使用配置管理工具
```bash
# 检查系统环境
python -m app.config --system-info

# 生成优化配置
python -m app.config --generate-env

# 验证配置
python -m app.config --validate

# 启动服务
python run.py
```

#### 2. Nginx反向代理配置
```nginx
upstream sfzocr_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://sfzocr_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 3. 系统服务配置
```ini
# /etc/systemd/system/sfzocr.service
[Unit]
Description=身份证OCR识别服务
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/sfzocr
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 集群部署

```bash
# 启动多个实例
python run.py --port 8000 &
python run.py --port 8001 &
python run.py --port 8002 &
python run.py --port 8003 &

# 使用负载均衡器分发请求
```

## 🔍 故障排查

### 常见问题

#### 1. 内存不足 (OOM)
```bash
# 启用内存优化模式
export MEMORY_OPTIMIZATION=true
export ENABLE_GC_AFTER_REQUEST=true

# 减少进程数
export WORKERS=1
export OCR_PROCESS_POOL_SIZE=1
export MAX_CONCURRENT_REQUESTS=2

# 监控内存使用
python memory_monitor.py --monitor
```

#### 2. 识别准确率低
```bash
# 检查图片质量
# 图片应该清晰、光照充足、避免反光
# 推荐分辨率：1000x600以上

# 调整OCR参数
export OCR_DET_DB_THRESH=0.3
export OCR_DET_DB_BOX_THRESH=0.6
export OCR_DROP_SCORE=0.5
```

#### 3. 服务响应慢
```bash
# 增加进程数（确保有足够内存）
export WORKERS=4
export OCR_PROCESS_POOL_SIZE=3
export MAX_CONCURRENT_REQUESTS=8

# 启用性能优化
export MEMORY_OPTIMIZATION=false

# 检查性能瓶颈
python -m app.config --performance
```

#### 4. API密钥验证失败
```bash
# 设置API密钥
export API_KEYS=your_secret_key_1,your_secret_key_2

# 在请求头中添加密钥
curl -H "X-API-KEY: your_secret_key_1" \
     -X POST "http://localhost:8000/api/v1/ocr/idcard" \
     -d '{"image":"BASE64_DATA"}'
```

### 日志分析

```bash
# 查看实时日志
tail -f logs/sfzocr.log

# 查看错误日志
grep ERROR logs/sfzocr.log

# 查看性能日志
grep "耗时" logs/sfzocr.log
```

### 诊断工具

```bash
# 完整系统诊断
python -m app.config --all

# 配置验证
python -m app.config --validate

# 内存监控
python memory_monitor.py

# API测试
python test_api.py
```

## 开发说明

### 项目结构
```
sfzocr/
├── app/                    # 应用核心代码
│   ├── __init__.py
│   ├── main.py            # FastAPI应用入口
│   ├── config.py          # 配置管理
│   ├── api/               # API路由
│   │   ├── __init__.py
│   │   ├── endpoints.py   # API端点实现
│   │   └── models.py      # 数据模型
│   ├── core/              # 核心功能
│   │   ├── __init__.py
│   │   ├── ocr_engine.py  # OCR引擎
│   │   └── image_processor.py  # 图像处理
│   └── utils/             # 工具函数
│       ├── __init__.py
│       ├── logger.py      # 日志配置
│       ├── validators.py  # 数据验证
│       └── concurrency.py # 并发控制
├── memory_monitor.py       # 内存监控工具
├── run.py                 # 服务启动脚本
├── requirements.txt       # 依赖包列表
├── .env.example          # 配置文件示例
└── README.md             # 项目文档
```

### 开发环境搭建

```bash
# 克隆项目
git clone https://github.com/yourusername/sfzocr.git
cd sfzocr

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python run.py --debug
```

### API测试

```bash
# 运行API测试
python test_api.py

# 运行性能测试
python test_performance.py

# 运行所有测试
python -m pytest tests/
```

## 🔄 版本兼容性

- **向后兼容**：所有优化功能均为可选，不影响现有API
- **默认行为**：未启用优化时行为与之前版本一致
- **渐进升级**：可以逐步启用各项优化功能

## 📄 许可证

本项目采用MIT许可证，详情请参阅LICENSE文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进本项目。

## 📞 技术支持

如需技术支持或有任何问题，请：

1. 首先运行完整的配置检查：
   ```bash
   python -m app.config --all
   ```

2. 查看服务日志：
   ```bash
   tail -100 logs/sfzocr.log
   ```

3. 收集系统信息：
   ```bash
   python -m app.config --system-info > system_info.txt
   ```

---

**💡 提示**：建议从平衡模式开始使用，根据实际需求调整配置。通过配置管理工具可以获得个性化的优化建议。

*🚀 持续优化中，建议关注项目更新获取最新功能和性能改进。* 
