import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量到系统环境中
load_dotenv()

# 从环境变量读取配置，第二个参数是默认值（.env读不到时使用）
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
API_JSON_PATH = os.getenv("API_JSON_PATH", "")
OUTPUT_IMAGE_DIR = os.getenv("OUTPUT_IMAGE_DIR", "./generated_images")
STATIC_DIR = os.getenv("STATIC_DIR", "./static")

# ComfyUI工作流节点ID（修改工作流后需同步更新）
PERSON_IMAGE_NODE_ID = "76"    # 人物图片输入节点
CLOTHES_IMAGE_NODE_ID = "129"  # 服装图片输入节点

# 文件校验常量
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 任务轮询超时时间（秒）
TASK_TIMEOUT = 600