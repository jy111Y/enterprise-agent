import json
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.tools import TOOL_DEFINITIONS, ToolExecutor

class AgentService:
    def __init__(   #初始化，将client等属性传给self
            self,
            client: OpenAI,
            model: str,
            tool_executor: ToolExecutor,   #工具执行器，负责真正执行工具函数
    ):
        self.client = client        #保存大模型客户端
        self.model = model           #保存模型名称
        self.tool_executor = tool_executor          #保存工具执行器

    def chat(        #agent核心循环
            self,
            user_message: str,     #用户问题
            history: list[dict[str, str]] | None = None,
            max_steps: int = 4,       #最多循环四次
    ) -> dict[str, Any]:             #返回字符串回答和任意格式的工具调用记录
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "你是一名企业AI助手。"
                    "涉及公司制度、考勤、远程办公、请假和报销制度的问题，"
                    "必须调用search_company_policy工具查询后回答。"
                    "涉及数学计算时必须调用calculate工具。"
                    "涉及请假审批人时调用check_leave_approval工具。"
                    "不能伪造工具结果。"
                    "如果工具返回的资料不足，应明确说明无法确认。"
                ),
            },
        ]
        for history_message in history or []:
            role = history_message.get("role")
            content = history_message.get("content")

            if(
                role in ("user", "assistant")
                and isinstance(content, str)
                and content.strip()
            ):
                messages.append(
                    {
                        "role": role,
                        "content": content,
                    }
                )
        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        trace: list[dict[str, Any]] = []      #记录每一步调用了什么工具，参数和结果是什么，方便调试和展示

        for step in range(max_steps):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,      #当前对话历史
                tools=TOOL_DEFINITIONS,     #把可用工具告诉大模型
                tool_choice="auto",       #大模型自动决定是否调用工具
                temperature=0.2,
            )

            assistant_message = response.choices[0].message     #选择第一个候选回答
            tool_calls = assistant_message.tool_calls or []      #调用工具则有工具列表否则就是空列表

            if not tool_calls:
                return {
                    "answer": assistant_message.content or "",
                    "trace": trace,
                }

            assistant_record = {           #如果有工具调用，则记录助手的消息
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,       #工具名
                            "arguments": tool_call.function.arguments,    #参数
                        },
                    }
                    for tool_call in tool_calls
                ],
            }

            messages.append(assistant_record)   #将这个助手record加入到message对话历史中,使对话历史更完整

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments    #raw_arguments原始参数,
                """遍历工具调用"""

                try:
                    tool_result = self.tool_executor.execute(    #调用ToolExecutor.execute执行工具
                        tool_name=tool_name,
                        raw_arguments=raw_arguments,
                    )
                except(
                    ValueError,
                    ValidationError
                ) as exc:
                    tool_result = {
                        "error": str(exc),    #返回调用失败的信息
                    }

                try:
                    parsed_arguments = json.loads(raw_arguments)   #将JSON字符串解析成Python字典，方便记录到trace
                except json.JSONDecodeError:
                    parsed_arguments = {
                        "raw_arguments": raw_arguments,
                    }

                trace.append(
                    {
                        "step": step + 1,
                        "tool_name": tool_name,
                        "arguments": parsed_arguments,
                        "result": tool_result,
                    }
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            tool_result,
                            ensure_ascii=False,    #保证中文正常显示
                        ),
                    }
                )

        return {
            "answer": "Agent达到最大工具调用次数,任务已停止。",
            "trace": trace,
        }



# 用户提问
#    ↓
# 构建 messages（system + user）
#    ↓
# 循环最多 max_steps 次：
#    ├── 调用大模型（带工具定义）
#    ├── 如果模型没有调用工具 → 返回最终答案
#    └── 如果模型调用了工具：
#          ├── 记录助手消息到 messages
#          ├── 对每个工具调用：
#          │     ├── 执行工具（ToolExecutor）
#          │     ├── 捕获异常
#          │     ├── 记录 trace
#          │     └── 把工具结果作为 role=tool 消息加入 messages
#          └── 继续下一轮循环
#    ↓
# 返回最终答案和 trace