# User Guide / 用户指南

AICodePilot helps developers understand unfamiliar codebases, search project content, ask code questions, inspect Agent steps, and review code evidence.

AICodePilot 用于帮助开发者理解陌生代码库、检索项目内容、进行代码问答、查看 Agent 执行步骤，并审阅回答所依据的代码证据。

## Backend Workflow / 后端流程

The FastAPI backend provides:

FastAPI 后端提供：

1. `GET /api/health`
2. `POST /api/chat`
3. `POST /api/projects/index`
4. `POST /api/projects/search`

Start it locally from `backend`:

从 `backend` 目录本地启动：

```bash
uvicorn app.main:app --reload
```

Open API docs at:

打开 API 文档：

```text
http://localhost:8000/docs
```

## Web Workspace / Web 工作台

Start the frontend from `frontend`:

从 `frontend` 目录启动前端：

```bash
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

The UI is organized as a three-column engineering workspace:

界面采用三栏工程化工作台布局：

- **Left rail / 左侧控制区**：Model Hub, Codebase Import, and future Agent capability shortcuts. 模型中心、代码库导入和后续 Agent 能力入口。
- **Center / 中间主区**：Agent Chat with Markdown rendering, code highlighting, avatars, and multiline input. Agent 对话，支持 Markdown、代码高亮、头像和多行输入。
- **Right rail / 右侧证据区**：Agent Steps and Code Evidence for the latest response. 展示最新回答的执行步骤和代码证据。

## Model Hub / 模型中心

- **Domestic / 国内模型**：DeepSeek V4-Pro is available and selected by default. DeepSeek V4-Flash, GLM-4.6, Qwen3.6 Plus, and Qwen3 Coder Plus are shown as coming-soon options.
- **Global / 国外模型**：GPT-5.2 is available through the OpenAI provider. GPT-4o and Claude options are shown as coming-soon options.

Current backend provider support is limited to OpenAI and DeepSeek. Coming-soon cards are disabled until their backend provider modules are implemented.

当前后端真实可用 Provider 为 OpenAI 和 DeepSeek。GLM、Qwen、Claude 等卡片为待接入状态，后端 Provider 完成前不可点击。

## Codebase Import / 代码库导入

There are two ways to prepare a project:

项目准备有两种方式：

1. **Open local folder / 打开本地文件夹**：uses browser folder authorization to scan file names, infer a local language mix, and show a Project Summary preview. 浏览器授权读取文件名，用于生成前端项目摘要预览。
2. **Backend-visible path / 后端可访问路径**：sends a path to the backend for real RAG indexing through `/api/projects/index`. 将路径发送给后端，执行真实 RAG 索引。

When running with Docker, the browser is on Windows but the backend runs inside a Linux container. Set these values in `.env`:

Docker 运行时，浏览器在 Windows，后端在 Linux 容器内。建议在 `.env` 中配置：

```env
PROJECTS_HOST_ROOT=D:/code/my_projects
PROJECTS_CONTAINER_ROOT=/workspace
NEXT_PUBLIC_DEFAULT_PROJECT_PATH=/workspace
```

Then enter either a host path under `PROJECTS_HOST_ROOT`:

然后可以输入宿主机路径：

```text
D:/code/my_projects/AI_Projects/AICodePilot
```

or the mapped container path:

也可以输入映射后的容器路径：

```text
/workspace/AI_Projects/AICodePilot
```

After indexing succeeds, the Project Summary modal shows project name, purpose, tech stack, architecture, structure overview, file/chunk counts, and language ratio bars.

索引成功后，Project Summary 弹窗会展示项目名称、用途、技术栈、主要架构、结构概览、文件/Chunk 数量和语言比例图。

## Chat Workflow / 对话流程

1. Sign in using the frontend auth mock. 使用前端演示认证登录或注册。
2. Choose a supported model card. 选择可用模型卡片。
3. Open a folder for preview or enter a backend-visible path. 打开本地文件夹预览，或输入后端可访问路径。
4. Index the codebase. 索引代码库。
5. Ask a question in the central chat panel. 在中间对话区提问。
6. Use `Shift + Enter` for line breaks. Press `Enter` to send. 使用 `Shift + Enter` 换行，按 `Enter` 发送。
7. Review the Markdown answer, code blocks, collapsible execution summary, Agent Steps, and Code Evidence. 查看 Markdown 答案、代码块、折叠执行摘要、执行步骤和代码证据。

## Theme and Language / 主题与语言

The top bar supports:

顶部栏支持：

- Light/dark theme switching, with light mode as the default. 深色/浅色切换，默认浅色。
- Simplified Chinese and English UI switching. 简体中文/英文切换。

Preferences are stored in browser `localStorage`.

偏好设置保存在浏览器 `localStorage` 中。

## Recommended Questions / 推荐问题

```text
请分析这个项目的 Agent 主流程在哪里？
配置是在哪里读取的？
工具注册逻辑是怎么实现的？
哪些文件定义了 FastAPI 路由？
Generate tests for the Agent executor.
Analyze this error log and suggest a fix.
```

## Boundaries / 当前边界

- Browser folder access is permission-based and cannot grant the backend direct access to arbitrary local paths.
- Real backend authentication is not implemented yet; the current auth UI is a frontend mock for the product workflow.
- GLM, Qwen, and Claude require backend provider implementations before they can be used for real requests.

- 浏览器文件夹授权只能用于前端预览，不能让后端直接访问任意本地路径。
- 后端真实认证尚未实现；当前登录/注册/资料设置是前端产品流程演示。
- GLM、Qwen、Claude 需要实现后端 Provider 后才能用于真实模型请求。
