import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# 从配置文件导入目录路径常量
from app.config.settings import OUTPUT_IMAGE_DIR, STATIC_DIR

# 从路由文件导入router
from app.api.routes import router

import os

# 初始化必要目录，不存在则自动创建
os.makedirs(OUTPUT_IMAGE_DIR, exist_ok=True)
os.makedirs("./temp_uploads", exist_ok=True)

# 配置全局日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(title="AI换装后端")

# 允许跨域，开发阶段放开所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载生成图片目录，让前端可以通过URL直接访问图片
app.mount(
    "/generated-images",
    StaticFiles(directory=OUTPUT_IMAGE_DIR, html=False),
    name="generated-images"
)

# 挂载前端静态文件目录
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR, html=True),
    name="static"
)

# 注册API路由，所有路由自动带上/api前缀
app.include_router(router)


# 根路径重定向到前端页面
@app.get("/")
async def redirect_to_frontend():
    return RedirectResponse(url="/static/index.html")


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("✅ AI换装后端启动成功")
    logger.info(f"🔗 后端访问地址：http://127.0.0.1:8000")
    logger.info("="*60)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )