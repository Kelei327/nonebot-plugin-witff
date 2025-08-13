# 先 require 再 from nonebot_plugin_htmlrender import ...
from nonebot import require
require("nonebot_plugin_htmlrender")

from pathlib import Path
from typing import List, Tuple, Optional
import json
import threading

import httpx

from nonebot import get_driver
from nonebot.plugin import on_command, PluginMetadata
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment

from nonebot_plugin_htmlrender import template_to_pic


# 插件元信息

__plugin_meta__ = PluginMetadata(
    name="WITFF",
    description="基于NoneBot2架构的兽聚查询",
    usage="使用 “/兽聚” 查看兽聚列表；输入 `/兽聚 帮助` 查看示例用法。",
    type="application",
    homepage="https://github.com/Kelei327/nonebot-plugin-witff",
    supported_adapters={"~onebot.v11"},
)


# 常量 & 配置

API_URL = "https://api.furryfusion.net/service/activity"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
STATE_MAIN = ["活动结束", "预告中", "售票中", "活动中", "活动取消"]
ITEMS_PER_PAGE = 3

TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_NAME = "witff.html"
HELP_TEMPLATE_NAME = "help.html"  # 帮助模板

MODE_IMAGE_TOKEN = "图片发送"
MODE_TEXT_TOKEN = "文字发送"
HELP_TOKEN = "帮助"

PREFS_PATH = Path(__file__).parent / "prefs.json"
_PREFS_LOCK = threading.Lock()



client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=10.0))
driver = get_driver()


@driver.on_shutdown
async def _close_httpx_client():
    try:
        await client.aclose()
    except Exception:
        pass



# 偏好读写

def _load_prefs() -> dict:
    with _PREFS_LOCK:
        if not PREFS_PATH.exists():
            return {}
        try:
            with PREFS_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


def _save_prefs(prefs: dict) -> None:
    with _PREFS_LOCK:
        try:
            with PREFS_PATH.open("w", encoding="utf-8") as f:
                json.dump(prefs, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


USER_PREFS = _load_prefs()


def get_user_pref(user_id: str) -> Optional[str]:
    return USER_PREFS.get(user_id)


def set_user_pref(user_id: str, mode: str) -> None:
    if mode not in ("image", "text"):
        return
    USER_PREFS[user_id] = mode
    _save_prefs(USER_PREFS)



# 数据获取与处理

async def fetch_fusion_data() -> Optional[List[dict]]:
    try:
        resp = await client.get(API_URL, headers=HEADERS)
    except httpx.RequestError:
        return None

    if resp.status_code != 200:
        return None

    try:
        body = resp.json()
    except ValueError:
        return None

    return body.get("data", [])


def filter_by_keyword(data: List[dict], keyword: str) -> List[dict]:
    if not keyword:
        return data
    k = keyword.strip().lower()
    return [
        item
        for item in data
        if k in item.get("title", "").lower() or k in item.get("name", "").lower()
    ]


def paginate_data(data: List[dict], page_num: int) -> Tuple[List[dict], int]:
    total_items = len(data)
    num_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page_num = max(1, min(page_num, num_pages))
    start = (page_num - 1) * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, total_items)
    return data[start:end], num_pages


def normalize_activities(items: List[dict]) -> List[dict]:
    normalized = []
    for item in items:
        groups = item.get("groups")
        state_idx = item.get("state", 0)
        if not isinstance(state_idx, int) or state_idx < 0 or state_idx >= len(STATE_MAIN):
            state_text = STATE_MAIN[0]
        else:
            state_text = STATE_MAIN[state_idx]
        normalized.append({
            "title": item.get("title", "未知"),
            "name": item.get("name", "未知"),
            "state": state_text,
            "group": groups[0] if groups else "无",
            "address": item.get("address", "无地址"),
            "time_day": item.get("time_day", "未知"),
            "time_start": item.get("time_start", "未知"),
            "time_end": item.get("time_end", "未知"),
        })
    return normalized


def build_text_message(activities: List[dict], page_num: int, num_pages: int, mode: str) -> str:
    if mode == "image":
        hint = f"[当前为 图片发送 模式] · 输入 `/兽聚 文字发送` 切换到文字模式\n\n"
    else:
        hint = f"[当前为 文字发送 模式] · 输入 `/兽聚 图片发送` 切换到图片模式\n\n"

    parts = [hint + f"==== [WITFF?] 第 {page_num}/{num_pages} 页 ===="]
    for item in activities:
        parts.append(
            "\n--------------------\n"
            f"兽聚名称：{item.get('title')}\n"
            f"兽聚主题：{item.get('name')}\n"
            f"兽聚状态：{item.get('state')}\n"
            f"兽聚Q群：{item.get('group')}\n"
            f"兽聚地址：{item.get('address')}\n"
            f"举办天数：{item.get('time_day')} 天\n"
            f"举办时间：{item.get('time_start')} ~ {item.get('time_end')}\n"
            "--------------------"
        )
    parts.append(f"\n==== [WITFF?] {page_num}/{num_pages} 页 ====")
    return "\n".join(parts)


def build_help_message() -> str:
    examples = [
        "/兽聚                  —— 显示第 1 页",
        "/兽聚 2                —— 显示第 2 页",
        "/兽聚 搜索 研          —— 搜索包含“研”的活动并显示第一页（图片）",
        "/兽聚 搜索 研 聚 2 —— 多词搜索并显示第 2 页",
        "/兽聚 图片发送         —— 以图片形式发送结果",
        "/兽聚 文字发送         —— 以文本形式发送结果",
        "/兽聚 搜索 研 文字发送 2 —— 混合使用：搜索、文字发送、页码",
        "/兽聚 帮助             —— 显示本帮助",
    ]
    return "WITFF 使用说明：\n\n" + "\n".join(examples) + "\n\n说明：默认输出为 图片发送 模式。你可以在同一条命令中同时指定 搜索/页码/输出模式。"



# 命令处理器

fusion_activity = on_command("兽聚", priority=10, block=True)


@fusion_activity.handle()
async def _(event: MessageEvent):
    raw = str(event.get_message() or "").strip()
    args = [t for t in raw.split() if t]

    # 获取 user_id（用于偏好读写）
    user_id = event.get_user_id()

    
    # 图片发送 / 文字发送
    
    explicit_mode = None
    removed_indices = set()
    for i, tok in enumerate(args):
        if tok == MODE_IMAGE_TOKEN:
            explicit_mode = "image"
            removed_indices.add(i)
        elif tok == MODE_TEXT_TOKEN:
            explicit_mode = "text"
            removed_indices.add(i)

    if removed_indices:
        args = [t for i, t in enumerate(args) if i not in removed_indices]

    if explicit_mode:
        mode = explicit_mode
        try:
            set_user_pref(user_id, mode)
        except Exception:
            pass
    else:
        pref = get_user_pref(user_id)
        mode = pref if pref in ("image", "text") else "image"

    
    # HELP 分支
    
    if HELP_TOKEN in args or "help" in [a.lower() for a in args]:
        examples = [
        "/兽聚                  —— 显示第 1 页",
        "/兽聚 2                —— 显示第 2 页",
        "/兽聚 搜索 研          —— 搜索包含“研”的活动并显示第一页（图片）",
        "/兽聚 搜索 研 聚 2 —— 多词搜索并显示第 2 页",
        "/兽聚 图片发送         —— 以图片形式发送结果",
        "/兽聚 文字发送         —— 以文本形式发送结果",
        "/兽聚 搜索 研 文字发送 2 —— 混合使用：搜索、文字发送、页码",
        "/兽聚 帮助             —— 显示本帮助",
        ]
        mode_hint = "说明：默认输出为 图片发送 模式。你可以在同一条命令中同时指定 搜索/页码/输出模式。"


        response = None
        # 如果 mode 为 image,尝试渲染 help.html ,若失败，回退为文本
        if mode == "image":
            try:
                pic_bytes = await template_to_pic(
                    template_path=str(TEMPLATE_DIR),
                    template_name=HELP_TEMPLATE_NAME,
                    templates={
                        "examples": examples,
                        "mode_hint": mode_hint
                    },
                    pages={
                        "viewport": {"width": 900, "height": 10},
                        "base_url": f"file://{TEMPLATE_DIR}"
                    },
                    wait=0.8
                )
                response = MessageSegment.image(pic_bytes)
            except Exception:
                # 渲染失败：使用纯文本帮助
                response = build_help_message()
        else:
            # mode == "text" -> 直接文本帮助
            response = build_help_message()

        # 只发送一次（图片或文本）
        await fusion_activity.finish(response, at_sender=True)
        return

    
    
    keyword = ""
    page_num = 1
    if "搜索" in args:
        idx = args.index("搜索")
        rest = args[idx + 1 :]
        if not rest:
            await fusion_activity.finish("咱好像没有说要查询什么呢? 请使用 `/兽聚 搜索 关键字`。", at_sender=True)
            return
        if rest and rest[-1].isdigit():
            page_num = max(1, int(rest[-1]))
            keyword_tokens = rest[:-1]
        else:
            keyword_tokens = rest
        keyword = " ".join(keyword_tokens).strip()
        if not keyword:
            await fusion_activity.finish("咱好像没有说要查询什么呢? 请检查关键字。", at_sender=True)
            return
    else:
        if args and args[-1].isdigit():
            page_num = max(1, int(args[-1]))

    # 请求数据
    data = await fetch_fusion_data()
    if data is None:
        await fusion_activity.finish("获取失败，稍后再试试吧～", at_sender=True)
        return
    if not data:
        await fusion_activity.finish("没找到最近的兽聚...xwx", at_sender=True)
        return

    if keyword:
        data = filter_by_keyword(data, keyword)
        if not data:
            await fusion_activity.finish(f"没有找到包含关键词 '{keyword}' 的兽聚呜…", at_sender=True)
            return

    page_slice, num_pages = paginate_data(data, page_num)
    activities = normalize_activities(page_slice)

    # 输出：图片或文字
    if mode == "image":
        mode_hint = "当前为 图片发送 模式 · 输入 /兽聚 文字发送 切换到文字模式"
        try:
            pic_bytes = await template_to_pic(
                template_path=str(TEMPLATE_DIR),
                template_name=TEMPLATE_NAME,
                templates={
                    "activities": activities,
                    "page_num": page_num,
                    "num_pages": num_pages,
                    "mode_hint": mode_hint,
                },
                pages={
                    "viewport": {"width": 900, "height": 10},
                    "base_url": f"file://{TEMPLATE_DIR}"
                },
                wait=1
            )
        except Exception:
            await fusion_activity.finish("渲染失败，请稍后重试或联系管理员。", at_sender=True)
            return
        await fusion_activity.finish(MessageSegment.image(pic_bytes), at_sender=True)
    else:
        text_msg = build_text_message(activities, page_num, num_pages, mode="text")
        await fusion_activity.finish(text_msg, at_sender=True)
