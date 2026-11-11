"""Windows 安装包在本机只做静态检查；真正安装在 windows-latest 上跑。"""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "packaging" / "windows"


def _load_explain():
	path = WINDOWS / "explain_doctor.py"
	spec = importlib.util.spec_from_file_location("explain_doctor", path)
	assert spec and spec.loader
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def test_installer_files_exist_and_use_utf8_console() -> None:
	bat = (WINDOWS / "安装.bat").read_bytes()
	assert bat.startswith(b"\xef\xbb\xbf")
	text = bat.decode("utf-8-sig")
	assert "\r\n" in text
	for token in (
		"chcp 65001",
		"PYTHONUTF8=1",
		"PYTHONIOENCODING=utf-8",
		r"%LOCALAPPDATA%\HRAssistant",
		"patchright install chromium",
		"boss.cmd",
		"--json doctor",
		"explain_doctor.py",
		"BOSS_INSTALL_NONINTERACTIVE",
	):
		assert token in text
	assert ".boss-agent" not in text
	assert "rmdir" not in text.lower()


def test_hr_readme_stays_plain_and_agent_note_lists_commands() -> None:
	hr = (WINDOWS / "使用说明.txt").read_text(encoding="utf-8-sig")
	assert "招聘助手" in hr
	assert "扫码" in hr
	assert "securityId" not in hr
	assert "dry-run" not in hr
	agent = (WINDOWS / "给Agent的说明.md").read_text(encoding="utf-8")
	for snippet in (
		"boss status",
		"boss login",
		"boss hr whoami",
		"boss hr candidates",
		"boss hr recommendations",
		"boss hr greet",
		"boss hr location <friend_id> --dry-run",
		"--yes",
		"boss agent stop",
	):
		assert snippet in agent


def test_explain_doctor_uses_plain_language() -> None:
	explain = _load_explain().explain
	text = explain(
		{
			"ok": True,
			"data": {
				"auth_state": "missing",
				"checks": [
					{"name": "patchright_chromium", "status": "warn"},
					{"name": "network", "status": "ok"},
					{"name": "cdp_risk_lock", "status": "ok"},
				],
			},
		}
	)
	assert "已经装好" in text
	assert "还没有登录" in text
	assert "浏览器内核" in text
	assert "securityId" not in text
	failed = explain({"ok": False, "error": {"message": "自检中断"}})
	assert "自检没有完成" in failed
	assert "自检中断" in failed


def test_windows_workflow_builds_on_windows_and_is_read_only() -> None:
	text = (ROOT / ".github" / "workflows" / "windows-installer.yml").read_text(encoding="utf-8")
	assert "windows-latest" in text
	assert "release/windows-installer" in text
	assert "persist-credentials: false" in text
	assert "pull_request_target" not in text
	assert "HRAssistant-windows" in text
	assert "ci_verify.ps1" in text
	assert "secrets." not in text
