#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import json

from app.api.endpoints import router as api_router
from app.config import PROJECT_NAME, VERSION, API_V1_PREFIX, CORS_ORIGINS, ALLOWED_HOSTS
from app.utils.logger import get_logger, log_request

# 获取logger
logger = get_logger("main")

# 创建FastAPI应用
app = FastAPI(
    title=PROJECT_NAME,
    description="身份证OCR识别服务API",
    version=VERSION,
    docs_url=None,  # 禁用默认的Swagger UI
    redoc_url=None  # 禁用默认的ReDoc
)

# 添加422错误的详细处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理422参数验证错误，提供详细错误信息"""
    error_details = []
    for error in exc.errors():
        error_detail = {
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input", "N/A")
        }
        error_details.append(error_detail)
    
    # 记录详细错误信息
    logger.error(f"422参数验证失败 - URL: {request.url} - 错误详情: {json.dumps(error_details, ensure_ascii=False)}")
    
    return JSONResponse(
        status_code=422,
        content={
            "code": 1001,
            "message": "请求参数验证失败",
            "data": None,
            "validation_errors": error_details
        }
    )

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = (time.time() - start_time) * 1000
    
    # 记录请求日志
    await log_request(request, response.status_code, process_time)
    
    return response

# 注册API路由
app.include_router(api_router, prefix=API_V1_PREFIX)

# 自定义OpenAPI文档
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=PROJECT_NAME,
        version=VERSION,
        description="""
## 身份证OCR识别服务API文档

### 功能特性
- 🆔 **多证件类型支持**: 中国居民身份证、外国人永久居留身份证
- 🔍 **智能自动检测**: 自动识别证件类型和正反面
- ⚡ **高性能处理**: 支持单张和批量识别，快速模式可选
- 🛡️ **安全可靠**: API密钥验证，请求限流保护
- 📊 **全面监控**: 健康检查，性能指标，日志记录

### 支持的证件类型
1. **中国居民身份证**
   - 正面：姓名、性别、民族、出生日期、住址、身份证号码
   - 背面：签发机关、有效期限

2. **外国人永久居留身份证**
   - 新版：中英文姓名、性别、出生日期、国籍、证件号码等
   - 旧版：同新版，识别算法优化适配

### 使用场景
- 用户注册身份验证
- 实名认证系统集成
- 金融业务身份核验
- 政务服务在线办理

### 接口特点
- RESTful API设计
- JSON格式数据交换
- Base64图像传输
- 详细错误码说明
        """,
        routes=app.routes,
    )
    
    # 自定义OpenAPI文档元信息
    openapi_schema["info"].update({
        "x-logo": {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        },
        "contact": {
            "name": "身份证OCR识别服务",
            "url": "https://github.com/hkxiaoyao/sfzocr",
            "email": "support@example.com"
        },
        "license": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        "termsOfService": "/terms",
        "x-api-features": [
            "高精度OCR识别",
            "多证件类型支持", 
            "批量处理能力",
            "实时性能监控",
            "安全API访问"
        ]
    })
    
    # 添加服务器信息
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "开发环境"
        },
        {
            "url": "https://api.example.com",
            "description": "生产环境"
        }
    ]
    
    # 添加详细的API标签描述
    openapi_schema["tags"] = [
        {
            "name": "OCR",
            "description": """
            ### 身份证OCR识别接口
            
            **核心功能**：
            - 单张身份证识别（JSON/文件上传）
            - 批量身份证识别（最多10张）
            - 自动检测证件类型和正反面
            - 支持快速模式（速度优先）
            
            **支持格式**：
            - 图像格式：JPG, PNG, BMP, TIFF
            - 传输方式：Base64编码或文件上传
            - 最大尺寸：10MB单张图片
            
            **识别精度**：
            - 标准模式：99%+ 准确率
            - 快速模式：95%+ 准确率，速度提升50%
            """
        },
        {
            "name": "系统",
            "description": """
            ### 系统管理接口
            
            **功能包括**：
            - 服务健康状态检查
            - 版本信息查询
            - 系统性能监控
            
            **监控指标**：
            - 服务运行状态
            - 接口响应时间
            - 系统资源使用
            - 错误统计信息
            """
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 自定义Swagger UI路由
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义Swagger UI页面"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{PROJECT_NAME} - API文档",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

# 自定义ReDoc路由
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """自定义ReDoc页面"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{PROJECT_NAME} - API文档",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

# 根路由
@app.get("/", tags=["系统"])
async def root():
    """根路由，返回服务信息"""
    return {
        "name": PROJECT_NAME,
        "version": VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"{PROJECT_NAME} v{VERSION} 服务启动")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info(f"{PROJECT_NAME} v{VERSION} 服务关闭")
