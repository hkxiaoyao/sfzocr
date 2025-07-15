#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

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
        description="身份证OCR识别服务API文档，提供身份证信息识别功能。",
        routes=app.routes,
    )
    
    # 自定义OpenAPI文档
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # 添加中文标签描述
    openapi_schema["tags"] = [
        {
            "name": "OCR",
            "description": "身份证OCR识别相关接口"
        },
        {
            "name": "系统",
            "description": "系统状态和健康检查接口"
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
