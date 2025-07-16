# 🚀 配置优化指南

本文档帮助您根据服务器性能优化身份证OCR识别服务的配置，提高服务性能和稳定性。

## 📋 快速开始

### 1. 查看当前配置和优化建议
```bash
python app/config.py
```

### 2. 检查系统配置（需要安装psutil）
```bash
# 安装依赖
pip install psutil

# 运行配置检查器
python tools/config_checker.py
```

### 3. 获取推荐配置（示例：8核16GB服务器）
```bash
python tools/config_checker.py --recommend 8 16
```

### 4. 导出配置文件
```bash
python tools/config_checker.py --export .env
```

## 🎯 配置方案选择

### 🚀 方案A：高性能服务器（16GB+内存，8核+CPU）
**适用场景**：高并发生产环境，内存充足  
**预期性能**：高并发处理，低延迟  
**内存需求**：约12-16GB

```bash
export WORKERS=8
export OCR_PROCESS_POOL_SIZE=8
export MAX_CONCURRENT_REQUESTS=16
export MEMORY_OPTIMIZATION=False
export ENABLE_GC_AFTER_REQUEST=False
export LOG_LEVEL=INFO
export OCR_TASK_TIMEOUT=15
```

### 💾 方案B：内存受限服务器（4-8GB内存，4核CPU）
**适用场景**：内存受限环境，注重稳定性  
**预期性能**：中等并发，内存占用低  
**内存需求**：约3-5GB

```bash
export WORKERS=2
export OCR_PROCESS_POOL_SIZE=2
export MAX_CONCURRENT_REQUESTS=4
export MEMORY_OPTIMIZATION=True
export ENABLE_GC_AFTER_REQUEST=True
export LOG_LEVEL=WARNING
export OCR_TASK_TIMEOUT=60
```

### 🔧 方案C：生产环境推荐（8-16GB内存，4-8核CPU）
**适用场景**：生产环境，平衡性能和稳定性  
**预期性能**：稳定高效，资源利用合理  
**内存需求**：约6-10GB

```bash
export WORKERS=4
export OCR_PROCESS_POOL_SIZE=4
export MAX_CONCURRENT_REQUESTS=8
export MEMORY_OPTIMIZATION=True
export ENABLE_GC_AFTER_REQUEST=True
export LOG_LEVEL=WARNING
export OCR_TASK_TIMEOUT=30
export DEBUG=False
export API_KEYS="your-secret-key-1,your-secret-key-2"
```

### 🧪 方案D：开发/测试环境
**适用场景**：开发调试，功能测试  
**预期性能**：便于调试，快速启动  
**内存需求**：约2-4GB

```bash
export WORKERS=1
export OCR_PROCESS_POOL_SIZE=1
export MAX_CONCURRENT_REQUESTS=2
export MEMORY_OPTIMIZATION=True
export ENABLE_GC_AFTER_REQUEST=True
export LOG_LEVEL=DEBUG
export OCR_TASK_TIMEOUT=60
export DEBUG=True
```

## ⚙️ 配置参数详解

### 🔧 核心性能参数

| 参数 | 说明 | 性能影响 | 推荐值 |
|------|------|----------|--------|
| `WORKERS` | Uvicorn工作进程数 | 影响并发处理能力和内存占用 | CPU核心数或CPU核心数*2 |
| `OCR_PROCESS_POOL_SIZE` | OCR处理进程池大小 | 影响OCR并发能力，每个进程约1GB内存 | 2-8（根据内存调整） |
| `MAX_CONCURRENT_REQUESTS` | 最大并发请求数 | 限制同时处理请求数，防止内存溢出 | OCR_PROCESS_POOL_SIZE * 2 |
| `OCR_TASK_TIMEOUT` | OCR任务超时时间（秒） | 防止任务卡死 | 15-60秒 |

### 💾 内存优化参数

| 参数 | 说明 | 内存影响 | 推荐场景 |
|------|------|----------|----------|
| `MEMORY_OPTIMIZATION` | 启用内存优化 | 轻微影响性能但大幅降低内存占用 | 内存<16GB时启用 |
| `ENABLE_GC_AFTER_REQUEST` | 请求后强制垃圾回收 | 稍微增加响应时间但降低内存占用 | 生产环境推荐启用 |

### 📝 日志配置参数

| 参数 | 说明 | 性能影响 | 推荐值 |
|------|------|----------|--------|
| `LOG_LEVEL` | 日志级别 | 影响磁盘I/O和内存 | 生产:WARNING, 开发:DEBUG |
| `LOG_ROTATION` | 日志轮转大小 | 影响磁盘空间 | 20-50MB |
| `LOG_RETENTION` | 日志保留时间 | 影响磁盘空间 | 1 week - 1 month |

## 📊 性能监控

### 内存监控
```bash
# 监控进程内存使用
ps aux | grep python

# 系统内存使用
free -h

# 实时监控
htop
```

### CPU监控
```bash
# CPU使用率
top

# 进程CPU占用
ps aux --sort=-%cpu
```

### 日志监控
```bash
# 实时查看日志
tail -f logs/sfzocr.log

# 错误统计
grep ERROR logs/sfzocr.log | wc -l

# 查看最近的错误
tail -n 100 logs/sfzocr.log | grep ERROR
```

## 🚨 故障排除

### 内存不足（OOM）
**症状**：服务频繁重启，出现内存不足错误
```bash
# 解决方案
export WORKERS=1
export OCR_PROCESS_POOL_SIZE=1
export MAX_CONCURRENT_REQUESTS=2
export MEMORY_OPTIMIZATION=True
export ENABLE_GC_AFTER_REQUEST=True
```

### 响应慢
**症状**：API响应时间过长
```bash
# 解决方案（如内存充足）
export OCR_PROCESS_POOL_SIZE=4  # 增加OCR进程
export MAX_CONCURRENT_REQUESTS=8  # 增加并发
export MEMORY_OPTIMIZATION=False  # 关闭内存优化
export OCR_TASK_TIMEOUT=15  # 缩短超时时间
```

### 高CPU占用
**症状**：CPU使用率持续很高
```bash
# 解决方案
export WORKERS=2  # 减少工作进程
export OCR_PROCESS_POOL_SIZE=2  # 减少OCR进程

# 检查是否有死循环进程
ps aux --sort=-%cpu | head -10
```

### 磁盘空间不足
**症状**：日志文件占用大量磁盘空间
```bash
# 解决方案
export LOG_ROTATION="10 MB"  # 减少日志文件大小
export LOG_RETENTION="3 days"  # 缩短保留时间

# 清理旧日志
find logs/ -name "*.log.*" -mtime +7 -delete
```

## 🔧 实用工具

### 配置模板文件
- `config_template.env` - 包含各种场景的配置模板
- 复制并修改为 `.env` 使用

### 配置检查器
```bash
# 基本检查
python tools/config_checker.py

# 验证配置
python tools/config_checker.py --validate

# 推荐配置
python tools/config_checker.py --recommend 8 16

# 导出配置
python tools/config_checker.py --export production.env
```

### 配置验证
```bash
# 检查配置文件语法
python -c "from app.config import *; print('配置加载成功')"

# 查看配置摘要
python app/config.py
```

## 📈 性能基准

| 配置方案 | 内存使用 | 并发能力 | 响应时间 | 适用场景 |
|----------|----------|----------|----------|----------|
| 高性能   | 12-16GB  | 16并发   | <2秒     | 高并发生产环境 |
| 平衡     | 6-10GB   | 8并发    | <3秒     | 一般生产环境 |
| 节约     | 3-5GB    | 4并发    | <5秒     | 内存受限环境 |
| 开发     | 2-4GB    | 2并发    | <10秒    | 开发测试环境 |

## 📞 技术支持

如果您在配置优化过程中遇到问题：

1. 查看日志文件：`logs/sfzocr.log`
2. 运行配置检查器：`python tools/config_checker.py`
3. 验证系统资源：`htop`, `free -h`, `df -h`
4. 检查进程状态：`ps aux | grep python`

---

*本文档会根据项目更新持续完善，建议定期查看最新版本。* 