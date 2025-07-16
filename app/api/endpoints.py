#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import asyncio
import base64
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, UploadFile, File, Form

from app.api.models import (
    IDCardRequest, IDCardResponse, BatchIDCardRequest, BatchIDCardResponse,
    HealthResponse, ResponseCode, IDCardInfo, CardSide
)
from app.core.ocr_engine import extract_id_card_info
from app.utils.concurrency import process_pool_manager, run_batch_tasks
from app.utils.logger import get_logger
from app.config import API_KEY_HEADER, API_KEYS, VERSION

# 获取logger
logger = get_logger("api")

# 创建路由
router = APIRouter()

# API密钥验证
async def verify_api_key(request: Request, api_key: Optional[str] = Header(None, alias=API_KEY_HEADER)):
    """
    验证API密钥
    
    Args:
        request: 请求对象
        api_key: API密钥
    
    Raises:
        HTTPException: 验证失败时抛出
    """
    # 如果未配置API密钥，则不进行验证
    if not API_KEYS:
        return
    
    # 验证API密钥
    if not api_key or api_key not in API_KEYS:
        logger.warning(f"API密钥验证失败: {api_key}")
        raise HTTPException(status_code=401, detail="无效的API密钥")

# 健康检查端点
@router.get("/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """
    ## 服务健康检查API
    
    **功能说明**：
    - 检查服务运行状态
    - 返回版本信息
    - 提供时间戳用于监控
    
    **返回信息**：
    - `status`: 服务状态（healthy/unhealthy）
    - `version`: 服务版本号
    - `timestamp`: 当前时间戳
    
    **使用场景**：
    - 负载均衡器健康检查
    - 监控系统状态探测
    - 服务可用性验证
    
    **响应示例**：
    ```json
    {
        "code": 0,
        "message": "服务正常",
        "data": {
            "status": "healthy",
            "version": "0.1.4",
            "timestamp": 1752646627
        }
    }
    ```
    """
    return {
        "code": ResponseCode.SUCCESS,
        "message": "服务正常",
        "data": {
            "status": "healthy",
            "version": VERSION,
            "timestamp": int(time.time())
        }
    }

# 身份证识别端点
@router.post("/ocr/idcard", response_model=IDCardResponse, tags=["OCR"])
async def recognize_id_card(
    request: IDCardRequest,
    _: None = Depends(verify_api_key)
):
    """
    ## 身份证OCR识别API（JSON方式）
    
    **功能说明**：
    - 识别各类身份证信息
    - 支持自动检测证件类型
    - 提供调试模式和快速模式
    
    **支持的证件类型**：
    - `front`: 中国身份证正面
    - `back`: 中国身份证背面  
    - `foreign_new`: 新版外国人永久居留身份证
    - `foreign_old`: 旧版外国人永久居留身份证
    - `auto`: 自动检测（推荐）
    
    **参数详细说明**：
    
    📷 **image** (必需)
    - 类型：string (Base64编码)
    - 格式：JPG、PNG、BMP、TIFF
    - 大小：≤10MB
    - 示例：`"iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB..."`
    
    🏷️ **side** (可选，默认：auto)
    - `auto`: 智能检测（推荐）🔥
    - `front`: 中国身份证正面
    - `back`: 中国身份证背面
    - `foreign_new`: 新版外国人永久居留证
    - `foreign_old`: 旧版外国人永久居留证
    
    🐛 **debug** (可选，默认：false)
    - `false`: 返回结构化数据（生产环境）
    - `true`: 返回原始OCR文本（调试诊断）
    - 调试示例返回：`{"ocr_text": ["姓名 张三", "性别 男", ...]}`
    
    ⚡ **fast_mode** (可选，默认：false)
    - `false`: 标准模式（99%准确率，2-3秒）
    - `true`: 快速模式（95%准确率，1-1.5秒）
    - 适用场景：实时预览、批量处理、高并发
    
    **图片要求**：
    - 格式：JPG、PNG、BMP、TIFF
    - 大小：≤10MB
    - 分辨率：建议≥300DPI
    - 光照：充足、均匀，避免反光
    
    **返回字段**：
    - **中国身份证**：姓名、性别、民族、出生、住址、身份证号、签发机关、有效期限
    - **外国人永久居留证**：中英文姓名、性别、出生日期、国籍、证件号码、签发信息等
    
    **请求示例**：
    ```json
    {
        "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB...",
        "side": "auto",
        "debug": false,
        "fast_mode": false
    }
    ```
    
    **标准模式响应**：
    ```json
    {
        "code": 0,
        "message": "识别成功",
        "data": {
            "name": "张三",
            "sex": "男",
            "nation": "汉",
            "birth": "1990年1月1日",
            "address": "北京市海淀区...",
            "id_number": "110101199001011234"
        }
    }
    ```
    
    **调试模式响应** (debug=true)：
    ```json
    {
        "code": 0,
        "message": "识别成功(DEBUG模式)",
        "data": {
            "ocr_text": [
                "姓名 张三",
                "性别 男", 
                "民族 汉",
                "出生 1990年01月01日",
                "住址 北京市海淀区中关村街道...",
                "公民身份号码 110101199001011234"
            ]
        }
    }
    ```
    """
    try:
        start_time = time.time()
        logger.info(f"接收到身份证识别请求，类型: {request.side}")
        
        # 根据请求类型处理不同的识别逻辑
        if request.side == CardSide.BOTH:
            # 如果是双面识别，需要分别处理正反面
            logger.error("双面识别需要使用批量接口，提供正反面图像")
            return {
                "code": ResponseCode.PARAM_ERROR,
                "message": "双面识别需要使用批量接口，提供正反面图像",
                "data": None
            }
        
        # 使用进程池处理OCR任务
        # 根据证件类型确定参数
        if request.side == CardSide.AUTO:
            # 自动检测模式
            result = await process_pool_manager.run_task(
                extract_id_card_info,
                request.image,
                True,  # 默认值，自动检测会覆盖
                "auto",
                request.debug,
                request.fast_mode  # v0.1.4新增快速模式
            )
        elif request.side in [CardSide.FOREIGN_NEW, CardSide.FOREIGN_OLD]:
            # 外国人永久居留身份证
            card_type = "foreign_new" if request.side == CardSide.FOREIGN_NEW else "foreign_old"
            result = await process_pool_manager.run_task(
                extract_id_card_info,
                request.image,
                True,  # is_front参数对外国人永久居留身份证无意义，但需要传递
                card_type,
                request.debug,
                request.fast_mode  # v0.1.4新增快速模式
            )
        else:
            # 中国居民身份证
            is_front = request.side == CardSide.FRONT
            result = await process_pool_manager.run_task(
                extract_id_card_info,
                request.image,
                is_front,
                "chinese",
                request.debug,
                request.fast_mode  # v0.1.4新增快速模式
            )
        
        # 检查结果是否为空
        if not result:
            logger.warning("未能识别到身份证信息")
            return {
                "code": ResponseCode.OCR_ERROR,
                "message": "未能识别到身份证信息",
                "data": None
            }
        
        # Debug模式：直接返回OCR文本
        logger.info(f"Debug检查: debug={request.debug}, result keys={list(result.keys()) if result else 'None'}")
        if request.debug and result and "ocr_text" in result:
            execution_time = time.time() - start_time
            logger.info(f"身份证识别(DEBUG模式)完成，耗时: {execution_time:.2f}秒")
            return {
                "code": ResponseCode.SUCCESS,
                "message": "识别成功(DEBUG模式)",
                "data": result
            }
        
        # 构造响应
        id_card_info = IDCardInfo(**result)
        
        execution_time = time.time() - start_time
        logger.info(f"身份证识别完成，耗时: {execution_time:.2f}秒")
        
        return {
            "code": ResponseCode.SUCCESS,
            "message": "识别成功",
            "data": id_card_info
        }
        
    except ValueError as e:
        logger.error(f"图像处理错误: {str(e)}")
        return {
            "code": ResponseCode.IMAGE_ERROR,
            "message": str(e),
            "data": None
        }
        
    except Exception as e:
        logger.error(f"身份证识别异常: {str(e)}")
        return {
            "code": ResponseCode.SYSTEM_ERROR,
            "message": f"系统错误: {str(e)}",
            "data": None
        }

# 文件上传身份证识别端点
@router.post("/ocr/idcard/upload", response_model=IDCardResponse, tags=["OCR"])
async def recognize_id_card_upload(
    image: UploadFile = File(..., description="身份证图片文件"),
    side: CardSide = Form(CardSide.AUTO, description="证件类型（auto=自动检测）"),
    debug: bool = Form(False, description="调试模式"),
    fast_mode: bool = Form(False, description="快速模式"),
    _: None = Depends(verify_api_key)
):
    """
    ## 身份证OCR识别API（文件上传版）
    
    **功能说明**：
    - 通过文件上传方式识别身份证
    - 更适合前端应用集成
    - 支持多种图片格式
    
    **参数详细说明**：
    
    📁 **image** (必需)
    - 类型：multipart/form-data文件
    - 格式：JPG、JPEG、PNG、BMP、TIFF
    - 大小：≤10MB
    - 质量：建议≥300DPI，清晰无模糊
    
    🏷️ **side** (可选，默认：auto)
    - 同JSON版本，支持auto智能检测
    - 建议：除非明确知道证件类型，否则使用auto
    
    🐛 **debug** (可选，默认：false)
    - 用法与JSON版本相同
    - 开发阶段建议启用，便于问题排查
    
    ⚡ **fast_mode** (可选，默认：false)
    - 适合：网页实时预览、移动端快速响应
    - 不适合：金融级认证、法律文档处理
    
    **上传要求**：
    - 文件格式：JPG、JPEG、PNG、BMP、TIFF
    - 文件大小：≤10MB
    - 图片质量：清晰、完整、正置
    
    **与JSON版本区别**：
    - ✅ 更方便的文件上传
    - ✅ 支持前端表单提交
    - ✅ 无需Base64编码
    - ❌ 稍高的传输开销
    
    **适用场景**：
    - 网页表单上传
    - 移动应用拍照识别
    - 批量文件处理工具
    
    **cURL示例**：
    ```bash
    curl -X POST "http://localhost:8000/api/v1/ocr/idcard/upload" \\
         -F "image=@idcard.jpg" \\
         -F "side=auto" \\
         -F "fast_mode=false"
    ```
    """
    try:
        start_time = time.time()
        logger.info(f"接收到身份证识别文件上传请求，类型: {side}")
        
        # 读取上传的文件内容
        image_data = await image.read()
        
        # 转换为base64编码
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 使用进程池处理OCR任务
        # 根据证件类型确定参数
        if side == CardSide.AUTO:
            # 自动检测模式
            result = await process_pool_manager.run_task(
                extract_id_card_info,
                image_base64,
                True,  # 默认值，自动检测会覆盖
                "auto",
                debug,
                fast_mode  # v0.1.4新增快速模式
            )
        elif side in [CardSide.FOREIGN_NEW, CardSide.FOREIGN_OLD]:
            # 外国人永久居留身份证
            card_type = "foreign_new" if side == CardSide.FOREIGN_NEW else "foreign_old"
            result = await process_pool_manager.run_task(
                extract_id_card_info,
                image_base64,
                True,  # is_front参数对外国人永久居留身份证无意义，但需要传递
                card_type,
                debug,
                fast_mode  # v0.1.4新增快速模式
            )
        else:
            # 中国居民身份证
            is_front = side == CardSide.FRONT
            # 直接处理图像数据，避免序列化OCR引擎
            result = await process_pool_manager.run_task(
                extract_id_card_info,
                image_base64,
                is_front,
                "chinese",
                debug,
                fast_mode  # v0.1.4新增快速模式
            )
        
        # 检查结果是否为空
        if not result:
            logger.warning("未能识别到身份证信息")
            return {
                "code": ResponseCode.OCR_ERROR,
                "message": "未能识别到身份证信息",
                "data": None
            }
        
        # Debug模式：直接返回OCR文本
        logger.info(f"Debug检查: debug={debug}, result keys={list(result.keys()) if result else 'None'}")
        if debug and result and "ocr_text" in result:
            execution_time = time.time() - start_time
            logger.info(f"身份证识别(DEBUG模式)完成，耗时: {execution_time:.2f}秒")
            return {
                "code": ResponseCode.SUCCESS,
                "message": "识别成功(DEBUG模式)",
                "data": result
            }
        
        # 构造响应
        id_card_info = IDCardInfo(**result)
        
        execution_time = time.time() - start_time
        logger.info(f"身份证识别完成，耗时: {execution_time:.2f}秒")
        
        return {
            "code": ResponseCode.SUCCESS,
            "message": "识别成功",
            "data": id_card_info
        }
        
    except ValueError as e:
        logger.error(f"图像处理错误: {str(e)}")
        return {
            "code": ResponseCode.IMAGE_ERROR,
            "message": str(e),
            "data": None
        }
        
    except Exception as e:
        logger.error(f"身份证识别异常: {str(e)}")
        return {
            "code": ResponseCode.SYSTEM_ERROR,
            "message": f"系统错误: {str(e)}",
            "data": None
        }

# 批量文件上传身份证识别端点
@router.post("/ocr/idcard/batch/upload", response_model=BatchIDCardResponse, tags=["OCR"])
async def batch_recognize_id_card_upload(
    front_image: Optional[UploadFile] = File(None, description="身份证正面图片文件"),
    back_image: Optional[UploadFile] = File(None, description="身份证背面图片文件"),
    fast_mode: bool = Form(False, description="快速模式"),
    _: None = Depends(verify_api_key)
):
    """
    ## 批量身份证识别API（文件上传版）
    
    **功能说明**：
    - 同时上传身份证正反面
    - 自动匹配正反面信息
    - 返回完整身份证信息
    
    **参数说明**：
    - `front_image`: 身份证正面图片（可选）
    - `back_image`: 身份证背面图片（可选）
    - `fast_mode`: 快速模式（可选，默认false）
    
    **上传要求**：
    - 至少上传一张图片（正面或背面）
    - 建议同时上传正反面获得完整信息
    - 支持格式：JPG、PNG、BMP、TIFF
    - 单文件大小：≤10MB
    
    **典型使用场景**：
    - 用户注册时上传身份证正反面
    - 实名认证完整信息收集
    - 金融开户身份验证
    
    **返回结果**：
    - 包含所有上传图片的识别结果
    - 正面信息：姓名、性别、民族、出生、住址、身份证号
    - 背面信息：签发机关、有效期限
    
    **HTML表单示例**：
    ```html
    <form action="/api/v1/ocr/idcard/batch/upload" 
          method="post" enctype="multipart/form-data">
        <input type="file" name="front_image" accept="image/*">
        <input type="file" name="back_image" accept="image/*">
        <input type="checkbox" name="fast_mode" value="true">
        <button type="submit">识别身份证</button>
    </form>
    ```
    
    **cURL示例**：
    ```bash
    curl -X POST "http://localhost:8000/api/v1/ocr/idcard/batch/upload" \\
         -F "front_image=@front.jpg" \\
         -F "back_image=@back.jpg" \\
         -F "fast_mode=false"
    ```
    """
    try:
        start_time = time.time()
        
        # 检查至少上传了一张图片
        if not front_image and not back_image:
            logger.error("未提供任何身份证图片")
            return {
                "code": ResponseCode.PARAM_ERROR,
                "message": "请至少上传一张身份证图片",
                "data": [],
                "failed_indices": []
            }
        
        logger.info(f"接收到批量身份证识别文件上传请求，正面: {bool(front_image)}，背面: {bool(back_image)}")
        
        # 准备任务列表
        tasks = []
        
        # 处理正面图片
        if front_image:
            front_data = await front_image.read()
            front_base64 = base64.b64encode(front_data).decode('utf-8')
            tasks.append({
                "image_data": front_base64,
                "is_front": True
            })
        
        # 处理背面图片
        if back_image:
            back_data = await back_image.read()
            back_base64 = base64.b64encode(back_data).decode('utf-8')
            tasks.append({
                "image_data": back_base64,
                "is_front": False
            })
        
        # 定义处理函数
        async def process_single_image(task):
            try:
                return await process_pool_manager.run_task(
                    extract_id_card_info,
                    task["image_data"],
                    task["is_front"],
                    "chinese",  # 固定为中国身份证
                    False,      # debug=False
                    fast_mode   # v0.1.4新增快速模式
                )
            except Exception as e:
                logger.error(f"处理单张图像失败: {str(e)}")
                return None
        
        # 并发处理所有图像
        results = await asyncio.gather(*[process_single_image(task) for task in tasks])
        
        # 处理结果
        id_card_infos = []
        failed_indices = []
        
        for i, result in enumerate(results):
            if result and any(result.values()):
                id_card_infos.append(IDCardInfo(**result))
            else:
                id_card_infos.append(None)
                failed_indices.append(i)
        
        # 统计结果
        image_count = len(tasks)
        success_count = image_count - len(failed_indices)
        execution_time = time.time() - start_time
        logger.info(f"批量身份证识别完成，成功: {success_count}/{image_count}，耗时: {execution_time:.2f}秒")
        
        # 构造响应
        return {
            "code": ResponseCode.SUCCESS,
            "message": f"处理完成，成功: {success_count}/{image_count}",
            "data": id_card_infos,
            "failed_indices": failed_indices
        }
        
    except ValueError as e:
        logger.error(f"批量处理参数错误: {str(e)}")
        return {
            "code": ResponseCode.PARAM_ERROR,
            "message": str(e),
            "data": [],
            "failed_indices": []
        }
        
    except Exception as e:
        logger.error(f"批量身份证识别异常: {str(e)}")
        return {
            "code": ResponseCode.SYSTEM_ERROR,
            "message": f"系统错误: {str(e)}",
            "data": [],
            "failed_indices": []
        }

# 批量身份证识别端点
@router.post("/ocr/idcard/batch", response_model=BatchIDCardResponse, tags=["OCR"])
async def batch_recognize_id_card(
    request: BatchIDCardRequest,
    _: None = Depends(verify_api_key)
):
    """
    ## 批量身份证识别API（JSON方式）
    
    **功能说明**：
    - 一次请求处理多张身份证
    - 并发处理，提高效率
    - 支持混合证件类型
    
    **处理能力**：
    - 最多支持10张图片
    - 并发处理，响应更快
    - 失败图片不影响其他图片处理
    
    **请求格式**：
    ```json
    {
        "images": [
            {
                "image": "base64_encoded_image_data",
                "side": "auto",
                "fast_mode": false
            },
            {
                "image": "base64_encoded_image_data", 
                "side": "front",
                "fast_mode": true
            }
        ]
    }
    ```
    
    **返回结果**：
    - `data`: 识别结果数组，失败项为null
    - `failed_indices`: 处理失败的图片索引列表
    
    **性能优势**：
    - 🚀 并发处理，比逐个调用快3-5倍
    - 💾 复用连接，减少网络开销
    - 🔄 部分失败不影响整体结果
    
    **使用建议**：
    - 身份证正反面一起处理
    - 大批量文档处理场景
    - 提高用户体验的快速响应
    
    **限制说明**：
    - 单次最多10张图片
    - 总数据量建议≤50MB
    - 超时时间较长（300秒）
    """
    try:
        start_time = time.time()
        image_count = len(request.images)
        logger.info(f"接收到批量身份证识别请求，图像数量: {image_count}")
        
        # 准备任务列表
        tasks = []
        for img_source in request.images:
            if img_source.side == CardSide.AUTO:
                # 自动检测模式
                tasks.append({
                    "image_data": img_source.image,
                    "is_front": True,  # 默认值，自动检测会覆盖
                    "card_type": "auto",
                    "fast_mode": img_source.fast_mode  # v0.1.4新增
                })
            elif img_source.side in [CardSide.FOREIGN_NEW, CardSide.FOREIGN_OLD]:
                # 外国人永久居留身份证
                card_type = "foreign_new" if img_source.side == CardSide.FOREIGN_NEW else "foreign_old"
                tasks.append({
                    "image_data": img_source.image,
                    "is_front": True,  # 对外国人永久居留身份证无意义，但需要传递
                    "card_type": card_type,
                    "fast_mode": img_source.fast_mode  # v0.1.4新增
                })
            else:
                # 中国居民身份证
                is_front = img_source.side == CardSide.FRONT
                tasks.append({
                    "image_data": img_source.image,
                    "is_front": is_front,
                    "card_type": "chinese",
                    "fast_mode": img_source.fast_mode  # v0.1.4新增
                })
        
        # 定义处理函数
        async def process_single_image(task):
            try:
                return await process_pool_manager.run_task(
                    extract_id_card_info,
                    task["image_data"],
                    task["is_front"],
                    task["card_type"],
                    False,  # debug=False
                    task["fast_mode"]  # v0.1.4新增快速模式
                )
            except Exception as e:
                logger.error(f"处理单张图像失败: {str(e)}")
                return None
        
        # 并发处理所有图像
        results = await asyncio.gather(*[process_single_image(task) for task in tasks])
        
        # 处理结果
        id_card_infos = []
        failed_indices = []
        
        for i, result in enumerate(results):
            if result and any(result.values()):
                id_card_infos.append(IDCardInfo(**result))
            else:
                id_card_infos.append(None)
                failed_indices.append(i)
        
        # 统计结果
        success_count = image_count - len(failed_indices)
        execution_time = time.time() - start_time
        logger.info(f"批量身份证识别完成，成功: {success_count}/{image_count}，耗时: {execution_time:.2f}秒")
        
        # 构造响应
        return {
            "code": ResponseCode.SUCCESS,
            "message": f"处理完成，成功: {success_count}/{image_count}",
            "data": id_card_infos,
            "failed_indices": failed_indices
        }
        
    except ValueError as e:
        logger.error(f"批量处理参数错误: {str(e)}")
        return {
            "code": ResponseCode.PARAM_ERROR,
            "message": str(e),
            "data": [],
            "failed_indices": []
        }
        
    except Exception as e:
        logger.error(f"批量身份证识别异常: {str(e)}")
        return {
            "code": ResponseCode.SYSTEM_ERROR,
            "message": f"系统错误: {str(e)}",
            "data": [],
            "failed_indices": []
        }
