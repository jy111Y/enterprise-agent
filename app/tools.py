import ast
import json
import math
import operator
from typing import Any

from pydantic import BaseModel, Field, ValidationError

class SearchPolicyArgs(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    """查询公司制度用的参数"""

class CalculateArgs(BaseModel):
    expression: str = Field(min_length=1, max_length=100)
    """数学计算时用的参数"""

class LeaveApprovalArgs(BaseModel):
    days: int = Field(ge=1, le=30)
    """请假天数,ge和le限制数值大小,上面的限制长度大小"""

"""这个列表用于告诉大模型有什么工具可以用"""
TOOL_DEFINITIONS = [
    {
        "type": "function",   #函数(function)
        "function": {
            "name": "search_company_policy",
            "description": (
                "查询公司内部制度和员工手册。"
                "当问题涉及远程办公、考勤、请假、报销等公司制度时使用。"
            ),
            "parameters": {   #有哪些参数(parameters)
                "type": "object",
                "properties": {
                    "query": {    #query疑问
                        "type": "string",
                        "description": "需要查询的公司制度问题",
                    }
                },
                "required": ["query"],  #required中列出的必须在调用时提供
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "执行安全的数学计算"
                "当用户要求计算金额、加减乘除或报销总额时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {    #expression表达式
                        "type": "string",
                        "description": "只包含数字、括号和加减乘除符号的表达式",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_leave_approval",
            "description": "根据请假天数查询需要哪一级负责人审批。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",    #int
                        "description": "员工计划请假的天数",
                        "minimum": 1,
                        "maximum": 30,
                    }
                },
                "required": ["days"],
            },
        },
    },
]

BINARY_OPERATORS = {        #ast抽象语法树
    ast.Add: operator.add,    #+
    ast.Sub: operator.sub,    #-
    ast.Mult: operator.mul,   #*
    ast.Div: operator.truediv,   #/
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,   #正号
    ast.USub: operator.neg,   #负号
}
"""左边代表的是ast中的符号标记,仅仅只是标记，无法进行实际运算，必须映射成运算函数进行计算，也就是右边部分"""

def _evaluate_node(node: ast.AST) -> float:   #递归函数
    if isinstance(node, ast.Expression):     #isinstance用来判断这个对象是否是这个类型，比如123是不是int型
        return _evaluate_node(node.body)     #返回expression

    if isinstance(node, ast.Constant):      #检查是常量的节点是不是数字，是就转化为float返回否则报错
        if type(node.value) not in (int, float):
            raise ValueError("表达式中只能包含数字")

        return float(node.value)

    if isinstance(node, ast.BinOp):    #Binary Operation 二元运算,ast.Binop代表运算符节点
        operator_function = BINARY_OPERATORS.get(type(node.op))

        if operator_function is None:
            raise ValueError("只支持加、减、乘、除")

        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)

        return operator_function(left, right)    #返回左右节点通过运算符节点计算得出的答案

    if isinstance(node, ast.UnaryOp):   #一元运算
        operator_function = UNARY_OPERATORS.get(type(node.op))
        """根据运算符类型取正或负函数"""

        if operator_function is None:
            raise ValueError("不支持这种运算符")

        return operator_function(_evaluate_node(node.operand))
    """node.operand是一元运算符的操作数"""
    """因为node.operand可能还是一个Binop,所以需要_evaluate_node对其再次解析"""

    raise ValueError("表达式包含不允许的内容")

def calculate_expression(expression: str) -> float:     #安全的做数学运算
    if len(expression) > 100:
        raise ValueError("表达式过长")

    try:
        tree = ast.parse(expression, mode="eval")   #将字符串解析成AST抽象语法树
        result = _evaluate_node(tree)
    except ZeroDivisionError as exc:     #除0转换成更友好的错误
        raise ValueError("不能除以0") from exc
    except SyntaxError as exc:           #语法错误也转成友好错误
        raise ValueError("数学表达式格式错误") from exc       #except在这里是接住的意思,相当于将错误赋给exc,exc则为错误对象

    if not math.isfinite(result):
        raise ValueError("计算结果无效")

    return round(result, 4)    #round用于保留小数点后几位，如果没有后面的数字，自动四舍五入为整数

def check_leave_approval(days: int) -> dict[str, Any]:    #查询请假审批人
    if days <=1:
        approvers = ["直属负责人"]
    else:
        approvers = ["直属负责人","部门负责人"]

    return{
        "days": days,
        "approvers": approvers,
        "message": f"请假{days}天需要{'和'.join(approvers)}审批。",
    }

class ToolExecutor:    #负责接收大模型返回的工具调用请求，执行对应的函数并返回结果
    def __init__(self, retriever: Any):
        self.retriever = retriever

    def execute(
        self,
        tool_name: str,
        raw_arguments: str,
    ) -> dict[str, Any]:
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            raise ValueError("模型生成的工具参数不是合法JSON") from exc

        if tool_name == "search_company_policy":   #调用search_company_policy来校验参数query是否合法
            validated = SearchPolicyArgs.model_validate(arguments)

            results = self.retriever.search(
                validated.query,
                top_k=3,
            )

            return {
                "query": validated.query,
                "results": [
                    {
                        "chunk_id": result.chunk_id,
                        "source": result.source,
                        "content": result.content,
                        "score": round(result.score, 4),
                    }
                    for result in results
                ],
            }

        if tool_name == "calculate":
            validated = CalculateArgs.model_validate(arguments)

            return{
                "expression": validated.expression,
                "result": calculate_expression(validated.expression),
            }

        if tool_name == "check_leave_approval":
            validated = LeaveApprovalArgs.model_validate(arguments)
            return check_leave_approval(validated.days)    #将validated当做包裹，打开包裹取出days这个物品交给check_leave_approval处理

        raise ValueError(f"不允许调用未知工具：{tool_name}")



# text
# 用户提问
#    ↓
# 大模型分析问题
#    ↓
# 大模型决定调用哪个工具，并生成参数 JSON
#    ↓
# ToolExecutor.execute(tool_name, raw_arguments)
#    ↓
# 解析 JSON → Pydantic 校验 → 调用对应函数
#    ↓
# 返回结果给大模型
#    ↓
# 大模型根据工具结果生成最终回答