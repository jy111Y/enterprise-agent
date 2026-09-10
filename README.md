# Enterprise Agent

面向企业知识库问答和业务任务执行的 AI Agent。

## 当前进度

- [x] 基础模型调用
- [x] 流式响应
- [x] FastAPI 接口
- [ ] RAG 文档检索
- [ ] Tool Calling
- [ ] 状态与记忆
- [ ] Agent 评测
- [ ] Docker 部署

## 启动方法

1. 创建虚拟环境：`python -m venv .venv`
2. 激活虚拟环境：`.venv\Scripts\activate`
3. 安装依赖：`python -m pip install -r requirements.txt`
4. 根据 `.env.example` 创建并配置 `.env`
5. 启动服务：`python -m uvicorn app.main:app --reload`
6. 打开 `http://127.0.0.1:8000/docs`