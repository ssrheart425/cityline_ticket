import logging
import colorlog

# 创建日志记录器
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)  # 设置日志级别为 DEBUG

# 创建带颜色的输出格式
log_format = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# 使用 colorlog.StreamHandler 来创建彩色控制台输出
handler = colorlog.StreamHandler()
handler.setLevel(logging.DEBUG)

# 设置日志格式
formatter = colorlog.ColoredFormatter(log_format, datefmt=date_format)
handler.setFormatter(formatter)

# 将 handler 添加到 logger
logger.addHandler(handler)
