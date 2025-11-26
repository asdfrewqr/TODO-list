Todo-List 任务管理系统

这是一个基于 FastAPI (后端) 和 Vue 3 (前端) 开发的现代化 Todo-List 网站。该项目不仅实现了标准的待办事项管理功能，还融入了游戏化元素（元气值系统）和视觉动画，旨在提供高效且有趣的任务管理体验。

✨ 功能特性

🛠 基础功能

  任务管理：轻松添加和删除待办事项。

  状态追踪：一键标记任务为完成或未完成。

  列表查看：清晰展示所有待办事项。

🚀 扩展功能

  数据持久化：使用数据库存储，确保数据不丢失。

  任务分类：支持工作、学习、生活等多维度分类管理。

  智能排序：支持按优先级或分类对任务进行排序。

🌟 进阶亮点

  提醒功能：不再错过任何截止日期。

  搜索功能：快速定位特定任务。

  元气值系统：完成任务积攒“元气值”，解锁专属互动动画，让效率管理更具成就感。
  <img width="1241" height="659" alt="image" src="https://github.com/user-attachments/assets/a4c4c288-0ed0-46b7-abf1-79d01d62d3cd" />
  <img width="418" height="308" alt="image" src="https://github.com/user-attachments/assets/63d77174-c1ac-4983-828e-ce3da8ae7732" />


🛠 技术栈

  后端：Python, FastAPI, SQLModel, Uvicorn

  前端：Node.js, Vue 3, TypeScript, Axios, Vite, GSAP (动画库)

开发工具：PyCharm (推荐)

⚙️ 安装与配置指南

1. 获取项目代码

  将 todo-app 文件夹下载或克隆到您的本地计算机。

2. 后端环境配置 (Python)

  确保您已安装 Python 3.10+。在 backend 目录下安装所需依赖：

  pip install fastapi sqlmodel uvicorn



3. 前端环境配置 (Node.js)

确保您已安装 Node.js 和 npm。进入 frontend 目录并安装依赖：

  cd frontend
  npm install
  # 项目依赖包括: vue, typescript, axios, vite, gsap



🔧 PyCharm 运行配置 (后端)

为了在 PyCharm 中便捷地运行后端服务，请按照以下步骤配置 uvicorn：

  在 PyCharm 顶部菜单栏选择 Run -> Edit Configurations...。

  点击左上角的 "+" 号，选择 Python。

按如下参数填写配置：

  Name: FastAPI Backend (或自定义名称)

  Module: 勾选 Module name，并输入 uvicorn

  Parameters: 输入 main:app --reload

  Working directory: 选择项目中的 /backend 目录路径

  点击 OK 保存。

▶️ 启动项目

第一步：运行后端

  在 PyCharm 右上角选择刚才配置好的 FastAPI Backend，点击绿色的 RUN (▶) 按钮。

  成功启动后，后端通常运行在 http://127.0.0.1:8000。

第二步：运行前端

  打开终端（Terminal），进入前端目录并启动开发服务器：

  cd frontend
  npm run dev



成功启动后，控制台将显示访问地址默认为 http://localhost:5173
点击链接即可在浏览器中访问 Todo-List。
