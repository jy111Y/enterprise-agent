import os
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel, Field

project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")


api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model = os.getenv("LLM_MODEL")

if not api_key or not model:
    raise RuntimeError("缺少 LLM_API_KEY 或 LLM_MODEL")

client_args = {"api_key": api_key}
if base_url:
    client_args["base_url"] = base_url

client = OpenAI(**client_args)

# response = client.chat.completions.create(
#     model=model,
#     messages=[
#         {
#             "role": "system",
#             "content": "你是一名企业知识库助手。回答应简洁、准确。",
#         },
#         {
#             "role": "user",
#             "content": "请用三句话解释什么是AI Agent。",
#         },
#     ],
#     temperature=0.2,
# )

# print(response.choices[0].message.content)

# stream = client.chat.completions.create(
#     model=model,
#     messages=[
#         {
#             "role": "system",
#             "content": (
#                 "你是一名企业知识库助手。"
#                 "如果缺少资料，必须明确说明无法确认。"
#             ),
#         },
#         {
#             "role": "user",
#             "content": "AI Agent 与普通聊天机器人有什么区别",
#         },
#     ],
#     temperature=0.2,
#     stream=True,
# )

# for chunk in stream:
#     content = chunk.choices[0].delta.content
#     if content:
#         print(content, end="", flush=True)

# print()

app = FastAPI(title="Enterprise Agent", version="0.1.0")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


def generate_text(message: str) -> Iterator[str]:
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是一名可靠的企业知识库助手。",
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        temperature=0.2,
        stream= True,
    )

    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest) -> StreamingResponse:
    try:
        return StreamingResponse(
            generate_text(request.message),
            media_type="text/plain; charset=utf-8",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="模型服务调用失败") from exc