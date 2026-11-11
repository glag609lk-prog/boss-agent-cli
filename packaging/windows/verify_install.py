"""验收已安装的招聘助手。只跑本地命令，不登录、不发送。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ENVELOPE_KEYS = {"ok", "schema_version", "command", "data", "pagination", "error", "hints"}


def _run(boss: Path, args: list[str]) -> tuple[int, str, str]:
	command = subprocess.list2cmdline([str(boss), *args])
	completed = subprocess.run(
		["cmd.exe", "/c", command],
		capture_output=True,
		check=False,
	)
	stdout = completed.stdout.decode("utf-8")
	stderr = completed.stderr.decode("utf-8", errors="replace")
	return completed.returncode, stdout, stderr


def _envelope(stdout: str) -> dict:
	payload = json.loads(stdout)
	if not isinstance(payload, dict) or set(payload) != ENVELOPE_KEYS:
		raise SystemExit(f"不是七键 JSON 信封: {stdout[:500]}")
	return payload


def main(argv: list[str] | None = None) -> int:
	args = list(sys.argv[1:] if argv is None else argv)
	if len(args) != 1:
		print("usage: verify_install.py <boss.cmd>", file=sys.stderr)
		return 2
	boss = Path(args[0])
	if not boss.is_file():
		print(f"找不到 {boss}", file=sys.stderr)
		return 1

	code, stdout, stderr = _run(boss, ["--version"])
	if code != 0 or "boss" not in stdout.lower():
		print(stdout)
		print(stderr, file=sys.stderr)
		raise SystemExit("boss --version 失败")
	print("version:", stdout.strip())

	code, stdout, stderr = _run(boss, ["--json", "schema"])
	payload = _envelope(stdout)
	if code != 0 or payload.get("ok") is not True:
		print(stderr, file=sys.stderr)
		raise SystemExit("boss schema 失败")
	subcommands = payload["data"]["commands"]["hr"]["subcommands"]
	if "location" not in subcommands:
		raise SystemExit("schema 里没有 hr location")
	print("schema: hr location present")

	code, stdout, stderr = _run(boss, ["--json", "doctor"])
	payload = _envelope(stdout)
	if code != 0 or not isinstance(payload.get("ok"), bool):
		print(stderr, file=sys.stderr)
		raise SystemExit("boss doctor 没有返回信封")
	print("doctor: ok =", payload["ok"])

	code, stdout, stderr = _run(boss, ["--json", "hr", "location", "123", "--dry-run"])
	payload = _envelope(stdout)
	if payload.get("ok") is True:
		data = payload.get("data")
		if not isinstance(data, dict) or data.get("dry_run") is not True:
			raise SystemExit("预览结果缺少 dry_run")
	else:
		error = payload.get("error")
		if not isinstance(error, dict) or not isinstance(error.get("code"), str):
			raise SystemExit("失败信封缺少 error.code")
		if not isinstance(error.get("recoverable"), bool) or "recovery_action" not in error:
			raise SystemExit("失败信封缺少 recoverable 或 recovery_action")
	if (payload.get("ok") is True and code != 0) or (payload.get("ok") is False and code == 0):
		raise SystemExit("退出码和 ok 不一致")
	print("location:", "preview" if payload.get("ok") else payload["error"]["code"])
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
