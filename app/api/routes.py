import os
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

# 从配置文件导入校验常量
from app.config.settings import (
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE,
    PERSON_IMAGE_NODE_ID,
    CLOTHES_IMAGE_NODE_ID
)
# 从服务层导入核心业务函数
from app.services.comfyui_service import (
    task_status,
    load_comfyui_api_json,
    upload_image_to_comfyui,
    update_workflow_seed,
    process_workflow
)
from app.utils.file_utils import (
    generate_random_str,
    generate_random_seed,
    generate_task_id
)

logger = logging.getLogger(__name__)

# 创建路由器，所有接口都注册到这个router上
# 在main.py中统一挂载，prefix="/api"表示所有路由自动加上/api前缀
router = APIRouter(prefix="/api")


@router.get("/task/{task_id}", summary="查询生成任务状态")
async def get_task_status(task_id: str):
    """根据任务ID查询当前生成状态"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return JSONResponse({
        "code": 200,
        "data": task_status[task_id]
    })


@router.post("/generate", summary="上传人物+服装图片生成换装结果")
async def generate_image(
    background_tasks: BackgroundTasks,
    person_img: UploadFile = File(..., description="人物图片"),
    clothes_img: UploadFile = File(..., description="服装图片")
):
    """接收两张图片，提交换装任务，返回任务ID供前端轮询"""
    
    # 1. 生成唯一任务ID，初始化任务状态
    task_id = generate_task_id()
    task_status[task_id] = {
        "status": "pending",
        "image_url": "",
        "error": ""
    }

    # 2. 校验文件格式和大小
    if person_img.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"人物图片格式不支持：{person_img.content_type}，请上传jpg/png/webp"
        )
    if clothes_img.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"服装图片格式不支持：{clothes_img.content_type}，请上传jpg/png/webp"
        )

    person_img_data = await person_img.read()
    if len(person_img_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="人物图片超过10MB限制")

    clothes_img_data = await clothes_img.read()
    if len(clothes_img_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="服装图片超过10MB限制")

    # 3. 保存上传图片到临时目录
    try:
        # 文件名加入task_id和随机字符串，避免多用户同时上传时文件名冲突
        person_filename = f"person_{task_id}_{generate_random_str(6)}_{person_img.filename}"
        clothes_filename = f"clothes_{task_id}_{generate_random_str(6)}_{clothes_img.filename}"

        person_img_path = os.path.join("./temp_uploads", person_filename)
        clothes_img_path = os.path.join("./temp_uploads", clothes_filename)

        with open(person_img_path, "wb") as f:
            f.write(person_img_data)
        with open(clothes_img_path, "wb") as f:
            f.write(clothes_img_data)

    except Exception as e:
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["error"] = f"保存上传图片失败：{str(e)}"
        raise HTTPException(status_code=500, detail=task_status[task_id]["error"])

    # 4. 加载工作流JSON（每次重新加载，避免缓存）
    api_json = load_comfyui_api_json()

    # 5. 上传图片到ComfyUI
    person_img_name = upload_image_to_comfyui(person_img_path)
    clothes_img_name = upload_image_to_comfyui(clothes_img_path)

    # 6. 替换工作流中的图片节点参数
    if PERSON_IMAGE_NODE_ID in api_json["prompt"]:
        api_json["prompt"][PERSON_IMAGE_NODE_ID]["inputs"]["image"] = person_img_name
    else:
        raise HTTPException(status_code=500, detail=f"工作流中未找到人物图片节点（ID:{PERSON_IMAGE_NODE_ID}）")

    if CLOTHES_IMAGE_NODE_ID in api_json["prompt"]:
        api_json["prompt"][CLOTHES_IMAGE_NODE_ID]["inputs"]["image"] = clothes_img_name
    else:
        raise HTTPException(status_code=500, detail=f"工作流中未找到服装图片节点（ID:{CLOTHES_IMAGE_NODE_ID}）")

    # 7. 生成随机种子并更新工作流
    random_seed = generate_random_seed()
    api_json = update_workflow_seed(api_json, random_seed)
    logger.info(f"任务{task_id}使用随机种子：{random_seed}")

    # 8. 后台异步执行工作流，不阻塞当前请求
    background_tasks.add_task(
        process_workflow, task_id, api_json, person_img_path, clothes_img_path
    )

    # 9. 立即返回任务ID，前端凭此轮询状态
    return JSONResponse({
        "code": 200,
        "message": "任务已提交，正在生成中...",
        "data": {
            "task_id": task_id,
            "seed": random_seed
        }
    })