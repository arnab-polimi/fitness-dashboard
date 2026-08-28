from subprocess import CompletedProcess

from src.ingestion.garmin_sync_runner import GarminSyncRunner


def test_safe_tail_hides_sensitive_lines():
    tail = GarminSyncRunner._safe_tail("ready\npassword=hunter2\nfinished")

    assert tail == "ready\nfinished"


def test_run_uses_cmd_and_returns_success(tmp_path, monkeypatch):
    script = tmp_path / "sync.bat"
    script.write_text("@echo off", encoding="utf-8")
    calls = {}

    def fake_run(*args, **kwargs):
        calls["args"] = args
        calls["kwargs"] = kwargs
        return CompletedProcess(args[0], 0, stdout="download complete", stderr="")

    monkeypatch.setattr("src.ingestion.garmin_sync_runner.subprocess.run", fake_run)

    result = GarminSyncRunner.run(str(script))

    assert result["status"] == "success"
    assert result["summary"] == "download complete"
    assert calls["args"][0][:3] == ["cmd.exe", "/d", "/c"]
    assert calls["kwargs"]["cwd"] == str(tmp_path)
