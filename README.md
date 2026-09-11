# Enterprise Agent

面向企业知识库问答和业务任务执行的 AI Agent。

## day1进度

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

data 目录中的内容为虚构的测试资料，不代表真实公司制度。


## day2进度

- [x] 基础模型调用
- [x] 流式响应
- [x] FastAPI 接口
- [x] RAG 文档检索
- [ ] Tool Calling
- [ ] 状态与记忆
- [ ] Agent 评测
- [ ] Docker 部署

## RAG 流程

1. 加载本地企业制度测试文档
2. 按固定长度和重叠区域切分文档
3. 使用中文字符 n-gram TF-IDF 建立稀疏向量索引
4. 根据用户问题检索 Top-K 相关片段
5. 将检索资料和问题共同发送给大模型
6. 返回答案、来源文件和检索分数

## 测试数据声明

`data` 目录中的企业制度内容均为虚构测试数据，不代表任何真实公司的内部制度。

## 当前限制

- 当前使用 TF-IDF 词面检索，不能充分理解同义词和复杂语义
- 知识库更新后需要重新构建索引
- 暂未实现重排、混合检索和语义 Embedding
- 暂未建立完整的答案质量评测体系

