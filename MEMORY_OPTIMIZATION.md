# OCR服务内存优化部署说明

## 问题背景

原有架构在4H4G服务器上部署时，由于双层进程池设计导致内存占用过高（约8-10GB），频繁出现OOM崩溃。

## 优化措施

### 1. 进程池配置优化
- **Worker进程数**: 从4降至1 (减少75%内存占用)
- **OCR进程池大小**: 从4降至2 (减少50%内存占用)  
- **总进程数**: 从16降至2 (减少87.5%内存占用)

### 2. 内存使用监控
- 添加实时内存监控和告警
- 支持内存使用阈值配置
- 提供内存监控工具脚本

### 3. 图像处理优化
- 跳过复杂的轮廓检测和图像校正
- 降低图像最大处理尺寸
- 添加显式垃圾回收机制

### 4. 日志级别优化
- 默认日志级别调整为WARNING
- 内存优化模式下使用DEBUG级别
- 减少日志输出对内存的影响

## 环境变量配置

可通过环境变量调整优化参数:

```bash
# 基础配置
WORKERS=1                           # Worker进程数
OCR_PROCESS_POOL_SIZE=2            # OCR进程池大小
LOG_LEVEL=WARNING                  # 日志级别

# 内存优化配置  
MEMORY_OPTIMIZATION=True           # 启用内存优化模式
MAX_CONCURRENT_REQUESTS=3          # 最大并发请求数
ENABLE_GC_AFTER_REQUEST=True       # 请求后垃圾回收
```

## 部署步骤

### 1. 更新依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务（内存优化模式）
```bash
python run.py --host 0.0.0.0 --port 8000
```

### 3. 监控内存使用
```bash
# 一次性检查
python memory_monitor.py

# 持续监控
python memory_monitor.py --monitor --interval 10 --threshold 1024
```

## 内存使用预期

| 配置项 | 优化前 | 优化后 | 降幅 |
|--------|--------|--------|------|
| Worker进程 | 4 | 1 | 75% |
| OCR进程池 | 4 | 2 | 50% |  
| 总进程数 | 16 | 2 | 87.5% |
| 预计内存 | 8-10GB | 1-1.5GB | 85% |

## 性能影响

- **并发处理能力**: 降低约60-70%
- **响应延迟**: 高负载时可能增加1-2秒
- **功能完整性**: 保持100%兼容
- **识别准确率**: 轻微下降（跳过图像增强）

## 监控告警

### 内存阈值
- **正常**: < 1GB
- **关注**: 1-2GB  
- **警告**: > 2GB

### 监控指标
- 进程内存使用量
- 系统内存使用率
- OCR任务执行时间
- 请求响应延迟

## 故障排查

### 1. 服务仍然OOM
```bash
# 检查配置是否生效
python memory_monitor.py

# 进一步降低进程数
export OCR_PROCESS_POOL_SIZE=1
```

### 2. 性能过慢
```bash
# 适当增加进程数（谨慎）
export OCR_PROCESS_POOL_SIZE=3

# 监控内存变化
python memory_monitor.py --monitor
```

### 3. 功能异常
```bash
# 关闭内存优化模式
export MEMORY_OPTIMIZATION=False

# 恢复详细日志
export LOG_LEVEL=INFO
```

## 长期优化建议

1. **升级硬件**: 8H8G配置可考虑恢复多进程
2. **架构重构**: 考虑OCR引擎微服务化
3. **模型优化**: 使用更轻量的OCR模型
4. **缓存策略**: 添加OCR结果缓存机制

## 回滚方案

如需回滚到原配置:

```bash
export WORKERS=4
export OCR_PROCESS_POOL_SIZE=4  
export LOG_LEVEL=INFO
export MEMORY_OPTIMIZATION=False
```

注意：回滚后在4GB内存环境下仍可能出现OOM问题。 