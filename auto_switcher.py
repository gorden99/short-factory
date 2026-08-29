# -*- coding: utf-8 -*-
"""免费额度自动切换模块（auto_switcher）

当当前激活的免费模型额度用完（方舟返回 429）时，自动切换到下一个还有免费额度的模型。
- FREE_MODEL_QUEUE：免费模型轮换队列（按推荐顺序，可随时调整）
- switch_to_next()：当前模型额度用完时调用，自动切到下一个可用的免费模型
- status_report()：列出所有免费模型当前状态（供监控/查看）

用法（集成到生成流程）：
    在捕获到 429 错误时调用 auto_switcher.switch_to_next()，然后用新模型重试即可。
"""
import io
import os
import threading

import model_manager

# ===== 免费模型轮换队列（按推荐顺序，用完当前自动切下一个）=====
# 这些是已在方舟开通、带免费体验额度的模型
FREE_MODEL_QUEUE = [
    "deepseek-v4-flash-ga-260731",      # 1. DeepSeek V4 Flash（轻量快，当前默认）
    "deepseek-v4-flash-260425",         # 2. DeepSeek V4 Flash 备用
    "deepseek-v4-pro-ga-260813",        # 3. DeepSeek V4 Pro（旗舰）
    "deepseek-v4-pro-260425",           # 4. DeepSeek V4 Pro 备用
    "glm-5-2-260617",                   # 5. GLM-5.2（智谱旗舰）
    "doubao-seed-2-1-pro-260628",       # 6. 豆包 Seed 2.1 Pro（旗舰）
    "doubao-seed-2-0-pro-260215",       # 7. 豆包 Seed 2.0 Pro
    "doubao-seed-2-0-lite-260428",      # 8. 豆包 Seed 2.0 Lite
    "doubao-seed-2-0-mini-260428",      # 9. 豆包 Seed 2.0 Mini
    "doubao-seed-2-0-code-preview-260215",  # 10. 豆包 Seed 2.0 Code
    "doubao-seed-character-260628",     # 11. 豆包 Seed 角色
    "doubao-seed-character-251128",     # 12. 豆包 Seed 角色备用
]

_lock = threading.Lock()
_switch_count = 0


def _ark_key() -> str:
    """读取 .env 中的方舟 API Key"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        for line in io.open(env_path, encoding="utf-8"):
            if line.startswith("LLM_API_KEY="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return (model_manager.get_active().get("api_key") or "")


def _id_by_model(model_id: str):
    """按 model 名查 ai_models 表中的 id"""
    for m in model_manager.list_models():
        if m.get("model") == model_id:
            return m["id"]
    return None


def test_model_status(model_id: str, timeout: int = 20) -> str:
    """测试模型状态：
    - 'ok'    可正常调用（有额度）
    - 'quota' 免费额度用完（429）
    - 'fail'  未开通 / 其它错误（404 等）
    """
    import requests
    key = _ark_key()
    if not key or not model_id:
        return "fail"
    try:
        r = requests.post(
            "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model_id, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
            timeout=timeout,
        )
        if r.status_code == 200:
            return "ok"
        if r.status_code == 429:
            return "quota"
        return "fail"
    except Exception:
        return "fail"


def current_model() -> str:
    """当前激活的模型 id"""
    cfg = model_manager.get_active()
    return (cfg.get("model") or "") if cfg else ""


def switch_to_next() -> tuple:
    """当前免费模型额度用完时，切换到下一个可用的免费模型。
    返回 (ok, message)
    """
    global _switch_count
    with _lock:
        cur = current_model()
        if cur not in FREE_MODEL_QUEUE:
            # 当前是非免费/自定义模型：不自动切换，避免干扰用户手动配置
            return False, "当前模型不在免费队列中，不自动切换"

        start = FREE_MODEL_QUEUE.index(cur)
        # 从当前的下一个开始，循环找第一个可用的免费模型
        for step in range(1, len(FREE_MODEL_QUEUE) + 1):
            nxt = FREE_MODEL_QUEUE[(start + step) % len(FREE_MODEL_QUEUE)]
            st = test_model_status(nxt)
            if st == "ok":
                mid = _id_by_model(nxt)
                if mid:
                    model_manager.activate(mid)
                    _switch_count += 1
                    return True, f"已自动切换到免费模型：{nxt}"
            # quota（也用完）/ fail（未开通）都跳过，继续找下一个
        return False, "所有免费模型额度均不可用（都 429 或未开通）"


def status_report() -> list:
    """列出所有免费模型状态，返回 [{model, name, status, current}]"""
    out = []
    cur = current_model()
    for mid in FREE_MODEL_QUEUE:
        st = test_model_status(mid)
        out.append({
            "model": mid,
            "name": next((m["name"] for m in model_manager.list_models() if m.get("model") == mid), mid),
            "status": st,
            "current": mid == cur,
        })
    return out


def get_switch_count() -> int:
    return _switch_count
