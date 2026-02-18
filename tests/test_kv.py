from unittest.mock import patch, call
from click.testing import CliRunner
from kv import cli


def test_ingest_delegates_to_kb_ingest():
    runner = CliRunner()
    with patch("kv._call", return_value=0) as mock_call:
        result = runner.invoke(cli, ["ingest", "run", "--channel", "@foo"])
        mock_call.assert_called_once_with(["kb-ingest", "run", "--channel", "@foo"])


def test_index_delegates_to_kb_indexer():
    runner = CliRunner()
    with patch("kv._call", return_value=0) as mock_call:
        result = runner.invoke(cli, ["index", "run", "--channel", "foo"])
        mock_call.assert_called_once_with(["kb-indexer", "run", "--channel", "foo"])


def test_search_delegates_to_kb_search():
    runner = CliRunner()
    with patch("kv._call", return_value=0) as mock_call:
        result = runner.invoke(cli, ["search", "run", "my query"])
        mock_call.assert_called_once_with(["kb-search", "run", "my query"])


def test_check_runs_all_three():
    runner = CliRunner()
    with patch("kv._call", return_value=0) as mock_call:
        result = runner.invoke(cli, ["check"])
        assert mock_call.call_count == 3
        calls = mock_call.call_args_list
        assert calls[0] == call(["kb-ingest", "check", "--data-dir", "./data"])
        assert calls[1] == call(["kb-indexer", "check", "--qdrant-url", "http://localhost:6333"])
        assert calls[2] == call(["kb-search", "check", "--qdrant-url", "http://localhost:6333"])


def test_check_with_qdrant_url():
    runner = CliRunner()
    with patch("kv._call", return_value=0) as mock_call:
        result = runner.invoke(cli, ["check", "--qdrant-url", "http://custom:1234"])
        calls = mock_call.call_args_list
        assert calls[1] == call(["kb-indexer", "check", "--qdrant-url", "http://custom:1234"])
        assert calls[2] == call(["kb-search", "check", "--qdrant-url", "http://custom:1234"])


def test_check_exits_1_on_failure():
    runner = CliRunner()
    with patch("kv._call", side_effect=[1, 0, 0]):
        result = runner.invoke(cli, ["check"])
        assert result.exit_code == 1


def test_check_exits_0_on_success():
    runner = CliRunner()
    with patch("kv._call", return_value=0):
        result = runner.invoke(cli, ["check"])
        assert result.exit_code == 0
