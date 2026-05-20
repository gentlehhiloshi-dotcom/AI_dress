import os
import random
import string
from uuid import uuid4

# 导入logger，复用main.py里配置好的日志格式
import logging
logger = logging.getLogger(__name__)


def generate_random_str(length=8) -> str:
    """生成指定长度的随机字母数字字符串，用于避免文件名重复"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_seed() -> int:
    """生成ComfyUI兼容的随机种子，范围是64位无符号整数"""
    return random.randint(0, 0xFFFFFFFFFFFFFFFF)


def generate_task_id() -> str:
    """生成唯一任务ID，使用UUID4保证全局唯一"""
    return str(uuid4())


def cleanup_temp_files(*file_paths: str):
    """
    删除临时文件，接受任意数量的文件路径
    例如：cleanup_temp_files(path1, path2)
    """
    for file_path in file_paths:
        try:
            # 先判断文件是否存在，再删除，避免报错
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"已清理临时文件：{file_path}")
        except Exception as e:
            # 清理失败不影响主流程，只记录警告
            logger.warning(f"清理临时文件失败：{file_path}，原因：{str(e)}")