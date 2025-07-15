#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

# NumPy补丁：解决np.int弃用问题
# 在导入PaddleOCR之前添加补丁
if not hasattr(np, 'int'):
    np.int = int
if not hasattr(np, 'float'):
    np.float = float
if not hasattr(np, 'bool'):
    np.bool = bool

from paddleocr import PaddleOCR
from app.config import OCR_MODEL_DIR, ID_CARD_CONFIG, ID_CARD_FIELD_MAPPING
from app.core.image_processor import ImageProcessor
from app.utils.logger import get_logger

# 获取logger
logger = get_logger("ocr_engine")

# 全局OCR引擎实例缓存，按进程ID存储
_ocr_instances = {}

def get_ocr_engine():
    """
    获取当前进程的OCR引擎实例
    
    Returns:
        PaddleOCR实例
    """
    import os
    pid = os.getpid()
    
    # 如果当前进程已有实例，则直接返回
    if pid in _ocr_instances:
        return _ocr_instances[pid]
    
    # 否则创建新实例
    logger.info(f"进程 {pid} 初始化OCR引擎...")
    
    # 创建模型目录
    os.makedirs(OCR_MODEL_DIR, exist_ok=True)
    
    # 初始化PaddleOCR
    try:
        ocr = PaddleOCR(
            use_angle_cls=ID_CARD_CONFIG["use_angle_cls"],
            lang="ch",  # 中文模型
            det=ID_CARD_CONFIG["det"],
            rec=ID_CARD_CONFIG["rec"],
            cls=ID_CARD_CONFIG["cls"],
            use_gpu=False  # 默认使用CPU，可根据需要修改
        )
        _ocr_instances[pid] = ocr
        logger.info(f"进程 {pid} OCR引擎初始化完成")
        return ocr
    except Exception as e:
        logger.error(f"进程 {pid} OCR引擎初始化失败: {str(e)}")
        raise RuntimeError(f"OCR引擎初始化失败: {str(e)}")

def recognize_text(image: np.ndarray) -> List[List[Tuple[List[List[int]], str, float]]]:
    """
    识别图像中的文字
    
    Args:
        image: 图像数组
        
    Returns:
        识别结果列表，格式为[[[坐标], 文本, 置信度], ...]
    """
    try:
        start_time = time.time()
        ocr = get_ocr_engine()
        result = ocr.ocr(image, cls=True)
        
        # PaddleOCR返回的结果格式可能因版本而异，进行适配
        if result is None:
            return []
            
        # 如果结果是列表但没有嵌套，则进行包装
        if result and not isinstance(result[0], list):
            result = [result]
            
        # 取第一页结果（通常只有一页）
        if result:
            result = result[0]
            
        execution_time = time.time() - start_time
        logger.info(f"OCR识别完成，耗时: {execution_time:.2f}秒，识别到 {len(result)} 个文本块")
        return result
        
    except Exception as e:
        logger.error(f"OCR识别失败: {str(e)}")
        return []

def extract_id_card_info(image_data: Union[str, bytes], is_front: bool = True) -> Dict[str, Any]:
    """
    提取身份证信息
    
    Args:
        image_data: base64编码的图像数据或二进制图像数据
        is_front: 是否为身份证正面，默认为True
        
    Returns:
        提取的身份证信息字典
    """
    try:
        # 预处理图像
        image = ImageProcessor.preprocess_id_card_image(image_data)
        
        # 识别文字
        ocr_result = recognize_text(image)
        
        # 提取身份证信息
        id_card_info = {}
        
        # 如果没有识别结果，返回空字典
        if not ocr_result:
            logger.warning("未识别到任何文字")
            return id_card_info
        
        # 提取文本和位置信息
        text_blocks = []
        for item in ocr_result:
            if len(item) >= 2:  # 确保结果格式正确
                coords, (text, confidence) = item
                # 计算文本块的中心点坐标
                center_x = sum(point[0] for point in coords) / 4
                center_y = sum(point[1] for point in coords) / 4
                text_blocks.append({
                    "text": text,
                    "confidence": confidence,
                    "center": (center_x, center_y),
                    "coords": coords
                })
        
        # 记录所有识别到的文本，用于调试
        logger.debug(f"识别到的文本块: {[block['text'] for block in text_blocks]}")
        
        # 根据身份证正反面提取不同信息
        if is_front:
            # 提取身份证号码（通常位于底部）
            id_number = _extract_id_number(text_blocks)
            if id_number:
                id_card_info["id_number"] = id_number
            
            # 智能姓名提取 - 支持分离的文本块
            name_value = _extract_name_smart(text_blocks)
            if name_value:
                id_card_info["name"] = name_value
            
            # 提取其他字段
            field_patterns = {
                "性别": r"性别[\s:：]*([男女])",  # 修改性别匹配模式，只匹配"男"或"女"
                "民族": r"民族[\s:：]*(.+)",
                "出生": r"出生[\s:：]*(.+)"
                # 移除住址字段，让它由后续的地址合并逻辑处理
                # 移除姓名字段，由智能提取处理
            }
            
            # 遍历文本块提取信息
            address_blocks = []
            birth_blocks = []
            
            for block in text_blocks:
                text = block["text"].strip()
                
                # 检查是否匹配任何字段
                for field, pattern in field_patterns.items():
                    match = re.search(pattern, text)
                    if match:
                        field_key = ID_CARD_FIELD_MAPPING.get(field, field)
                        field_value = match.group(1).strip()
                        id_card_info[field_key] = field_value
                        
                        # 如果是出生日期字段，添加到birth_blocks以便后续处理
                        if field == "出生":
                            birth_blocks.append(block)
                        break
                
                # 特殊处理性别和民族字段，它们可能在同一行
                if "性别" in text and "民族" in text:
                    # 尝试提取性别和民族
                    sex_match = re.search(r"性别[\s:：]*([男女])", text)
                    nation_match = re.search(r"民族[\s:：]*([^\s]+)", text)
                    
                    if sex_match:
                        id_card_info["sex"] = sex_match.group(1).strip()
                    if nation_match:
                        id_card_info["nation"] = nation_match.group(1).strip()
                
                # 处理"性别男民族汉"这样的格式
                if "性别" in text and "民族" in text and "sex" not in id_card_info:
                    # 尝试匹配"性别男民族汉"格式
                    combined_match = re.search(r"性别([男女])民族([^\s]+)", text)
                    if combined_match:
                        id_card_info["sex"] = combined_match.group(1).strip()
                        id_card_info["nation"] = combined_match.group(2).strip()
                        logger.info(f"从组合文本中提取性别和民族: 性别={id_card_info['sex']}, 民族={id_card_info['nation']}")
                
                # 住址可能跨多行，收集可能的住址行
                if "住址" in text:
                    address_blocks.append(block)
                elif address_blocks:
                    # 如果已经有住址块，检查当前块是否可能是地址的延续
                    # 放宽条件，不再排除包含特定关键词的块，因为地址可能包含门牌号等信息
                    # 通过检查y坐标和位置关系来判断是否是地址的延续
                    last_block = address_blocks[-1]
                    y_diff = abs(block["center"][1] - last_block["center"][1])
                    x_pos = block["center"][0]
                    
                    # 如果y坐标接近（同一行或下一行）或者x坐标在合理范围内（可能是下一行地址）
                    # 放宽垂直距离限制，从50增加到70
                    if y_diff < 70 or (y_diff < 120 and x_pos > 50):
                        # 检查文本是否像地址的一部分，但要排除明显不是地址的内容
                        if _is_valid_address_text(text):
                            address_blocks.append(block)
                            logger.debug(f"添加地址延续块: {text}")
                
                # 尝试提取出生日期，可能在"出生"文本块的附近
                if "出生" in text and "birth" not in id_card_info:
                    # 尝试直接从文本中提取日期格式
                    date_patterns = [
                        r"(\d{4}年\d{1,2}月\d{1,2}日)",  # 1990年1月1日
                        r"(\d{4}[\./\-年]\d{1,2}[\./\-月]\d{1,2}[日]?)",  # 1990.1.1, 1990-1-1
                        r"(\d{4}[年\s]+\d{1,2}[月\s]+\d{1,2}[日]?)"  # 1990 1 1
                    ]
                    
                    for pattern in date_patterns:
                        date_match = re.search(pattern, text)
                        if date_match:
                            id_card_info["birth"] = date_match.group(1).strip()
                            break
            
            # 如果没有找到出生日期，尝试从身份证号码提取
            if "birth" not in id_card_info and "id_number" in id_card_info:
                id_num = id_card_info["id_number"]
                if len(id_num) == 18 and re.match(r"^\d{17}[\dXx]$", id_num):
                    # 从身份证号码提取出生日期 (格式: YYYYMMDD, 位置: 7-14)
                    year = id_num[6:10]
                    month = id_num[10:12]
                    day = id_num[12:14]
                    id_card_info["birth"] = f"{year}年{int(month)}月{int(day)}日"
                    logger.info(f"从身份证号码提取出生日期: {id_card_info['birth']}")
            
            # 处理住址（可能跨多行）
            if "address" not in id_card_info and address_blocks:
                # 按y坐标排序，然后按x坐标排序（处理同一行的多个块）
                address_blocks.sort(key=lambda b: (b["center"][1], b["center"][0]))
                
                # 记录排序后的地址块
                logger.debug(f"排序后的地址块: {[block['text'] for block in address_blocks]}")
                
                # 提取地址文本
                address_parts = []
                
                for block in address_blocks:
                    text = block["text"].strip()
                    logger.debug(f"处理地址块: '{text}'")
                    
                    if "住址" in text:
                        # 提取住址后面的部分
                        original_text = text
                        text = re.sub(r"住址[\s:：]*", "", text)
                        logger.debug(f"住址块处理: '{original_text}' -> '{text}'")
                    
                    # 直接添加所有地址块的文本，不再按行分组
                    # 因为OCR识别的文本块已经是有意义的单位，应该直接合并
                    if text:  # 确保文本不为空
                        address_parts.append(text)
                        logger.debug(f"添加地址部分: '{text}'")
                    else:
                        logger.debug(f"跳过空文本块")
                
                logger.debug(f"所有地址部分: {address_parts}")
                
                # 合并所有地址组件，不使用空格分隔（符合中文地址格式）
                address = "".join(address_parts)
                id_card_info["address"] = address.strip()
                logger.debug(f"初始提取的地址: {id_card_info['address']}")
                
                # 清理地址中可能的多余空格和标点符号
                if "address" in id_card_info:
                    # 删除所有空格（中文地址通常不需要空格）
                    id_card_info["address"] = re.sub(r'\s+', '', id_card_info["address"])
                    # 删除末尾可能的标点符号
                    id_card_info["address"] = re.sub(r'[,，.。、；;]$', '', id_card_info["address"])
                    
                    # 检查是否有单独的数字块可能是门牌号
                    house_number_block = None
                    for block in text_blocks:
                        if block not in address_blocks:  # 避免重复处理已包含的块
                            text = block["text"].strip()
                            # 检查是否是门牌号格式（更广泛的模式）
                            # 扩展门牌号识别模式，包括更多组合形式
                            if (re.match(r'^\d+号?$', text) or  # 纯数字或数字+号
                                re.match(r'^[0-9-]+号?$', text) or  # 数字-数字格式
                                re.match(r'^\d+[号室栋单元]$', text) or  # 数字+单位
                                re.match(r'^\d+[A-Za-z]号?$', text) or  # 数字+字母
                                re.match(r'^[村组社区队]\d+号?$', text) or  # 村/组/社区/队+数字
                                re.match(r'.*[村组社区队]\d+号?$', text)):  # 任意文本+村/组/社区/队+数字
                                # 检查位置是否在最后一个地址块附近
                                if address_blocks:
                                    last_block = address_blocks[-1]
                                    y_diff = abs(block["center"][1] - last_block["center"][1])
                                    # 放宽垂直距离限制，从80增加到120
                                    if y_diff < 120:  # 允许更大的垂直距离
                                        house_number_block = block
                                        logger.info(f"找到可能的门牌号: {text}")
                                        break
                    
                    # 如果找到门牌号，添加到地址末尾
                    if house_number_block:
                        if not id_card_info["address"].endswith(house_number_block["text"]):
                            id_card_info["address"] += house_number_block["text"]
                            logger.info(f"添加门牌号后的地址: {id_card_info['address']}")
                    
                    # 如果地址中不包含数字，检查是否有单独的数字块
                    elif not re.search(r'\d', id_card_info["address"]):
                        # 查找所有可能的数字块
                        number_blocks = []
                        for block in text_blocks:
                            text = block["text"].strip()
                            if re.search(r'\d+', text) and len(text) < 10:  # 避免误匹配身份证号等长数字
                                number_blocks.append(block)
                        
                        # 如果找到数字块，选择最接近地址块的一个
                        if number_blocks and address_blocks:
                            last_address_block = address_blocks[-1]
                            closest_block = min(number_blocks, 
                                               key=lambda b: abs(b["center"][1] - last_address_block["center"][1]))
                            
                            # 如果距离合理，添加到地址
                            # 放宽垂直距离限制，从100增加到150
                            if abs(closest_block["center"][1] - last_address_block["center"][1]) < 150:
                                id_card_info["address"] += closest_block["text"]
                                logger.info(f"添加数字块后的地址: {id_card_info['address']}")
                    
                    # 添加地址后处理逻辑
                    processed_address = _post_process_address(id_card_info["address"], text_blocks)
                    if processed_address != id_card_info["address"]:
                        id_card_info["address"] = processed_address
                        logger.info(f"地址后处理后: {id_card_info['address']}")
                    
                    # 应用地址规则引擎
                    rule_processed_address = _apply_address_rules(id_card_info["address"], id_card_info.get("name", ""), text_blocks)
                    if rule_processed_address != id_card_info["address"]:
                        id_card_info["address"] = rule_processed_address
                        logger.info(f"地址规则引擎处理后: {id_card_info['address']}")
                    
                    logger.info(f"最终地址: {id_card_info['address']}")
        else:
            # 提取签发机关和有效期限（身份证背面）
            for block in text_blocks:
                text = block["text"].strip()
                
                # 提取签发机关
                if "签发机关" in text:
                    match = re.search(r"签发机关[\s:：]*(.+)", text)
                    if match:
                        id_card_info["issue_authority"] = match.group(1).strip()
                
                # 提取有效期限
                if "有效期" in text:
                    match = re.search(r"有效期[限至]?[\s:：]*(.+)", text)
                    if match:
                        id_card_info["valid_period"] = match.group(1).strip()
        
        # 记录提取结果
        logger.info(f"提取的身份证信息: {id_card_info}")
        
        return id_card_info
        
    except Exception as e:
        logger.error(f"提取身份证信息失败: {str(e)}")
        return {}

def _extract_name_smart(text_blocks: List[Dict[str, Any]]) -> Optional[str]:
    """
    智能提取姓名，支持分离的文本块
    
    Args:
        text_blocks: 文本块列表
        
    Returns:
        提取的姓名或None
    """
    # 方法1：尝试在同一文本块中找到姓名
    for block in text_blocks:
        text = block["text"].strip()
        # 检查是否在同一块中包含姓名标签和姓名
        match = re.search(r"姓名[\s:：]*(.+)", text)
        if match:
            name = match.group(1).strip()
            if name and len(name) <= 10:  # 姓名长度验证
                logger.info(f"在同一文本块中提取姓名: {name}")
                return name
    
    # 方法2：查找"姓名"标签，然后在附近的文本块中查找姓名
    name_label_block = None
    for block in text_blocks:
        text = block["text"].strip()
        if text == "姓名" or "姓名" in text:
            name_label_block = block
            break
    
    if name_label_block:
        name_label_center = name_label_block["center"]
        logger.debug(f"找到姓名标签块，位置: {name_label_center}")
        
        # 在附近查找可能的姓名文本块
        candidate_blocks = []
        for block in text_blocks:
            if block == name_label_block:
                continue
            
            text = block["text"].strip()
            block_center = block["center"]
            
            # 跳过明显不是姓名的文本
            if text in ["性别", "民族", "出生", "住址", "公民身份号码"] or len(text) > 10:
                continue
            
            # 计算与姓名标签的距离
            distance = ((block_center[0] - name_label_center[0]) ** 2 + 
                       (block_center[1] - name_label_center[1]) ** 2) ** 0.5
            
            # 检查是否为有效的姓名格式
            if _is_valid_name(text):
                candidate_blocks.append((block, distance, text))
                logger.debug(f"找到姓名候选: '{text}'，距离: {distance:.1f}")
        
        # 按距离排序，选择最近的有效姓名
        if candidate_blocks:
            candidate_blocks.sort(key=lambda x: x[1])  # 按距离排序
            closest_name = candidate_blocks[0][2]
            logger.info(f"基于位置关联提取姓名: {closest_name}")
            return closest_name
    
    # 方法3：如果前两种方法都失败，尝试查找看起来像姓名的文本
    for block in text_blocks:
        text = block["text"].strip()
        if _is_valid_name(text) and len(text) >= 2 and len(text) <= 5:
            # 确保不是其他标识词
            if text not in ["性别", "民族", "出生", "住址", "公民", "身份", "号码"]:
                logger.info(f"通过格式匹配提取姓名: {text}")
                return text
    
    logger.warning("未能提取到姓名")
    return None

def _is_valid_name(text: str) -> bool:
    """
    检查文本是否可能是有效的姓名
    
    Args:
        text: 待检查的文本
        
    Returns:
        是否为有效姓名格式
    """
    if not text or len(text) < 2 or len(text) > 5:
        return False
    
    # 检查是否主要由中文字符组成
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    if chinese_chars < len(text) * 0.8:  # 至少80%是中文字符
        return False
    
    # 排除常见的非姓名词汇
    exclude_words = ["性别", "民族", "出生", "住址", "公民", "身份", "号码", "签发", "机关", "有效", "期限"]
    if any(word in text for word in exclude_words):
        return False
    
    return True

def _extract_id_number(text_blocks: List[Dict[str, Any]]) -> Optional[str]:
    """
    提取身份证号码
    
    Args:
        text_blocks: 文本块列表
        
    Returns:
        身份证号码或None
    """
    # 身份证号码正则表达式
    id_pattern = r"[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}(?:\d|X|x)"
    
    # 首先查找包含"公民身份号码"的文本块
    for block in text_blocks:
        text = block["text"].strip()
        if "公民身份号码" in text:
            # 尝试从同一文本块中提取
            match = re.search(id_pattern, text)
            if match:
                return match.group(0)
            
            # 如果在同一块中没找到，查找y坐标接近的块
            block_y = block["center"][1]
            for other_block in text_blocks:
                if other_block == block:
                    continue
                
                other_text = other_block["text"].strip()
                other_y = other_block["center"][1]
                
                # 如果y坐标接近，检查是否包含身份证号
                if abs(other_y - block_y) < 50:
                    match = re.search(id_pattern, other_text)
                    if match:
                        return match.group(0)
    
    # 如果没有找到包含"公民身份号码"的文本块，尝试直接匹配身份证号格式
    for block in text_blocks:
        text = block["text"].strip()
        match = re.search(id_pattern, text)
        if match:
            return match.group(0)
    
    return None

def _post_process_address(address: str, text_blocks: List[Dict[str, Any]]) -> str:
    """
    地址后处理函数，用于检查并合并可能遗漏的地址组件
    
    Args:
        address: 初步提取的地址
        text_blocks: 所有文本块
        
    Returns:
        处理后的地址
    """
    logger.debug(f"地址后处理开始，原始地址: {address}")
    
    # 检查地址是否已经包含村/组/社区等关键词和门牌号
    has_village = bool(re.search(r'[村组社区队]', address))
    has_house_number = bool(re.search(r'\d+号', address))
    
    logger.debug(f"地址分析：包含村/组/社区/队={has_village}, 包含门牌号={has_house_number}")
    
    # 如果地址缺少村名或门牌号，尝试从其他文本块中找到
    processed_address = address
    
    # 1. 查找村/组+门牌号的组合模式
    village_number_patterns = [
        r'([村组社区队]\d+号?)',  # 村218号, 组5号
        r'([^住址]*[村组社区队]\d+号?)',  # 边庄村218号
        r'([村组社区队][^住址]*\d+号?)',  # 村边庄218号  
        r'([^住址]*[村组社区队][^住址]*\d+号?)',  # 任意文本+村+任意文本+数字+号
    ]
    
    for block in text_blocks:
        text = block["text"].strip()
        if "住址" in text:
            continue  # 跳过住址标签文本
            
        # 检查是否匹配村/组+门牌号模式，并且是有效的地址文本
        if _is_valid_address_text(text):
            for pattern in village_number_patterns:
                match = re.search(pattern, text)
                if match:
                    village_part = match.group(1)
                    if village_part not in processed_address:
                        processed_address += village_part
                        logger.debug(f"添加村/组+门牌号: {village_part}")
                        return processed_address
    
    # 2. 如果没有找到组合模式，分别查找村名和门牌号
    if not has_village:
        # 查找村/组/社区名称
        for block in text_blocks:
            text = block["text"].strip()
            if "住址" in text or not _is_valid_address_text(text):
                continue
                
            village_match = re.search(r'([^住址]*[村组社区队])', text)
            if village_match:
                village_name = village_match.group(1)
                if village_name not in processed_address:
                    processed_address += village_name
                    logger.debug(f"添加村/组名称: {village_name}")
                    break
    
    if not has_house_number:
        # 查找门牌号（更广泛的模式）
        house_number_patterns = [
            r'(\d+号)',  # 218号
            r'(\d+[室栋单元])',  # 218室
            r'([A-Za-z]?\d+号?)',  # A218号, 218
            r'(\d+-\d+号?)',  # 218-1号
            r'(\d+[A-Za-z]号?)',  # 218A号
            r'(第?\d+号)',  # 第218号
            r'(\d+[弄巷里街道路]?\d*号?)',  # 218弄5号
        ]
        
        for block in text_blocks:
            text = block["text"].strip()
            if "住址" in text or len(text) > 20 or not _is_valid_address_text(text):  # 增加地址有效性检查
                continue
                
            for pattern in house_number_patterns:
                match = re.search(pattern, text)
                if match:
                    house_number = match.group(1)
                    if house_number not in processed_address:
                        processed_address += house_number
                        logger.debug(f"添加门牌号: {house_number}")
                        return processed_address
    
    logger.debug(f"地址后处理完成，最终地址: {processed_address}")
    return processed_address

def _apply_address_rules(address: str, name: str, text_blocks: List[Dict[str, Any]]) -> str:
    """
    应用地址规则引擎，基于规则补全地址
    
    Args:
        address: 初步处理后的地址
        name: 身份证姓名
        text_blocks: 所有文本块
        
    Returns:
        规则处理后的地址
    """
    logger.debug(f"应用地址规则引擎，输入地址: {address}, 姓名: {name}")
    
    # 特殊情况处理：边茹的身份证
    # if name == "边茹" and "山东省邹城市太平镇边庄" in address and "村218号" not in address:
    #     address += "村218号"
    #     logger.info(f"应用特殊规则：为边茹添加'村218号'，最终地址: {address}")
    #     return address
    
    # 规则1：如果地址以乡/镇结尾，查找可能的村/组名称
    if re.search(r'[乡镇]$', address):
        logger.debug("应用规则1：地址以乡/镇结尾，查找村/组名称")
        
        # 提取地址中的最后一个地名（通常是乡镇名）
        last_place = address.split()[-1]
        if last_place.endswith("乡") or last_place.endswith("镇"):
            last_place = last_place[:-1]  # 去掉"乡"或"镇"字
            
            # 在所有文本块中查找可能包含该地名的村/组
            for block in text_blocks:
                text = block["text"].strip()
                # 查找格式如"XX村"、"XX组"等
                village_match = re.search(f"{last_place}[村组社区队]", text)
                if village_match:
                    village_name = village_match.group(0)
                    if village_name not in address:
                        address += " " + village_name
                        logger.info(f"应用规则1：添加村/组名称 '{village_name}'")
                        
                        # 继续查找门牌号
                        number_match = re.search(r'\d+号?', text[village_match.end():])
                        if number_match:
                            address += number_match.group(0)
                            logger.info(f"应用规则1：添加门牌号 '{number_match.group(0)}'")
                        
                        return address
    
    # 规则2：如果地址中包含村/组但没有门牌号，尝试查找门牌号
    if re.search(r'[村组社区队]$', address) and not re.search(r'\d+号?', address):
        logger.debug("应用规则2：地址包含村/组但没有门牌号")
        
        # 提取村/组名
        village_name = re.search(r'\w+[村组社区队]$', address)
        if village_name:
            village_name = village_name.group(0)
            
            # 在所有文本块中查找可能包含该村/组名的门牌号
            for block in text_blocks:
                text = block["text"].strip()
                if village_name in text:
                    # 查找村/组名后面的门牌号
                    idx = text.find(village_name) + len(village_name)
                    if idx < len(text):
                        number_match = re.search(r'\d+号?', text[idx:])
                        if number_match:
                            address += number_match.group(0)
                            logger.info(f"应用规则2：添加门牌号 '{number_match.group(0)}'")
                            return address
    
    # 规则3：检查是否有独立的门牌号文本块
    if not re.search(r'\d+号?', address):
        logger.debug("应用规则3：查找独立的门牌号文本块")
        
        # 查找可能是门牌号的独立文本块
        for block in text_blocks:
            text = block["text"].strip()
            if re.match(r'^\d+号?$', text) and len(text) < 10:  # 避免误匹配身份证号等长数字
                address += " " + text
                logger.info(f"应用规则3：添加独立门牌号 '{text}'")
                return address
    
    logger.debug("地址规则引擎：未触发任何规则，返回原始地址")
    return address

def _is_valid_address_text(text: str) -> bool:
    """
    检查文本是否是有效的地址组成部分
    
    Args:
        text: 要检查的文本
        
    Returns:
        True if valid address text, False otherwise
    """
    text = text.strip()
    
    # 排除条件
    # 1. 排除身份证号码（15位或18位数字）
    if re.match(r'^\d{15}$|^\d{17}[\dXx]$', text):
        return False
    
    # 2. 排除包含"公民身份号码"的文本
    if "公民身份号码" in text or "身份号码" in text:
        return False
    
    # 3. 排除单纯的年份（4位数字，1900-2100年）
    if re.match(r'^(19|20)\d{2}$', text):
        return False
    
    # 4. 排除过长的数字串（超过8位连续数字）
    if re.match(r'^\d{9,}$', text):
        return False
    
    # 5. 排除包含出生日期相关关键词的文本
    if any(keyword in text for keyword in ["出生", "生日", "年", "月", "日"]) and not any(addr_keyword in text for addr_keyword in ["省", "市", "区", "县", "乡", "镇", "村", "组", "路", "街", "道", "号", "室", "栋", "单元"]):
        return False
    
    # 包含条件：必须包含地址相关关键词
    address_keywords = r'[省市区县乡镇村组路街道号室社区队栋单元巷弄里]'
    if re.search(address_keywords, text):
        return True
    
    # 或者是门牌号格式（但不能是身份证号或年份）
    if re.match(r'^\d{1,4}号?[A-Za-z]?$', text) and len(text) <= 6:
        return True
    
    return False

# 清理进程的OCR实例
def cleanup_ocr_engine():
    """
    清理当前进程的OCR引擎实例
    """
    import os
    pid = os.getpid()
    if pid in _ocr_instances:
        del _ocr_instances[pid]
        logger.info(f"进程 {pid} OCR引擎已清理")

# 在进程退出时清理OCR实例
import atexit
atexit.register(cleanup_ocr_engine)
