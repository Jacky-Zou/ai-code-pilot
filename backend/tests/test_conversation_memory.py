from app.memory.conversation_memory import ConversationMemory


def test_memory_stores_messages_in_llm_order() -> None:
    memory = ConversationMemory(max_turns=2, conversation_id="demo")

    user = memory.add_user_message("Where is config loaded?", metadata={"project": "AICodePilot"})
    assistant = memory.add_assistant_message("Configuration is loaded in core/config.py")

    assert user.conversation_id == "demo"
    assert user.metadata == {"project": "AICodePilot"}
    assert assistant.role == "assistant"
    assert memory.to_llm_messages(system_message="You are AICodePilot") == [
        {"role": "system", "content": "You are AICodePilot"},
        {"role": "user", "content": "Where is config loaded?"},
        {"role": "assistant", "content": "Configuration is loaded in core/config.py"},
    ]


def test_memory_keeps_latest_complete_user_turns() -> None:
    memory = ConversationMemory(max_turns=2)

    memory.add_user_message("turn 1")
    memory.add_assistant_message("answer 1")
    memory.add_user_message("turn 2")
    memory.add_tool_message("tool result 2")
    memory.add_assistant_message("answer 2")
    memory.add_user_message("turn 3")

    assert [message.content for message in memory.messages] == [
        "turn 2",
        "tool result 2",
        "answer 2",
        "turn 3",
    ]
    assert memory.summary()["turn_count"] == 2


def test_memory_rejects_invalid_limits_and_empty_content() -> None:
    try:
        ConversationMemory(max_turns=0)
    except ValueError as exc:
        assert "max_turns" in str(exc)
    else:
        raise AssertionError("ConversationMemory should reject max_turns below 1")

    memory = ConversationMemory()
    try:
        memory.add_user_message("   ")
    except ValueError as exc:
        assert "content" in str(exc)
    else:
        raise AssertionError("ConversationMemory should reject blank messages")


def test_memory_clear_removes_history_but_keeps_identity() -> None:
    memory = ConversationMemory(conversation_id="session-1")
    memory.add_user_message("hello")

    memory.clear()

    assert memory.messages == []
    assert memory.summary() == {
        "conversation_id": "session-1",
        "max_turns": 8,
        "message_count": 0,
        "turn_count": 0,
    }
