import sys

from loguru import logger

# 配置loguru
logger.remove()  # 移除默认的处理器

# 添加控制台输出
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

# 添加文件输出
logger.add(
    "app.log",
    rotation="500 MB",  # 日志文件大小达到500MB时轮转
    retention="10 days",  # 保留10天的日志
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
)
