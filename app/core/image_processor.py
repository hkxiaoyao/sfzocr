#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import base64
import io
import cv2
import numpy as np
from typing import Tuple, Optional, Union, Dict, Any
from PIL import Image
import time

from app.utils.logger import get_logger

# 获取logger
logger = get_logger("image_processor")

# 导入性能配置 - v0.1.4新增
try:
    from app.config import OCR_PERFORMANCE_CONFIG
except ImportError:
    # 兼容性处理
    OCR_PERFORMANCE_CONFIG = {
        "max_image_size": 1600,
        "resize_quality": 85,
        "enable_fast_mode": False,
        "enable_memory_optimization": True,
    }

class ImageProcessor:
    """图像处理类，用于身份证图像的预处理"""
    
    @staticmethod
    def decode_image(image_data: Union[str, bytes]) -> np.ndarray:
        """
        解码图像数据
        
        Args:
            image_data: base64编码的图像数据或二进制图像数据
            
        Returns:
            解码后的图像数组
            
        Raises:
            ValueError: 图像数据无效
        """
        try:
            # 如果是base64字符串
            if isinstance(image_data, str):
                # 移除可能的base64前缀
                if "base64," in image_data:
                    image_data = image_data.split("base64,")[1]
                
                # 解码base64数据
                image_bytes = base64.b64decode(image_data)
            else:
                # 已经是二进制数据
                image_bytes = image_data
            
            # 将二进制数据转换为numpy数组
            nparr = np.frombuffer(image_bytes, np.uint8)
            # 解码图像
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("无法解码图像数据")
                
            return image
            
        except Exception as e:
            logger.error(f"图像解码失败: {str(e)}")
            raise ValueError(f"图像解码失败: {str(e)}")
    
    @staticmethod
    def encode_image_to_base64(image: np.ndarray, format: str = "JPEG") -> str:
        """
        将图像编码为base64字符串
        
        Args:
            image: 图像数组
            format: 图像格式，默认为JPEG
            
        Returns:
            base64编码的图像字符串
        """
        # 转换为PIL图像
        if image.shape[2] == 3:
            # OpenCV的BGR转为RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
        else:
            pil_image = Image.fromarray(image)
        
        # 保存到内存缓冲区
        buffer = io.BytesIO()
        pil_image.save(buffer, format=format)
        
        # 转换为base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return img_base64
    
    @staticmethod
    def resize_image(image: np.ndarray, max_size: int = 1200) -> np.ndarray:
        """
        调整图像大小，保持宽高比
        
        Args:
            image: 原始图像
            max_size: 最大尺寸
            
        Returns:
            调整大小后的图像
        """
        height, width = image.shape[:2]
        
        # 如果图像尺寸已经小于最大尺寸，则不需要调整
        if max(height, width) <= max_size:
            return image
        
        # 计算缩放比例
        if height > width:
            scale = max_size / height
        else:
            scale = max_size / width
        
        # 调整大小
        new_width = int(width * scale)
        new_height = int(height * scale)
        resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return resized_image
    
    @staticmethod
    def enhance_image(image: np.ndarray) -> np.ndarray:
        """
        增强图像质量，提高OCR识别率
        
        Args:
            image: 原始图像
            
        Returns:
            增强后的图像
        """
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 自适应直方图均衡化
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # 降噪
        enhanced = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        
        # 转回彩色图像
        enhanced_color = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return enhanced_color
    
    @staticmethod
    def enhance_image_fast(image: np.ndarray) -> np.ndarray:
        """
        快速图像增强，简化版本以提高性能
        
        Args:
            image: 原始图像
            
        Returns:
            增强后的图像
        """
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 简单的对比度增强
        enhanced = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
        
        # 转回彩色图像
        enhanced_color = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return enhanced_color
    
    @staticmethod
    def detect_id_card(image: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        检测并裁剪身份证区域
        
        Args:
            image: 原始图像
            
        Returns:
            裁剪后的身份证图像和是否成功检测到身份证的标志
        """
        try:
            # 保存原始图像尺寸，用于日志记录
            original_height, original_width = image.shape[:2]
            logger.info(f"开始检测身份证轮廓，原始图像尺寸: {original_width}x{original_height}")
            
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 高斯模糊 - 调整核大小和标准差
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            
            # 自适应二值化 - 添加这一步以提高轮廓检测效果
            binary = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # 形态学操作 - 闭操作，填充小孔
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 边缘检测 - 调整阈值
            edges = cv2.Canny(binary, 50, 150)
            
            # 再次进行形态学操作，连接断开的边缘
            edges = cv2.dilate(edges, kernel, iterations=1)
            
            # 查找轮廓 - 使用RETR_LIST以获取所有轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            # 如果没有找到轮廓，返回原图
            if not contours:
                logger.warning("未检测到任何轮廓")
                return image, False
            
            logger.info(f"检测到 {len(contours)} 个轮廓")
            
            # 按轮廓面积排序
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            
            # 遍历最大的几个轮廓
            for i, contour in enumerate(contours[:10]):  # 增加检查的轮廓数量
                # 计算轮廓面积
                area = cv2.contourArea(contour)
                
                # 计算轮廓近似
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                
                # 记录轮廓信息
                logger.debug(f"轮廓 #{i+1}: 面积={area}, 点数={len(approx)}")
                
                # 放宽条件：如果近似轮廓有4个点或接近4个点(3-5)，可能是身份证
                if 3 <= len(approx) <= 5:
                    # 计算轮廓面积与图像面积的比例
                    area_ratio = area / (image.shape[0] * image.shape[1])
                    
                    # 放宽面积比例限制
                    if area_ratio < 0.1:  # 原来是0.2
                        logger.debug(f"轮廓 #{i+1} 面积比例过小: {area_ratio:.3f}")
                        continue
                    
                    # 获取最小外接矩形
                    rect = cv2.minAreaRect(contour)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    
                    # 计算矩形的宽高比
                    width = rect[1][0]
                    height = rect[1][1]
                    aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 0
                    
                    # 身份证的宽高比应该在1.5到2.0之间
                    if not (1.4 <= aspect_ratio <= 2.1):
                        logger.debug(f"轮廓 #{i+1} 宽高比不符合要求: {aspect_ratio:.2f}")
                        continue
                    
                    # 获取矩形区域
                    x, y, w, h = cv2.boundingRect(approx)
                    
                    # 确保裁剪区域不超出图像边界
                    x = max(0, x)
                    y = max(0, y)
                    w = min(w, image.shape[1] - x)
                    h = min(h, image.shape[0] - y)
                    
                    # 裁剪图像
                    card_image = image[y:y+h, x:x+w]
                    
                    logger.info(f"成功检测到身份证，轮廓 #{i+1}, 面积比例: {area_ratio:.3f}, 宽高比: {aspect_ratio:.2f}")
                    return card_image, True
            
            # 如果没有找到合适的矩形，尝试使用最大轮廓
            if contours:
                largest_contour = contours[0]
                x, y, w, h = cv2.boundingRect(largest_contour)
                area_ratio = cv2.contourArea(largest_contour) / (image.shape[0] * image.shape[1])
                
                # 如果最大轮廓面积比例足够大，可能是身份证
                if area_ratio > 0.3:
                    card_image = image[y:y+h, x:x+w]
                    logger.info(f"使用最大轮廓作为身份证，面积比例: {area_ratio:.3f}")
                    return card_image, True
            
            # 如果没有找到合适的矩形，返回原图
            logger.warning("未检测到合适的身份证轮廓，返回原图")
            return image, False
            
        except Exception as e:
            logger.error(f"身份证检测失败: {str(e)}")
            return image, False
    
    @staticmethod
    def correct_skew(image: np.ndarray) -> np.ndarray:
        """
        校正图像倾斜
        
        Args:
            image: 原始图像
            
        Returns:
            校正后的图像
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 二值化
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # 查找轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            # 计算轮廓的最小外接矩形
            angles = []
            for contour in contours:
                if cv2.contourArea(contour) < 100:  # 忽略小轮廓
                    continue
                    
                rect = cv2.minAreaRect(contour)
                angle = rect[2]
                
                # 将角度标准化到[-45, 45]
                if angle < -45:
                    angle = 90 + angle
                elif angle > 45:
                    angle = angle - 90
                    
                angles.append(angle)
            
            # 如果没有找到有效角度，返回原图
            if not angles:
                return image
                
            # 计算中位数角度
            median_angle = np.median(angles)
            
            # 如果角度太小，不需要校正
            if abs(median_angle) < 1:
                return image
                
            # 获取图像中心点
            h, w = image.shape[:2]
            center = (w // 2, h // 2)
            
            # 计算旋转矩阵
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            
            # 执行旋转
            rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, 
                                    borderMode=cv2.BORDER_REPLICATE)
            
            logger.info(f"图像校正完成，校正角度: {median_angle:.2f}度")
            return rotated
            
        except Exception as e:
            logger.error(f"图像校正失败: {str(e)}")
            return image
    
    @classmethod
    def preprocess_id_card_image_fast(cls, image_data: Union[str, bytes]) -> np.ndarray:
        """
        身份证图像快速预处理流程 - v0.1.4性能优化版本
        
        Args:
            image_data: base64编码的图像数据或二进制图像数据
            
        Returns:
            预处理后的图像
        """
        try:
            start_time = time.time()
            
            # 解码图像
            image = cls.decode_image(image_data)
            original_size = image.shape[1] * image.shape[0]
            
            # 🚀 性能优化：智能尺寸调整
            max_size = OCR_PERFORMANCE_CONFIG["max_image_size"]
            
            # 如果启用快速模式，进一步降低尺寸限制
            if OCR_PERFORMANCE_CONFIG["enable_fast_mode"]:
                max_size = min(max_size, 1200)  # 快速模式下最大1200像素
            
            # 调整图像大小
            if max(image.shape[:2]) > max_size:
                image = cls.resize_image(image, max_size=max_size)
                logger.debug(f"图像尺寸优化：{original_size//1000}K -> {(image.shape[1]*image.shape[0])//1000}K 像素")
            
            # 🏃‍♂️ 快速模式：跳过复杂的图像增强
            if OCR_PERFORMANCE_CONFIG["enable_fast_mode"]:
                # 仅进行基本的对比度调整
                alpha = 1.1  # 对比度因子
                beta = 10    # 亮度调整
                image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
                logger.debug("快速模式：跳过复杂图像增强")
            else:
                # 使用轻量级增强
                image = cls.enhance_image_fast(image)
            
            # 内存优化
            if OCR_PERFORMANCE_CONFIG["enable_memory_optimization"]:
                import gc
                gc.collect()
            
            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"快速图像预处理完成，耗时: {processing_time:.2f}ms")
            
            return image
            
        except Exception as e:
            logger.error(f"快速图像预处理失败: {str(e)}")
            # 降级到基本解码
            try:
                return cls.decode_image(image_data)
            except:
                logger.error("无法解码图像，返回空白图像")
                return np.zeros((300, 500, 3), dtype=np.uint8)

    @classmethod
    def preprocess_id_card_image(cls, image_data: Union[str, bytes]) -> np.ndarray:
        """
        身份证图像预处理流程（内存优化版本）
        
        Args:
            image_data: base64编码的图像数据或二进制图像数据
            
        Returns:
            预处理后的图像
        """
        try:
            # 导入垃圾回收模块用于内存优化
            import gc
            from app.config import MEMORY_OPTIMIZATION
            
            if MEMORY_OPTIMIZATION:
                logger.debug("开始身份证图像预处理流程（内存优化模式）")
            
            # 解码图像
            start_time = time.time()
            image = cls.decode_image(image_data)
            if MEMORY_OPTIMIZATION:
                logger.debug(f"图像解码完成，尺寸: {image.shape[1]}x{image.shape[0]}，耗时: {(time.time() - start_time)*1000:.2f}ms")
            
            # 调整图像大小
            image = cls.resize_image(image, max_size=800)  # 降低最大尺寸以节省内存
            if MEMORY_OPTIMIZATION:
                logger.debug(f"图像大小调整完成，调整后尺寸: {image.shape[1]}x{image.shape[0]}")
            
            # 内存优化：跳过复杂的轮廓检测和校正，仅进行必要的增强
            if MEMORY_OPTIMIZATION:
                # 使用最轻量的处理，直接返回调整大小后的图像
                logger.debug("跳过图像增强以节省内存")
                gc.collect()  # 强制垃圾回收
                return image
            else:
                # 保持原有的增强逻辑用于兼容性
                image = cls.enhance_image_fast(image)
                logger.debug("快速图像增强完成")
            
            if MEMORY_OPTIMIZATION:
                gc.collect()  # 强制垃圾回收
                logger.debug("身份证图像预处理流程完成（内存优化）")
            
            return image
            
        except Exception as e:
            logger.error(f"身份证图像预处理失败: {str(e)}")
            # 如果预处理失败，尝试直接解码图像并返回
            try:
                return cls.decode_image(image_data)
            except:
                # 如果连解码都失败，则返回一个空白图像
                logger.error("无法解码图像，返回空白图像")
                return np.zeros((300, 500, 3), dtype=np.uint8)
