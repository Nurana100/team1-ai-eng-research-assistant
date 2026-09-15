"""Tests for the SQLite storage backend."""

import pytest

from src.storage.repository import SQLiteStorage, StorageBackend


def make_storage(tmp_path) -> SQLiteStorage:
    return SQLiteStorage(str(tmp_path / "history.db"))


def test_sqlite_storage_implements_the_contract():
    assert issubclass(SQLiteStorage, StorageBackend)


def test_abstract_backend_cannot_be_instantiated():
    with pytest.raises(TypeError):
        StorageBackend()


def test_save_then_get_returns_the_same_record(tmp_path):
    storage = make_storage(tmp_path)
    sources = [{"title": "Quantum computing", "url": "https://example.org", "origin": "wikipedia"}]

    query_id = storage.save_query("What is a qubit?", "A qubit is ...", sources)
    record = storage.get_query(query_id)

    assert record["id"] == query_id
    assert record["question"] == "What is a qubit?"
    assert record["answer_text"] == "A qubit is ..."
    assert record["sources"] == sources


def test_get_query_returns_none_for_a_missing_id(tmp_path):
    storage = make_storage(tmp_path)
    assert storage.get_query(999) is None


def test_list_queries_is_newest_first(tmp_path):
    storage = make_storage(tmp_path)
    for i in range(3):
        storage.save_query(f"question {i}", "answer", [])

    questions = [row["question"] for row in storage.list_queries()]
    assert questions == ["question 2", "question 1", "question 0"]


def test_list_queries_honours_the_limit(tmp_path):
    storage = make_storage(tmp_path)
    for i in range(5):
        storage.save_query(f"question {i}", "answer", [])

    assert len(storage.list_queries(limit=2)) == 2


def test_list_queries_is_empty_on_a_fresh_database(tmp_path):
    assert make_storage(tmp_path).list_queries() == []


def test_created_at_is_an_utc_timestamp(tmp_path):
    storage = make_storage(tmp_path)
    query_id = storage.save_query("question", "answer", [])

    assert storage.get_query(query_id)["created_at"].endswith("+00:00")


def test_records_survive_reopening_the_database(tmp_path):
    db_path = str(tmp_path / "history.db")
    query_id = SQLiteStorage(db_path).save_query("question", "answer", [])

    assert SQLiteStorage(db_path).get_query(query_id)["question"] == "question"


def test_missing_parent_directory_is_created(tmp_path):
    storage = SQLiteStorage(str(tmp_path / "does" / "not" / "exist" / "history.db"))
    assert storage.list_queries() == []
