"""Windows 上检查浏览器登录状态能不能被读到。不打印任何 Cookie 值，也不登录。"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch


def _sanitize(text: str) -> str:
	collapsed = " ".join(text.split())
	if len(collapsed) > 240:
		collapsed = collapsed[:240] + "..."
	return collapsed


def _browser_exe(name: str) -> str:
	local = os.environ.get("LOCALAPPDATA", "")
	program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
	program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
	candidates = {
		"chrome": [
			Path(program_files) / "Google" / "Chrome" / "Application" / "chrome.exe",
			Path(program_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe",
			Path(local) / "Google" / "Chrome" / "Application" / "chrome.exe",
		],
		"edge": [
			Path(program_files) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
			Path(program_files_x86) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
		],
	}
	for path in candidates.get(name, []):
		if path.is_file():
			return str(path)
	return "missing"


def _local_state(name: str) -> dict[str, bool]:
	local = os.environ.get("LOCALAPPDATA", "")
	relative = {
		"chrome": Path("Google") / "Chrome" / "User Data" / "Local State",
		"edge": Path("Microsoft") / "Edge" / "User Data" / "Local State",
	}
	path = Path(local) / relative[name]
	if not path.is_file():
		return {"file": False, "encrypted_key": False, "app_bound_encrypted_key": False}
	try:
		payload = json.loads(path.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError):
		return {"file": True, "encrypted_key": False, "app_bound_encrypted_key": False}
	os_crypt = payload.get("os_crypt") if isinstance(payload, dict) else None
	if not isinstance(os_crypt, dict):
		os_crypt = {}
	return {
		"file": True,
		"encrypted_key": bool(os_crypt.get("encrypted_key")),
		"app_bound_encrypted_key": bool(os_crypt.get("app_bound_encrypted_key")),
	}


def _cookie_api(name: str) -> str:
	import browser_cookie3

	loader = getattr(browser_cookie3, name, None)
	if not callable(loader):
		return "no-loader"
	try:
		jar = loader(domain_name=".zhipin.com")
		count = sum(1 for _ in jar)
	except Exception as exc:
		return f"error {type(exc).__name__}: {_sanitize(str(exc))}"
	return f"ok count={count}"


def _extract(source: str | None) -> str:
	from boss_agent_cli.auth.cookie_extract import extract_cookies

	try:
		result = extract_cookies(source, platform="zhipin")
	except Exception as exc:
		return f"error {type(exc).__name__}: {_sanitize(str(exc))}"
	if not result:
		return "none"
	cookies = result.get("cookies") if isinstance(result, dict) else None
	present = isinstance(cookies, dict) and bool(cookies.get("wt2"))
	return "present" if present else "empty"


def _fallback_reaches_sign_in_window() -> str:
	"""Cookie 读不到时，应继续走到扫码窗口。这里用替身，不打开浏览器、不访问网站。"""
	from boss_agent_cli.auth.manager import AuthManager

	with tempfile.TemporaryDirectory(prefix="hr-cookie-probe-") as folder:
		with (
			patch("boss_agent_cli.auth.manager.extract_cookies", return_value=None),
			patch("boss_agent_cli.auth.manager.probe_cdp", return_value=None),
			patch(
				"boss_agent_cli.auth.manager.login_via_browser",
				return_value={"cookies": {"wt2": "probe"}, "user_agent": "probe", "stoken": ""},
			) as sign_in,
		):
			result = AuthManager(Path(folder), platform="zhipin").login(timeout=1)
		called = sign_in.called
		method = result.get("_method") if isinstance(result, dict) else None
	if called and method == "扫码登录":
		return "calls_sign_in_window"
	return f"unexpected called={called} method={method}"


def main() -> int:
	os.environ.setdefault("BOSS_AGENT_MACHINE_ID", "windows-cookie-probe")
	print("chrome_exe:", _browser_exe("chrome"))
	print("edge_exe:", _browser_exe("edge"))
	for name in ("chrome", "edge"):
		state = _local_state(name)
		print(
			f"{name}_local_state:",
			f"file={state['file']}",
			f"encrypted_key={state['encrypted_key']}",
			f"app_bound_encrypted_key={state['app_bound_encrypted_key']}",
		)
		print(f"{name}_cookie_api:", _cookie_api(name))
		print(f"extract_{name}:", _extract(name))
	print("extract_auto:", _extract(None))
	try:
		fallback = _fallback_reaches_sign_in_window()
	except Exception as exc:
		print(f"login_fallback_when_cookies_missing: error {type(exc).__name__}: {_sanitize(str(exc))}")
		return 1
	print("login_fallback_when_cookies_missing:", fallback)
	return 0 if fallback == "calls_sign_in_window" else 1


if __name__ == "__main__":
	raise SystemExit(main())
