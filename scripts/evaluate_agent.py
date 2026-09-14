import json
import sys
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.main import agent_service

questions_path = (
    project_root
    / "tests"
    / "agent_eval_questions.json"
)    #评测问题所在文件的地址

report_path = (
    project_root
    / "reports"
    / "agent_eval_results.json"
)     #评测报告输出所在文件的地址

def normalize_text(text: str) -> str:
    """去掉空格、换行并统一常见标点。"""
    return(
        "".join(text.lower().split())
        .replace(":", ":")
    )
    

def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    question = case["question"]
    expected_tools = case["expected_tools"]
    expected_keywords = case["expected_keywords"]

    try:
        result = agent_service.chat(question)

        answer = result["answer"]
        trace = result["trace"]

        actual_tools = [
            item["tool_name"]    #遍历trace列表，每次都赋一个元素给item
            for item in trace
            if "tool_name" in item
        ]

        # tool_passed = all(
        #     tool_name in actual_tools
        #     for tool_name in expected_tools
        # )

        # if not expected_tools:
        #     tool_passed = len(actual_tools) ==0

        tool_passed = (
            set(actual_tools)
            == set(expected_tools)
        )

        """修改之后更加严格，强制要求期望工具和实际工具完全一样，旧代码可以允许实际工具多余期望工具"""

        # if expected_keywords:
        #     answer_passed = all(
        #         keyword in answer
        #         for keyword in expected_keywords
        #     )

        # else:
        #     answer_passed = bool(answer.strip())
        
        if expected_keywords:
            normalized_answer = normalize_text(answer)
            keyword_aliases = case.get(
                "keyword_aliases",
                {},
            )

            answer_passed = all(
                any(
                    normalize_text(candidate)
                    in normalized_answer
                    for candidate in keyword_aliases.get(
                        keyword,
                        [keyword],
                    )
                )
                for keyword in expected_keywords
            )
        else:
            answer_passed = bool(answer.strip())



        return {
            "id": case["id"],
            "category": case["category"],    #类别
            "question": question,
            "expected_tools": expected_tools,
            "actual_tools": actual_tools,
            "expected_keywords": expected_keywords,
            "answer": answer,
            "tool_passed": tool_passed,
            "answer_passed": answer_passed,
            "passed": tool_passed and answer_passed,
            "error": None,
        }

    except Exception as exc:
        return{
            "id": case["id"],
            "category": case["category"],
            "question": question,
            "expected_tools": expected_tools,
            "actual_tools": [],
            "expected_keywords": expected_keywords,
            "answer": "",
            "tool_passed": False,
            "answer_passed": False,
            "passed": False,
            "error": str(exc),
        }

def main() -> None:
    cases = json.loads(
        questions_path.read_text(encoding="utf-8")
    )

    results = [
        evaluate_case(case)
        for case in cases
    ]

    total = len(results)

    passed_count = sum(
        result["passed"]
        for result in results
    )

    tool_passed_count = sum(
        result["tool_passed"]
        for result in results
    )

    answer_passed_count = sum(
        result["answer_passed"]
        for result in results
    )

    summary = {
        "total": total,
        "passed": passed_count,
        "overall_accuracy": round(          #综合通过率
            passed_count / total,
            4,                       #这个4是保留四位小数
        ),
        "tool_accuracy": round(
            tool_passed_count / total,
            4,
        ),
        "answer_accuracy": round(
            answer_passed_count / total,
            4,
        ),
    }

    report = {
        "summary": summary,     #汇总统计
        "results": results,      #每道题详细结果
    }

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,        #中文正常显示
            indent=2,                   #格式化输出，缩进2空格，方便阅读
        ), 
        encoding="utf-8",
    )

    print("\nAgent评测结果")
    print(f"总题数：{total}")
    print(f"完全通过：{passed_count}")
    print(
        "工具准确率："
        f"{summary['tool_accuracy']:.1%}"
    )
    print(
        "答案准确率："
        f"{summary['answer_accuracy']:.1%}"
    )
    print(
        "综合通过率："
        f"{summary['overall_accuracy']:.1%}"
    )
    print(f"详细报告：{report_path}")


if __name__ == "__main__":
    main()

    