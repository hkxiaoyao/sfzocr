#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator

class CardSide(str, Enum):
    """身份证正反面枚举"""
    FRONT = "front"
    BACK = "back"
    BOTH = "both"

class ImageSource(BaseModel):
    """图像数据源"""
    image: str = Field(..., description="Base64编码的图像数据")
    side: CardSide = Field(CardSide.FRONT, description="身份证正反面")

class IDCardRequest(BaseModel):
    """身份证识别请求"""
    image: str = Field(..., description="Base64编码的图像数据")
    side: CardSide = Field(CardSide.FRONT, description="身份证正反面")
    
    @validator('image')
    def validate_image(cls, v):
        """验证图像数据"""
        if not v:
            raise ValueError("图像数据不能为空")
        
        # 移除可能的base64前缀
        if "base64," in v:
            v = v.split("base64,")[1]
        
        return v

class IDCardFrontInfo(BaseModel):
    """身份证正面信息"""
    name: Optional[str] = Field(None, description="姓名")
    sex: Optional[str] = Field(None, description="性别")
    nation: Optional[str] = Field(None, description="民族")
    birth: Optional[str] = Field(None, description="出生日期")
    address: Optional[str] = Field(None, description="住址")
    id_number: Optional[str] = Field(None, description="身份证号码")

class IDCardBackInfo(BaseModel):
    """身份证背面信息"""
    issue_authority: Optional[str] = Field(None, description="签发机关")
    valid_period: Optional[str] = Field(None, description="有效期限")

class IDCardInfo(BaseModel):
    """身份证完整信息"""
    name: Optional[str] = Field(None, description="姓名")
    sex: Optional[str] = Field(None, description="性别")
    nation: Optional[str] = Field(None, description="民族")
    birth: Optional[str] = Field(None, description="出生日期")
    address: Optional[str] = Field(None, description="住址")
    id_number: Optional[str] = Field(None, description="身份证号码")
    issue_authority: Optional[str] = Field(None, description="签发机关")
    valid_period: Optional[str] = Field(None, description="有效期限")

class ResponseCode(int, Enum):
    """响应状态码"""
    SUCCESS = 0  # 成功
    PARAM_ERROR = 1001  # 参数错误
    IMAGE_ERROR = 1002  # 图像处理错误
    OCR_ERROR = 1003  # OCR识别错误
    SYSTEM_ERROR = 9999  # 系统错误

class BaseResponse(BaseModel):
    """基础响应模型"""
    code: ResponseCode = Field(ResponseCode.SUCCESS, description="状态码：0-成功，1001-参数错误，1002-图像处理错误，1003-OCR识别错误，9999-系统错误")
    message: str = Field("success", description="状态信息：成功或错误描述")

class IDCardResponse(BaseResponse):
    """身份证识别响应"""
    data: Optional[IDCardInfo] = Field(None, description="身份证信息，识别失败时为null")

class HealthResponse(BaseResponse):
    """健康检查响应"""
    data: Dict[str, Any] = Field({}, description="健康状态信息，包含服务状态、版本和时间戳")

class BatchIDCardRequest(BaseModel):
    """批量身份证识别请求"""
    images: List[ImageSource] = Field(..., description="图像数据列表，每项包含image和side")
    
    @validator('images')
    def validate_images(cls, v):
        """验证图像数据列表"""
        if not v:
            raise ValueError("图像数据列表不能为空")
        if len(v) > 10:
            raise ValueError("批量处理最多支持10张图像")
        return v

class BatchIDCardResponse(BaseResponse):
    """批量身份证识别响应"""
    data: List[Optional[IDCardInfo]] = Field([], description="身份证信息列表，识别失败的项为null")
    failed_indices: List[int] = Field([], description="处理失败的图像索引列表")

# 文件上传相关响应模型说明
"""
注意：对于文件上传API，我们不需要定义新的响应模型，因为它们与现有的响应模型相同：
- 单张身份证识别使用 IDCardResponse
- 批量身份证识别使用 BatchIDCardResponse

文件上传API的请求参数直接使用FastAPI的File和Form参数，不需要定义新的请求模型。
"""
