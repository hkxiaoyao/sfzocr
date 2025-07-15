#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from typing import Optional

def validate_id_number(id_number: str) -> bool:
    """
    验证身份证号码格式
    
    Args:
        id_number: 身份证号码
        
    Returns:
        是否有效
    """
    if not id_number:
        return False
        
    # 18位身份证号码正则表达式
    pattern = r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}(\d|X|x)$'
    
    if not re.match(pattern, id_number):
        return False
    
    # 验证校验位
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    checksum_map = '10X98765432'
    
    # 计算校验和
    checksum = 0
    for i in range(17):
        checksum += int(id_number[i]) * factors[i]
    
    # 计算校验位
    check_digit = checksum_map[checksum % 11]
    
    # 验证校验位
    return str(check_digit).upper() == id_number[17].upper()

def validate_image_base64(image_data: str) -> bool:
    """
    验证base64编码的图像数据
    
    Args:
        image_data: base64编码的图像数据
        
    Returns:
        是否有效
    """
    if not image_data:
        return False
    
    # 移除可能的base64前缀
    if "base64," in image_data:
        image_data = image_data.split("base64,")[1]
    
    # 验证base64格式
    pattern = r'^[A-Za-z0-9+/]+={0,2}$'
    return bool(re.match(pattern, image_data))

def validate_chinese_name(name: str) -> bool:
    """
    验证中文姓名
    
    Args:
        name: 姓名
        
    Returns:
        是否有效
    """
    if not name:
        return False
    
    # 中文姓名正则表达式（2-15个汉字）
    pattern = r'^[\u4e00-\u9fa5]{2,15}$'
    return bool(re.match(pattern, name))

def extract_birth_date(birth_text: str) -> Optional[str]:
    """
    从出生日期文本中提取标准格式的日期
    
    Args:
        birth_text: 出生日期文本，如"1990年01月01日"
        
    Returns:
        标准格式的日期（YYYY-MM-DD）或None
    """
    if not birth_text:
        return None
    
    # 提取年月日
    pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
    match = re.search(pattern, birth_text)
    
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)  # 补零
        day = match.group(3).zfill(2)    # 补零
        return f"{year}-{month}-{day}"
    
    # 尝试其他可能的格式
    pattern = r'(\d{4})[-.年/](\d{1,2})[-.月/](\d{1,2})[日]?'
    match = re.search(pattern, birth_text)
    
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}-{month}-{day}"
    
    return None

def normalize_id_card_info(info: dict) -> dict:
    """
    规范化身份证信息
    
    Args:
        info: 身份证信息字典
        
    Returns:
        规范化后的信息字典
    """
    result = info.copy()
    
    # 规范化出生日期
    if 'birth' in result and result['birth']:
        birth_date = extract_birth_date(result['birth'])
        if birth_date:
            result['birth'] = birth_date
    
    # 规范化性别
    if 'sex' in result and result['sex']:
        sex = result['sex'].strip()
        if sex in ['男', '1']:
            result['sex'] = '男'
        elif sex in ['女', '2']:
            result['sex'] = '女'
    
    # 规范化民族
    if 'nation' in result and result['nation']:
        nation = result['nation'].strip()
        # 移除可能的"族"字
        if nation.endswith('族'):
            result['nation'] = nation[:-1]
    
    return result
