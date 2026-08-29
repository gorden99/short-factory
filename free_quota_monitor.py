# -*- coding: utf-8 -*-
"""免费模型额度监控 + 一键切换工具

用法（在 backend 目录下运行）：
    python free_quota_monitor.py status   # 查看所有免费模型状态
    python free_quota_monitor.py next     # 一键切换到下一个可用的免费模型
    python free_quota_monitor.py watch    # 持续守护：当前模型额度用完自动切下一个
    python free_quota_monitor.py switch <模型ID>  # 手动切到指定模型
"""
import sys
import time
import os
import io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auto_switcher


def _fmt(s):
    return {"ok": "✅ 可用", "quota": "⚠️ 免费额度用完(429)", "fail": "❌ 未开通/错误"}.get(s, s)


def cmd_status():
    print("=" * 66)
    print("免费模型额度状态（方舟免费体验，每模型 50 万 tokens）")
    print("=" * 66)
    cur = auto_switcher.current_model()
    for i, m in enumerate(auto_switcher.status_report(), 1):
        mark = "★ 当前生效" if m["current"] else ""
        print(f"{i}. {m['name'][:28]:30s} {m['model']:32s} {_fmt(m['status'])} {mark}")
    print(f"\n自动切换计数：{auto_switcher.get_switch_count()} 次")


def cmd_next():
    ok, msg = auto_switcher.switch_to_next()
    print(("✅ " if ok else "❌ ") + msg)
    if ok:
        print("当前生效：", auto_switcher.current_model())


def cmd_switch(model_id):
    import model_manager
    mid = None
    for m in model_manager.list_models():
        if m["model"] == model_id:
            mid = m["id"]
            break
    if mid is None:
        print(f"后台未找到模型 {model_id}")
        return
    model_manager.activate(mid)
    print(f"已切换到 {model_id}（当前生效）")


def cmd_watch():
    print("持续守护模式：每 60 秒检查当前模型，额度用完自动切换。Ctrl+C 退出。")
    last = None
    while True:
        cur = auto_switcher.current_model()
        st = auto_switcher.test_model_status(cur)
        now = time.strftime("%H:%M:%S")
        if st == "quota":
            ok, msg = auto_switcher.switch_to_next()
            print(f"[{now}] 当前模型额度用完 → {msg}")
        elif cur != last:
            print(f"[{now}] 当前模型：{cur}（{_fmt(st)}）")
            last = cur
        time.sleep(60)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        cmd_status()
    elif cmd == "next":
        cmd_next()
    elif cmd == "watch":
        cmd_watch()
    elif cmd == "switch" and len(sys.argv) > 2:
        cmd_switch(sys.argv[2])
    else:
        print(__doc__)
