"""
实时纠错校验（占位，阶段 2 实现）
读取 validation_rules 表，匹配 condition_json，返回 info/warning/error
"""
from app.utils.logger import logger


def validate_input(input_data: dict, type_: str) -> list[dict]:
    """实时校验，返回 [{variable, level, message}]"""
    logger.info(f"validation: type={type_}")
    return []
