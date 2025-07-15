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
    健康检查API
    
    返回服务的健康状态信息
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
    身份证识别API
    
    接收身份证图片，识别并返回身份证信息
    
    - **image**: Base64编码的图片数据
    - **side**: 身份证正反面，可选值：front（正面）、back（背面）
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
        is_front = request.side == CardSide.FRONT
        result = await process_pool_manager.run_task(
            extract_id_card_info,
            request.image,
            is_front
        )
        
        # 检查结果是否为空
        if not result:
            logger.warning("未能识别到身份证信息")
            return {
                "code": ResponseCode.OCR_ERROR,
                "message": "未能识别到身份证信息",
                "data": None
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
    image: UploadFile = File(...),
    side: CardSide = Form(CardSide.FRONT),
    _: None = Depends(verify_api_key)
):
    """
    身份证识别API（文件上传版）
    
    通过文件上传方式接收身份证图片，识别并返回身份证信息
    
    - **image**: 上传的身份证图片文件
    - **side**: 身份证正反面，可选值：front（正面）、back（背面）
    """
    try:
        start_time = time.time()
        logger.info(f"接收到身份证识别文件上传请求，类型: {side}")
        
        # 读取上传的文件内容
        image_data = await image.read()
        
        # 转换为base64编码
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 使用进程池处理OCR任务
        is_front = side == CardSide.FRONT
        
        # 直接处理图像数据，避免序列化OCR引擎
        result = await process_pool_manager.run_task(
            extract_id_card_info,
            image_base64,
            is_front
        )
        
        # 检查结果是否为空
        if not result:
            logger.warning("未能识别到身份证信息")
            return {
                "code": ResponseCode.OCR_ERROR,
                "message": "未能识别到身份证信息",
                "data": None
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
    front_image: Optional[UploadFile] = File(None),
    back_image: Optional[UploadFile] = File(None),
    _: None = Depends(verify_api_key)
):
    """
    批量身份证识别API（文件上传版）
    
    通过文件上传方式接收身份证正反面图片，批量识别并返回身份证信息
    
    - **front_image**: 上传的身份证正面图片文件
    - **back_image**: 上传的身份证背面图片文件
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
                    task["is_front"]
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
    批量身份证识别API
    
    接收多张身份证图片，批量识别并返回身份证信息
    
    - **images**: 图像数据列表，每个元素包含image（Base64编码的图片数据）和side（身份证正反面）
    """
    try:
        start_time = time.time()
        image_count = len(request.images)
        logger.info(f"接收到批量身份证识别请求，图像数量: {image_count}")
        
        # 准备任务列表
        tasks = []
        for img_source in request.images:
            is_front = img_source.side == CardSide.FRONT
            tasks.append({
                "image_data": img_source.image,
                "is_front": is_front
            })
        
        # 定义处理函数
        async def process_single_image(task):
            try:
                return await process_pool_manager.run_task(
                    extract_id_card_info,
                    task["image_data"],
                    task["is_front"]
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
