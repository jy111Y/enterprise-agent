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

## day3进度

- [x] 基础模型调用
- [x] 流式响应
- [x] FastAPI 接口
- [x] RAG 文档检索
- [x] Tool Calling
- [ ] 状态与记忆
- [ ] Agent 评测
- [ ] Docker 部署

## Agent 工具调用
项目实现了一个基于 Function Calling 的企业 AI Agent。
当前支持以下工具：
1. `search_company_policy`
   - 查询员工手册、请假和报销制度
   - 内部使用 TF-IDF 检索
2. `calculate`
   - 计算加减乘除表达式
   - 使用 AST 限制危险代码执行
3. `check_leave_approval`
   - 根据请假天数判断审批负责人

Agent 会将模型返回的工具名称和参数交给 Python 执行，
并把工具执行结果重新发送给模型生成最终回答。

为提高安全性，项目加入了：
- Pydantic 参数校验
- 工具白名单
- 安全数学表达式解析
- 最大工具调用次数
- 工具执行轨迹

## 第三天测试结果

| 测试问题 | 预期工具 | 实际工具 | 是否成功 |
|---|---|---|---|
| 每月远程办公多少天 | search_company_policy | search_company_policy | 成功 |
| 计算三个报销金额 | calculate | calculate | 成功 |
| 请假3天谁审批 | check_leave_approval | check_leave_approval | 成功 |
| 普通自我介绍 | 不调用工具 | 无 | 成功 |
| {"message": "我要请3天假，需要谁审批？"} | check_leave_approval | 无 | 失败 |


经过查找问题，发现是因为输入的问题不符合json格式，导致agent_service.chat() 根本没有被调用，大模型也没有机会提取用户意图
对于一个企业软件来说，不应该让用户去迎合agent输入需求，而是agent需要去理解用户的输入
所以经过改变，加入了用户输入框，使得Agent负责理解自然语言；前端负责把自然语言正确传给Agent。

## day4进度

- [x] 基础模型调用
- [x] 流式响应
- [x] FastAPI 接口
- [x] RAG 文档检索
- [x] Tool Calling
- [x] 状态与记忆
- [ ] Agent 评测
- [ ] Docker 部署

## 多轮会话记忆

项目使用 SQLite 实现 Agent 会话记忆。

主要功能：

- 使用 session_id 隔离不同会话
- 保存用户和AI助手的历史消息
- 每次加载最近10条消息作为上下文
- 支持查看和清除会话记录
- 使用参数化SQL降低SQL注入风险
- SQLite连接按操作创建，避免长期共享连接

### 多轮聊天

POST /agent/session/chat

```json
{
  "session_id": "demo-001",
  "message": "每个月最多可以远程办公多少天？"
}
```

## day5进度

- [x] 基础模型调用
- [x] 流式响应
- [x] FastAPI 接口
- [x] RAG 文档检索
- [x] Tool Calling
- [x] 状态与记忆
- [x] Agent 评测
- [ ] Docker 部署

## Agent评测

项目使用自定义测试集评估以下指标：

- 工具选择准确率
- 关键答案命中率
- 无工具问题处理能力
- 知识不足时的拒答能力

评测脚本：

```bash
python scripts/evaluate_agent.py

根据我的三次测试，平均工具选择命中率为100%，
平均关键答案命中率为86.7%
综合通过率为86.7%
答案命中失败的原因主要是同义词或近义词无法识别，比如9：00和九点，助手判断准确率只能识别九点，
以及无法找到和无法确认，助手也不能识别，所以对于现在这个程序，我认为还需加入同义词近义词识别，避免过于严苛与死板。

## day6进度

- [x] 基础模型调用
- [x] 流式响应
- [x] FastAPI 接口
- [x] RAG 文档检索
- [x] Tool Calling
- [x] 状态与记忆
- [x] Agent 评测
- [x] Docker 部署

## Docker启动

1. 根据 `.env.example` 创建并配置 `.env`
2. 构建并启动服务：

```bash
docker compose up -d --build
```

3. 打开接口文档：

```text
http://127.0.0.1:8000/docs
```

4. 检查服务状态：

```bash
docker compose ps
```

5. 停止服务：

```bash
docker compose down
```

SQLite 数据通过 `./runtime:/app/runtime` 持久化保存。
`.env` 不会被复制到 Docker 镜像中。