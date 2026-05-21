# AI 换装工具

基于 ComfyUI 工作流的 AI 换装 Web 应用。上传人物图片和服装图片，自动生成换装效果图。

---

## 项目架构

```
AI_dress/
├── app/
│   ├── api/
│   │   └── routes.py        # 路由层：接收请求、参数校验、返回响应
│   ├── services/
│   │   └── comfyui_service.py  # 服务层：核心业务逻辑，与ComfyUI交互
│   ├── utils/
│   │   └── file_utils.py    # 工具层：文件操作、随机数生成等通用函数
│   └── config/
│       └── settings.py      # 配置层：读取环境变量，集中管理所有常量
├── static/
│   └── index.html           # 前端页面
├── generated_images/        # 生成图片保存目录（自动创建）
├── temp_uploads/            # 临时上传目录（自动创建）
├── .env                     # 环境变量配置（不上传至GitHub）
├── main.py                  # 应用入口
└── requirements.txt         # 项目依赖
```

---

## 技术栈

- **后端**：Python / FastAPI / Uvicorn
- **图像生成**：ComfyUI（本地部署）
- **前端**：原生 HTML / CSS / JavaScript
- **任务处理**：FastAPI BackgroundTasks（异步后台任务）

---

## 功能说明

- 上传人物图片 + 服装图片，提交换装任务
- 后端异步调用 ComfyUI 工作流生成图片
- 前端轮询任务状态，生成完成后自动展示结果
- 支持将生成图片保存到本地

---

## 本地部署

### 环境要求

- Python 3.10+
- ComfyUI（本地运行，需 GPU，显存 6GB 及以上）
- Miniconda 或 venv 虚拟环境（推荐）

### 安装步骤

**1. 克隆项目**

```bash
git clone https://github.com/gentlehhiloshi-dotcom/AI_dress.git
cd AI_dress
```

**2. 创建并激活虚拟环境**

```bash
conda create -n ai_dress python=3.10
conda activate ai_dress
```

**3. 安装依赖**

```bash
pip install -r requirements.txt
```

**4. 配置环境变量**

在项目根目录新建 `.env` 文件，填入以下内容：

```
COMFYUI_URL=http://127.0.0.1:8188
API_JSON_PATH=你的工作流JSON文件绝对路径
OUTPUT_IMAGE_DIR=./generated_images
STATIC_DIR=./static
```

**5. 下载 ComfyUI 所需模型**

将以下模型下载后放入 ComfyUI 对应目录：

| 模型 | 存放目录 | 下载地址 |
|---|---|---|
| `flux-2-klein-4b.safetensors` | `ComfyUI/models/unet/` | [下载](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/resolve/main/flux-2-klein-4b.safetensors?download=true) |
| `qwen_3_4b.safetensors` | `ComfyUI/models/text_encoders/` | [下载](https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors?download=true) |
| `flux2-vae.safetensors` | `ComfyUI/models/vae/` | [下载](https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors?download=true) |

**6. 导入工作流**

启动 ComfyUI 后，将项目提供的工作流 JSON 文件导入，确认各节点模型路径正确。

**7. 配置工作流 JSON 路径**

将工作流 JSON 文件的绝对路径填入 `.env` 的 `API_JSON_PATH` 字段。

**8. 启动后端服务**

确保 ComfyUI 已在本地运行，默认端口 `8188`。

**9. 启动后端服务**

```bash
python main.py
```

**10. 访问应用**

打开浏览器访问：[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 使用方法

1. 在左侧上传区域点击上传**人物图片**
2. 在右侧上传区域点击上传**服装图片**
3. 点击**开始生成**按钮提交任务
4. 等待生成完成（通常需要数十秒），结果自动展示
5. 点击**保存图片到本地**下载生成结果

---

## 注意事项

- `.env` 文件包含本地路径信息，已加入 `.gitignore`，请勿上传至 GitHub
- 生成图片保存在 `generated_images/` 目录，临时上传文件在任务完成后自动清理
- 支持的图片格式：JPG / PNG / WebP，单张图片大小不超过 10MB
- 更换 ComfyUI 工作流时，需同步修改 `app/config/settings.py` 中的 `PERSON_IMAGE_NODE_ID` 和 `CLOTHES_IMAGE_NODE_ID`，节点 ID 可在工作流的 API 格式 JSON 中查找
---

## 后续计划

- [ ] 引入 Redis 替换内存任务状态存储，支持多 Worker 部署
- [ ] 部署至 GPU 云服务器（AutoDL 等平台）
- [ ] 增加历史记录功能
- 更换 ComfyUI 工作流时，需同步修改 `app/config/settings.py` 中的 `PERSON_IMAGE_NODE_ID` 和 `CLOTHES_IMAGE_NODE_ID`，节点 ID 可在工作流的 API 格式 JSON 中查找
---

## 作者

[gentlehhiloshi-dotcom](https://github.com/gentlehhiloshi-dotcom)
