from app.memory import ConversationMemory


def test_add_and_read_messages(tmp_path):
    memory = ConversationMemory(
        tmp_path / "memory.db"
    )

    memory.add_message(
        "session-001",
        "user",
        "你好",
    )

    memory.add_message(
        "session-001",
        "assistant",
        "你好，有什么可以帮助你？",
    )

    messages = memory.get_recent_messages(
        "session-001"
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "你好"
    assert messages[1]["role"] == "assistant"


def test_sessions_are_isolated(tmp_path):
    memory = ConversationMemory(
        tmp_path / "memory.db"
    )

    memory.add_message(
        "session-a",
        "user",
        "用户A的问题",
    )

    memory.add_message(
        "session-b",
        "user",
        "用户B的问题",
    )

    session_a_messages = (
        memory.get_recent_messages("session-a")
    )

    session_b_messages = (
        memory.get_recent_messages("session-b")
    )

    assert len(session_a_messages) == 1
    assert len(session_b_messages) == 1

    assert (
        session_a_messages[0]["content"]
        == "用户A的问题"
    )

    assert (
        session_b_messages[0]["content"]
        == "用户B的问题"
    )


def test_recent_message_limit(tmp_path):
    memory = ConversationMemory(
        tmp_path / "memory.db"
    )

    for index in range(10):
        memory.add_message(
            "session-001",
            "user",
            f"消息{index}",
        )

    messages = memory.get_recent_messages(
        "session-001",
        limit=3,
    )

    assert len(messages) == 3
    assert messages[0]["content"] == "消息7"
    assert messages[2]["content"] == "消息9"


def test_clear_session(tmp_path):
    memory = ConversationMemory(
        tmp_path / "memory.db"
    )

    memory.add_message(
        "session-001",
        "user",
        "需要删除的消息",
    )

    deleted_count = memory.clear_session(
        "session-001"
    )

    messages = memory.get_all_messages(
        "session-001"
    )

    assert deleted_count == 1
    assert messages == []