"""把 boss doctor 的 JSON 结果说成 HR 能直接看懂的话。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def explain(envelope: dict[str, Any]) -> str:
	"""返回给安装窗口看的中文说明。不复述内部字段名。"""
	if not isinstance(envelope, dict) or "ok" not in envelope:
		return "自检结果看不懂。请把这个窗口的文字发给同事。"
	if envelope.get("ok") is not True:
		error = envelope.get("error") if isinstance(envelope.get("error"), dict) else {}
		message = str(error.get("message") or "自检没有完成")
		return "自检没有完成。\n" + message + "\n请把窗口里的文字发给同事看一下。"

	data = envelope.get("data") if isinstance(envelope.get("data"), dict) else {}
	checks = data.get("checks") if isinstance(data.get("checks"), list) else []
	by_name = {item.get("name"): item for item in checks if isinstance(item, dict)}
	lines = ["招聘助手已经装好，可以开始用了。", ""]
	state = data.get("auth_state")
	if state == "complete":
		lines.append("这台电脑已经登录过，助手可以直接开始干活。")
	elif state == "partial":
		lines.append("登录信息还不全。如果助手提示要重新登录，按弹出的二维码扫一次就行。")
	elif state == "broken":
		lines.append("登录信息异常。如果助手提示要重新登录，按弹出的二维码扫一次就行。")
	else:
		lines.append("这台电脑还没有登录。第一次使用时，助手会先试试你浏览器里是否已经登录过招聘网站；不行的话，会弹出窗口让你扫码。")

	chromium = by_name.get("patchright_chromium") or {}
	if chromium.get("status") in {"warn", "error"}:
		lines.append("登录用的浏览器内核还没准备好。连上网之后再双击一次「安装.bat」。没有它，扫码窗口可能打不开。程序本身不用重装。")
	network = by_name.get("network") or {}
	if network.get("status") in {"warn", "error"}:
		lines.append("这台电脑暂时打不开招聘网站。请检查网络或公司代理。程序已经装好，不用重装。")
	paused = by_name.get("cdp_risk_lock") or {}
	if paused.get("status") not in {None, "ok"}:
		lines.append("安全暂停已经打开，助手会先停下来。需要继续时告诉同事，不要自己反复重试。")
	lines.append("")
	lines.append("登录信息保存在这台电脑上。以后再次双击安装，只会更新程序，不会清掉登录。")
	lines.append("请新开一个命令行窗口再使用，这样系统才能找到 boss 命令。")
	return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
	args = list(sys.argv[1:] if argv is None else argv)
	if len(args) != 1:
		print("缺少自检结果文件。", file=sys.stderr)
		return 1
	path = Path(args[0])
	try:
		envelope = json.loads(path.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError):
		print("自检结果读不出来。请把这个窗口的文字发给同事。")
		return 0
	if not isinstance(envelope, dict):
		print("自检结果看不懂。请把这个窗口的文字发给同事。")
		return 0
	print(explain(envelope))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
