import os
import json
import time
import random
import requests
import logging
from uuid import uuid4

# 从配置文件导入所有常量，不再硬编码
from app.config.settings import (
    COMFYUI_URL,
    API_JSON_PATH,
    OUTPUT_IMAGE_DIR,
    PERSON_IMAGE_NODE_ID,
    CLOTHES_IMAGE_NODE_ID,
    TASK_TIMEOUT
)
from app.utils.file_utils import generate_random_str, generate_random_seed, cleanup_temp_files

logger = logging.getLogger(__name__)

# 存储所有任务状态的字典
# 格式：{task_id: {"status": "pending/success/failed", "image_url": "", "error": ""}}
task_status = {}


def load_comfyui_api_json() -> dict:
    """加载ComfyUI工作流JSON文件"""
    try:
        if not os.path.exists(API_JSON_PATH):
            raise Exception(f"API JSON文件不存在：{API_JSON_PATH}")

        with open(API_JSON_PATH, "r", encoding="utf-8") as f:
            api_json = json.load(f)

        # 如果JSON没有顶层prompt键，则包装一层
        # 这是新版ComfyUI API的格式要求
        if "prompt" not in api_json:
            api_json = {
                "prompt": api_json,
                # 每次生成唯一的client_id，避免ComfyUI混淆不同请求
                "client_id": f"ai_huanzhuang_{generate_random_str(10)}"
            }
        return api_json
    except json.JSONDecodeError as e:
        raise Exception(f"API JSON格式错误：{str(e)}")
    except Exception as e:
        raise Exception(f"加载JSON失败：{str(e)}")


def upload_image_to_comfyui(image_path: str) -> str:
    """上传图片到ComfyUI服务，返回ComfyUI中的图片名称"""
    try:
        with open(image_path, "rb") as f:
            response = requests.post(
                f"{COMFYUI_URL}/upload/image",
                files={"image": f},
                timeout=60
            )
        response.raise_for_status()
        return response.json()["name"]
    except Exception as e:
        raise Exception(f"上传图片失败：{str(e)}")


def update_workflow_seed(api_json: dict, seed: int) -> dict:
    """遍历工作流所有节点，替换固定seed为随机值，确保每次生成结果不同"""
    prompt = api_json["prompt"]

    for node_id, node_data in prompt.items():
        if "inputs" not in node_data:
            continue

        # 替换KSampler节点的seed
        if "seed" in node_data["inputs"]:
            prompt[node_id]["inputs"]["seed"] = seed
            if "subseed" in node_data["inputs"]:
                prompt[node_id]["inputs"]["subseed"] = random.randint(0, 0xFFFFFFFFFFFFFFFF)
            if "subseed_strength" in node_data["inputs"]:
                prompt[node_id]["inputs"]["subseed_strength"] = round(random.uniform(0.0, 1.0), 4)

        # 替换RandomNoise节点的noise_seed
        if "noise_seed" in node_data["inputs"]:
            prompt[node_id]["inputs"]["noise_seed"] = seed

        # 小幅随机化Flux2Scheduler的步数，增加生成多样性
        if node_data.get("class_type") == "Flux2Scheduler":
            if "steps" in node_data["inputs"]:
                base_steps = node_data["inputs"]["steps"]
                prompt[node_id]["inputs"]["steps"] = max(4, base_steps + random.choice([-2, -1, 0, 1, 2]))

    # 为每次请求生成唯一prompt_id，防止ComfyUI读取缓存结果
    api_json["prompt_id"] = str(uuid4())
    return api_json


def process_workflow(task_id: str, api_json: dict, person_img_path: str, clothes_img_path: str):
    """后台执行ComfyUI工作流，轮询等待结果，完成后保存图片"""
    try:
        # 提交工作流到ComfyUI
        response = requests.post(
            f"{COMFYUI_URL}/prompt",
            json=api_json,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        prompt_id = response.json()["prompt_id"]
        logger.info(f"ComfyUI任务ID：{prompt_id} | 自定义任务ID：{task_id}")

        # 轮询等待生成完成，最长等待TASK_TIMEOUT秒
        start_time = time.time()
        while time.time() - start_time < TASK_TIMEOUT:
            try:
                history_response = requests.get(
                    f"{COMFYUI_URL}/history/{prompt_id}",
                    timeout=10
                )
                history_response.raise_for_status()
                history = history_response.json()

                # ComfyUI返回历史记录中包含该prompt_id，说明生成完成
                if prompt_id in history and "outputs" in history[prompt_id]:
                    outputs = history[prompt_id]["outputs"]

                    for node_id, node_data in outputs.items():
                        if "images" in node_data and len(node_data["images"]) > 0:
                            img_info = node_data["images"][0]

                            # 从ComfyUI下载生成的图片
                            img_url = f"{COMFYUI_URL}/view?filename={img_info['filename']}&subfolder={img_info['subfolder']}"
                            img_data = requests.get(img_url, timeout=30).content

                            # 生成唯一文件名：前缀 + 任务ID + 时间戳 + 随机字符串
                            unique_filename = f"ai_dress_{task_id}_{int(time.time())}_{generate_random_str(10)}.png"
                            img_save_path = os.path.join(OUTPUT_IMAGE_DIR, unique_filename)

                            # 保存图片到本地目录
                            with open(img_save_path, "wb") as f:
                                f.write(img_data)

                            # 更新任务状态为成功
                            task_status[task_id] = {
                                "status": "success",
                                # 返回可供前端访问的相对路径
                                "image_url": f"/generated-images/{unique_filename}",
                                "error": ""
                            }
                            logger.info(f"任务{task_id}生成成功：{img_save_path}")
                            return

            except Exception as e:
                logger.warning(f"轮询任务{task_id}出错：{str(e)}")
                time.sleep(3)
                continue

            time.sleep(2)

        # 超出最大等待时间，标记为失败
        task_status[task_id] = {
            "status": "failed",
            "image_url": "",
            "error": f"生成超时（{TASK_TIMEOUT}秒）"
        }

    except Exception as e:
        error_msg = f"执行工作流失败：{str(e)}"
        task_status[task_id] = {
            "status": "failed",
            "image_url": "",
            "error": error_msg
        }
        logger.error(f"任务{task_id}执行失败：{error_msg}")

    finally:
        # 无论成功失败，最终都清理临时上传文件
        cleanup_temp_files(person_img_path, clothes_img_path)