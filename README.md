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

1. 创建并激活 Python 虚拟环境
2. 安装 requirements.txt
3. 根据 .env.example 配置环境变量
4. 运行 `uvicorn app.main:app --reload`
5. 打开 `/docs`