"""Tests for SessionStore: get_or_create, TTL eviction, LRU capacity, concurrency.

Covers the T-1 requirement: thread-safe per-conversation memory registry.
"""

import threading
import time

import pytest

from app.memory.session_store import SessionStore, get_session_store
from app.memory.conversation_memory import ConversationMemory


class TestSessionStoreGetOrCreate:
    def test_returns_conversation_memory(self) -> None:
        store = SessionStore()
        memory = store.get_or_create("conv-1")
        assert isinstance(memory, ConversationMemory)

    def test_same_id_returns_same_instance(self) -> None:
        store = SessionStore()
        first = store.get_or_create("conv-1")
        second = store.get_or_create("conv-1")
        assert first is second

    def test_different_ids_return_different_instances(self) -> None:
        store = SessionStore()
        a = store.get_or_create("conv-a")
        b = store.get_or_create("conv-b")
        assert a is not b

    def test_empty_id_raises(self) -> None:
        store = SessionStore()
        with pytest.raises(ValueError, match="cannot be empty"):
            store.get_or_create("  ")

    def test_whitespace_id_is_stripped(self) -> None:
        store = SessionStore()
        m1 = store.get_or_create("  conv-x  ")
        m2 = store.get_or_create("conv-x")
        assert m1 is m2

    def test_conversation_id_propagated_to_memory(self) -> None:
        store = SessionStore()
        memory = store.get_or_create("my-session")
        assert memory.conversation_id == "my-session"


class TestSessionStoreDrop:
    def test_drop_removes_session(self) -> None:
        store = SessionStore()
        store.get_or_create("conv-1")
        assert store.active_count() == 1
        store.drop("conv-1")
        assert store.active_count() == 0

    def test_drop_nonexistent_is_noop(self) -> None:
        store = SessionStore()
        store.drop("does-not-exist")  # should not raise

    def test_after_drop_new_instance_created(self) -> None:
        store = SessionStore()
        first = store.get_or_create("conv-1")
        store.drop("conv-1")
        second = store.get_or_create("conv-1")
        assert first is not second


class TestSessionStoreTTL:
    def test_expired_session_evicted_on_next_access(self) -> None:
        store = SessionStore(ttl_seconds=0.01)
        store.get_or_create("conv-1")
        assert store.active_count() == 1
        time.sleep(0.05)
        # Trigger eviction by creating a new session
        store.get_or_create("conv-2")
        assert store.active_count() == 1  # only conv-2 survives

    def test_fresh_session_survives_ttl_check(self) -> None:
        store = SessionStore(ttl_seconds=60)
        store.get_or_create("conv-1")
        store.get_or_create("conv-2")
        assert store.active_count() == 2


class TestSessionStoreLRUCapacity:
    def test_oldest_session_evicted_when_at_capacity(self) -> None:
        store = SessionStore(max_sessions=2)
        store.get_or_create("conv-a")
        time.sleep(0.001)
        store.get_or_create("conv-b")
        time.sleep(0.001)
        # conv-a is LRU; adding conv-c should evict it
        store.get_or_create("conv-c")
        assert store.active_count() == 2

    def test_recently_accessed_session_not_evicted(self) -> None:
        store = SessionStore(max_sessions=2)
        store.get_or_create("conv-a")
        time.sleep(0.001)
        store.get_or_create("conv-b")
        # Re-access conv-a to make it MRU
        time.sleep(0.001)
        store.get_or_create("conv-a")
        time.sleep(0.001)
        # Adding conv-c should evict conv-b (now LRU)
        store.get_or_create("conv-c")
        assert store.active_count() == 2
        # conv-a must still be present
        assert store.get_or_create("conv-a") is not None


class TestSessionStoreConcurrency:
    def test_concurrent_same_id_returns_same_instance(self) -> None:
        """Multiple threads accessing the same conversation_id must get the same object."""

        store = SessionStore()
        results: list[ConversationMemory] = []
        errors: list[Exception] = []

        def worker() -> None:
            try:
                results.append(store.get_or_create("shared-conv"))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors, f"Concurrent access raised: {errors}"
        assert len(results) == 20
        # All threads must have received the exact same instance
        first = results[0]
        assert all(m is first for m in results)

    def test_concurrent_different_ids_no_error(self) -> None:
        store = SessionStore()
        errors: list[Exception] = []

        def worker(conv_id: str) -> None:
            try:
                store.get_or_create(conv_id)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(f"conv-{i}",)) for i in range(50)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors, f"Concurrent creation raised: {errors}"
        assert store.active_count() == 50


class TestGetSessionStoreSingleton:
    def test_returns_same_singleton(self) -> None:
        s1 = get_session_store()
        s2 = get_session_store()
        assert s1 is s2

    def test_invalid_ttl_raises(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            SessionStore(ttl_seconds=0)

    def test_invalid_max_sessions_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 1"):
            SessionStore(max_sessions=0)
