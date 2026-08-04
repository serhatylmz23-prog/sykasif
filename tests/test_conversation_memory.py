from syk_jarmin.conversation_memory import (
    ConversationMemory,
)


def test_hafiza_mesajlari_sinirlar():
    memory = ConversationMemory(
        maximum_messages_per_session=2
    )

    memory.create_session(
        "MEMORY-001"
    )

    memory.append(
        session_id="MEMORY-001",
        role="user",
        content="bir",
    )

    memory.append(
        session_id="MEMORY-001",
        role="assistant",
        content="iki",
    )

    memory.append(
        session_id="MEMORY-001",
        role="user",
        content="üç",
    )

    session = memory.get_session(
        "MEMORY-001"
    )

    assert len(session.messages) == 2

    assert (
        session.messages[0].content
        == "iki"
    )

    assert len(
        memory.snapshot()[
            "snapshot_sha256"
        ]
    ) == 64