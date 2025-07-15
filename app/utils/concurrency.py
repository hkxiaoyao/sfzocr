#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import asyncio
import concurrent.futures
import psutil
import gc
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import partial

from app.config import OCR_PROCESS_POOL_SIZE, OCR_TASK_TIMEOUT, MEMORY_OPTIMIZATION, ENABLE_GC_AFTER_REQUEST
from app.utils.logger import get_logger

# 类型变量
T = TypeVar('T')
R = TypeVar('R')

# 获取logger
logger = get_logger("concurrency")

class ProcessPoolManager:
    """进程池管理器，用于处理CPU密集型任务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessPoolManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._pool = concurrent.futures.ProcessPoolExecutor(
            max_workers=OCR_PROCESS_POOL_SIZE
        )
        self._initialized = True
        self._log_memory_usage("进程池初始化")
        logger.info(f"进程池已初始化，工作进程数: {OCR_PROCESS_POOL_SIZE} (内存优化模式: {MEMORY_OPTIMIZATION})")
    
    def _log_memory_usage(self, operation: str):
        """记录内存使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if MEMORY_OPTIMIZATION:
                logger.debug(f"[内存监控] {operation} - 当前进程内存使用: {memory_mb:.1f}MB")
            else:
                logger.info(f"[内存监控] {operation} - 当前进程内存使用: {memory_mb:.1f}MB")
                
            # 如果内存使用超过阈值，记录警告
            if memory_mb > 1024:  # 超过1GB发出警告
                logger.warning(f"[内存警告] 进程内存使用过高: {memory_mb:.1f}MB")
                
        except Exception as e:
            logger.debug(f"内存监控失败: {str(e)}")
    
    async def run_task(self, func: Callable[..., R], *args, **kwargs) -> R:
        """
        在进程池中异步执行任务
        
        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            **kwargs: 函数的关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            TimeoutError: 任务执行超时
            Exception: 任务执行失败
        """
        loop = asyncio.get_running_loop()
        
        start_time = time.time()
        if MEMORY_OPTIMIZATION:
            logger.debug(f"开始执行任务: {func.__name__}")
            self._log_memory_usage(f"任务开始-{func.__name__}")
        
        try:
            # 使用run_in_executor在进程池中执行函数
            if kwargs:
                # 如果有关键字参数，使用partial包装函数
                func_with_kwargs = partial(func, *args, **kwargs)
                result = await asyncio.wait_for(
                    loop.run_in_executor(self._pool, func_with_kwargs),
                    timeout=OCR_TASK_TIMEOUT
                )
            else:
                result = await asyncio.wait_for(
                    loop.run_in_executor(self._pool, func, *args),
                    timeout=OCR_TASK_TIMEOUT
                )
            
            execution_time = time.time() - start_time
            
            # 内存优化：任务完成后进行垃圾回收
            if ENABLE_GC_AFTER_REQUEST:
                gc.collect()
                
            if MEMORY_OPTIMIZATION:
                logger.debug(f"任务 {func.__name__} 执行完成，耗时: {execution_time:.2f}秒")
                self._log_memory_usage(f"任务完成-{func.__name__}")
            else:
                logger.debug(f"任务 {func.__name__} 执行完成，耗时: {execution_time:.2f}秒")
                
            return result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.error(f"任务 {func.__name__} 执行超时，已耗时: {execution_time:.2f}秒")
            raise TimeoutError(f"任务执行超时，超过 {OCR_TASK_TIMEOUT} 秒")
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"任务 {func.__name__} 执行失败，耗时: {execution_time:.2f}秒，错误: {str(e)}")
            raise
    
    def shutdown(self):
        """关闭进程池"""
        if hasattr(self, '_pool'):
            self._pool.shutdown(wait=True)
            logger.info("进程池已关闭")

# 全局进程池管理器实例
process_pool_manager = ProcessPoolManager()

# 在程序退出时关闭进程池
import atexit
atexit.register(process_pool_manager.shutdown)

# 异步批处理函数
async def run_batch_tasks(
    func: Callable[..., R], 
    items: List[Any], 
    max_concurrency: Optional[int] = None
) -> List[R]:
    """
    并发执行多个任务
    
    Args:
        func: 要执行的函数
        items: 要处理的项目列表
        max_concurrency: 最大并发数，默认为None（不限制）
        
    Returns:
        结果列表
    """
    if not items:
        return []
    
    if max_concurrency is None:
        # 创建所有任务
        tasks = [process_pool_manager.run_task(func, item) for item in items]
        # 并发执行所有任务
        return await asyncio.gather(*tasks, return_exceptions=True)
    else:
        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def _run_with_semaphore(item):
            async with semaphore:
                return await process_pool_manager.run_task(func, item)
        
        # 创建所有任务
        tasks = [_run_with_semaphore(item) for item in items]
        # 并发执行所有任务
        return await asyncio.gather(*tasks, return_exceptions=True)
