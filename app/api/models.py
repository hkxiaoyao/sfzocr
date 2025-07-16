#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator

class CardSide(str, Enum):
    """
    身份证证件类型枚举
    
    用于指定要识别的证件类型，支持自动检测和手动指定
    """
    FRONT = "front"           # 中国居民身份证正面（包含姓名、性别、民族等信息）
    BACK = "back"             # 中国居民身份证背面（包含签发机关、有效期限）
    BOTH = "both"             # 正反面（仅批量接口支持）
    # 外国人永久居留身份证类型
    FOREIGN_NEW = "foreign_new"  # 新版外国人永久居留身份证（2017年后发放）
    FOREIGN_OLD = "foreign_old"  # 旧版外国人永久居留身份证（2017年前发放）
    # 自动检测（推荐）
    AUTO = "auto"             # 智能自动检测证件类型和正反面

class ImageSource(BaseModel):
    """
    图像数据源模型
    
    用于批量识别时指定单张图片的参数
    """
    image: str = Field(
        ..., 
        description="Base64编码的图像数据（去除data:image/...;base64,前缀）",
        example="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk..."
    )
    side: CardSide = Field(
        CardSide.AUTO, 
        description="证件类型，推荐使用auto自动检测",
        example="auto"
    )
    fast_mode: bool = Field(
        False, 
        description="快速模式：启用后识别速度提升约50%，准确率略微下降（99%→95%）",
        example=False
    )

class IDCardRequest(BaseModel):
    """
    身份证识别请求模型
    
    用于单张身份证识别的完整请求参数
    """
    image: str = Field(
        ..., 
        description="Base64编码的图像数据，支持JPG/PNG/BMP/TIFF格式，最大10MB",
        example="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk..."
    )
    side: CardSide = Field(
        CardSide.AUTO, 
        description="证件类型：推荐使用auto让系统自动检测证件类型和正反面",
        example="auto"
    )
    debug: bool = Field(
        False, 
        description="""调试模式：
        • false（默认）：返回结构化的身份证信息
        • true：返回原始OCR识别文本，用于问题诊断和算法调优
        注意：调试模式下返回格式与正常模式不同""",
        example=False
    )
    fast_mode: bool = Field(
        False, 
        description="""快速模式（v0.1.4新增）：
        • false（默认）：标准模式，99%+准确率，识别时间2-3秒
        • true：快速模式，95%+准确率，识别时间1-1.5秒
        推荐场景：实时预览、大批量处理、对速度要求较高的场景""",
        example=False
    )
    
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

class ForeignIDCardInfo(BaseModel):
    """外国人永久居留身份证信息"""
    chinese_name: Optional[str] = Field(None, description="中文姓名")
    english_name: Optional[str] = Field(None, description="英文姓名")
    sex: Optional[str] = Field(None, description="性别")
    birth_date: Optional[str] = Field(None, description="出生日期")
    nationality: Optional[str] = Field(None, description="国籍")
    residence_number: Optional[str] = Field(None, description="永久居留证号码")
    issue_authority: Optional[str] = Field(None, description="签发机关")
    issue_date: Optional[str] = Field(None, description="签发日期")
    valid_until: Optional[str] = Field(None, description="有效期限")
    card_type: Optional[str] = Field(None, description="证件类型（新版/旧版）")

class IDCardInfo(BaseModel):
    """
    身份证完整信息统一返回模型
    
    支持中国居民身份证和外国人永久居留身份证的所有字段
    根据证件类型返回相应字段，未识别字段为null
    """
    # 中国居民身份证字段
    name: Optional[str] = Field(None, description="姓名", example="张三")
    sex: Optional[str] = Field(None, description="性别", example="男")
    nation: Optional[str] = Field(None, description="民族", example="汉")
    birth: Optional[str] = Field(None, description="出生日期", example="1990年1月1日")
    address: Optional[str] = Field(None, description="住址", example="北京市海淀区中关村街道...")
    id_number: Optional[str] = Field(None, description="身份证号码", example="110101199001011234")
    issue_authority: Optional[str] = Field(None, description="签发机关", example="北京市公安局海淀分局")
    valid_period: Optional[str] = Field(None, description="有效期限", example="2020.01.01-2030.01.01")
    
    # 外国人永久居留身份证字段
    chinese_name: Optional[str] = Field(None, description="中文姓名", example="李明")
    english_name: Optional[str] = Field(None, description="英文姓名", example="JOHN SMITH")
    birth_date: Optional[str] = Field(None, description="出生日期", example="1985-05-15")
    nationality: Optional[str] = Field(None, description="国籍", example="美国")
    residence_number: Optional[str] = Field(None, description="永久居留证号码", example="210101198505151234")
    issue_date: Optional[str] = Field(None, description="签发日期", example="2020-01-01")
    valid_until: Optional[str] = Field(None, description="有效期限", example="2030-01-01")
    card_type: Optional[str] = Field(None, description="证件类型", example="新版外国人永久居留身份证")

class ResponseCode(int, Enum):
    """
    API响应状态码枚举
    
    用于标识API请求的处理结果状态
    """
    SUCCESS = 0       # 成功：请求处理成功，识别完成
    PARAM_ERROR = 1001    # 参数错误：请求参数不正确或缺失
    IMAGE_ERROR = 1002    # 图像错误：图像格式不支持或损坏
    OCR_ERROR = 1003      # 识别错误：OCR引擎无法识别图像内容
    SYSTEM_ERROR = 9999   # 系统错误：服务器内部错误或资源不足

class BaseResponse(BaseModel):
    """
    API基础响应模型
    
    所有API响应的基础结构，包含状态码和消息
    """
    code: ResponseCode = Field(
        ResponseCode.SUCCESS, 
        description="响应状态码",
        example=0
    )
    message: str = Field(
        "success", 
        description="响应消息，成功时为'success'，失败时为具体错误信息",
        example="识别成功"
    )

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

外国人永久居留身份证识别：
- 新版外国人永久居留身份证：side = "foreign_new"
- 旧版外国人永久居留身份证：side = "foreign_old"
- 统一使用 IDCardResponse 返回结果，通过 card_type 字段区分证件类型
"""
