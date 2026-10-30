#!/usr/bin/env python3
"""build_site.py — 把 data/v2*、原始圖片轉成靜態站 site/ 所需的資料與縮圖。

本 repo（atlas/）只收資料與網站，不含圖片（約 404MB）。重建方式：
  1. 取得原始圖片目錄（結構 <縣>/<類>.webp、<縣>/food_N.webp、<縣>/spot_N.webp、
     areas/<地區id>/<類>.webp），放在 atlas/images/（預設）或用 --images 指定。
  2. python3 build_site.py [--images /path/to/images]
     → 重寫 site/data/*.js（資料內存相對路徑 img/…、img/t/…），並把大圖(1280px)與
       縮圖(480px)輸出到 site/img/、site/img/t/（已被 .gitignore 排除，不進 repo）。
  3. 圖片外部存放時：把 site/img/ 上傳到圖床，再於 site/config.js 設
     window.JP_IMG_BASE = "https://你的圖床/路徑/";（結尾要有 /）。
若沒有圖片目錄，所有項目會被視為「無圖」（網站顯示「圖片待生成」佔位），
所以請勿在無圖環境下覆蓋 site/data/（現有 site/data 已含正確的圖片路徑）。
只讀 data/、圖片目錄；只寫 site/img/、site/data/。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
# 原始圖片目錄：預設 atlas/images/，可用 --images 指定（本 repo 不含圖片）
IMAGES = ROOT / "images"
if "--images" in sys.argv:
    IMAGES = Path(sys.argv[sys.argv.index("--images") + 1]).expanduser().resolve()
SITE = ROOT / "site"
OUT_IMG = SITE / "img"
OUT_THUMB = SITE / "img" / "t"
OUT_DATA = SITE / "data"

# 縣碼（JIS）→ 縣 id（與 data/ 檔名一致）
PREFS: list[tuple[str, str]] = [
    ("01", "hokkaido"), ("02", "aomori"), ("03", "iwate"), ("04", "miyagi"),
    ("05", "akita"), ("06", "yamagata"), ("07", "fukushima"), ("08", "ibaraki"),
    ("09", "tochigi"), ("10", "gunma"), ("11", "saitama"), ("12", "chiba"),
    ("13", "tokyo"), ("14", "kanagawa"), ("15", "niigata"), ("16", "toyama"),
    ("17", "ishikawa"), ("18", "fukui"), ("19", "yamanashi"), ("20", "nagano"),
    ("21", "gifu"), ("22", "shizuoka"), ("23", "aichi"), ("24", "mie"),
    ("25", "shiga"), ("26", "kyoto"), ("27", "osaka"), ("28", "hyogo"),
    ("29", "nara"), ("30", "wakayama"), ("31", "tottori"), ("32", "shimane"),
    ("33", "okayama"), ("34", "hiroshima"), ("35", "yamaguchi"), ("36", "tokushima"),
    ("37", "kagawa"), ("38", "ehime"), ("39", "kochi"), ("40", "fukuoka"),
    ("41", "saga"), ("42", "nagasaki"), ("43", "kumamoto"), ("44", "oita"),
    ("45", "miyazaki"), ("46", "kagoshima"), ("47", "okinawa"),
]

# 八大地方：id, 中文名, 日文名, 縣碼範圍
REGIONS: list[tuple[str, str, str, int, int]] = [
    ("hokkaido", "北海道", "北海道", 1, 1),
    ("tohoku", "東北", "東北", 2, 7),
    ("kanto", "關東", "関東", 8, 14),
    ("chubu", "中部", "中部", 15, 23),
    ("kinki", "近畿", "近畿", 24, 30),
    ("chugoku", "中國", "中国", 31, 35),
    ("shikoku", "四國", "四国", 36, 39),
    ("kyushu", "九州・沖繩", "九州・沖縄", 40, 47),
]

CORE_CATS = ["architecture", "food", "culture", "history", "mascot",
             "scenery", "spot", "experience", "costume"]
AREA_CATS = ["spot", "food", "scenery"]

stats = {"full": 0, "thumb": 0, "skipped": 0, "bad": 0}


def load_json(path: Path) -> dict[str, Any] | None:
    """讀取 JSON；檔案不存在或壞掉時回傳 None（build 不中斷）。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"  ! 無法讀取 {path.name}: {exc}", file=sys.stderr)
        return None


def _is_fresh(dst: Path, src: Path) -> bool:
    """目標檔存在且不比來源舊，就視為最新。"""
    return dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime


def process_image(rel: str) -> tuple[str, str] | None:
    """處理 images/<rel>（如 'kyoto/scenery.webp'）。

    參數：rel 為相對 images/ 的路徑。
    回傳：(大圖相對路徑, 縮圖相對路徑)，相對於 site/；圖不存在／壞圖回傳 None。
    """
    src = IMAGES / rel
    if not src.is_file() or src.name.endswith(".tmp.webp"):
        return None
    full_dst, thumb_dst = OUT_IMG / rel, OUT_THUMB / rel
    results = (f"img/{rel}", f"img/t/{rel}")
    need_full = not _is_fresh(full_dst, src)
    need_thumb = not _is_fresh(thumb_dst, src)
    if not (need_full or need_thumb):
        stats["skipped"] += 1
        return results
    try:
        with Image.open(src) as im:
            im.load()
            im = im.convert("RGB")
    except Exception as exc:  # 可能正在寫入的半成品圖
        print(f"  ! 壞圖略過 {rel}: {exc}", file=sys.stderr)
        stats["bad"] += 1
        return None
    for dst, edge, quality, need, key in (
        (full_dst, 1280, 82, need_full, "full"),
        (thumb_dst, 480, 78, need_thumb, "thumb"),
    ):
        if not need:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        copy = im.copy()
        copy.thumbnail((edge, edge), Image.LANCZOS)  # 只縮小，不放大
        copy.save(dst, "WEBP", quality=quality, method=4)
        stats[key] += 1
    return results


def attach_img(item: dict[str, Any], rel: str) -> None:
    """替 item 加上 img / thumb 欄位（無圖為 None）。"""
    r = process_image(rel)
    item["img"], item["thumb"] = (r if r else (None, None))


def build() -> None:
    """主流程：逐縣輸出 p_<id>.js 並彙整 index.js。"""
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    prefs_meta: list[dict[str, Any]] = []
    search: list[dict[str, Any]] = []
    totals = {"core": 0, "food": 0, "spot": 0, "area": 0, "pref_files": 0}

    for code, pid in PREFS:
        base = load_json(DATA / "v2" / f"{pid}.json")
        if base is None:
            print(f"  ! 缺 {pid}，略過", file=sys.stderr)
            continue
        food = (load_json(DATA / "v2_food" / f"{pid}.json") or {}).get("foods", [])
        spot = (load_json(DATA / "v2_spot" / f"{pid}.json") or {}).get("spots", [])
        counts = {k: {"have": 0, "total": 0} for k in ("core", "food", "spot", "area")}

        # 九類核心項目
        items: dict[str, Any] = {}
        for cat in CORE_CATS:
            it = dict((base.get("items") or {}).get(cat) or {})
            if not it:
                continue
            attach_img(it, f"{pid}/{cat}.webp")
            items[cat] = it
            counts["core"]["total"] += 1
            counts["core"]["have"] += bool(it["img"])
            search.append({"p": pid, "k": "core", "c": cat, "i": cat,
                           "t": it.get("title_zh", ""), "tj": it.get("title_ja", ""),
                           "s": it.get("summary_zh", ""), "tags": it.get("tags", []),
                           "f": it.get("confidence", ""), "th": it["thumb"]})
        # 美食／景點（陣列第 N 項對應 food_N / spot_N）
        for kind, arr, key in (("food", food, "food"), ("spot", spot, "spot")):
            for n, it in enumerate(arr):
                attach_img(it, f"{pid}/{key}_{n + 1}.webp")
                counts[kind]["total"] += 1
                counts[kind]["have"] += bool(it["img"])
                search.append({"p": pid, "k": kind, "c": it.get("category", ""), "i": n,
                               "t": it.get("title_zh", ""), "tj": it.get("title_ja", ""),
                               "s": it.get("summary_zh", ""), "tags": it.get("tags", []),
                               "f": it.get("confidence", ""), "th": it["thumb"]})
        # 重點地區
        areas: list[dict[str, Any]] = []
        for ar in base.get("areas") or []:
            a_items: dict[str, Any] = {}
            for cat in AREA_CATS:
                it = dict((ar.get("items") or {}).get(cat) or {})
                if not it:
                    continue
                attach_img(it, f"areas/{ar['id']}/{cat}.webp")
                a_items[cat] = it
                counts["area"]["total"] += 1
                counts["area"]["have"] += bool(it["img"])
                search.append({"p": pid, "k": "area", "c": cat, "i": f"{ar['id']}/{cat}",
                               "t": it.get("title_zh", ""), "tj": it.get("title_ja", ""),
                               "s": it.get("summary_zh", ""), "tags": it.get("tags", []),
                               "f": it.get("confidence", ""), "th": it["thumb"],
                               "a": ar.get("name_zh", "")})
            areas.append({"id": ar.get("id"), "name_zh": ar.get("name_zh", ""),
                          "name_ja": ar.get("name_ja", ""),
                          "intro_zh": ar.get("intro_zh", ""), "items": a_items})

        for k in ("core", "food", "spot", "area"):
            totals[k] += counts[k]["have"]

        # 縣封面：優先 scenery，其次 spot_1，再 spot
        cover = None
        for rel in (f"{pid}/scenery.webp", f"{pid}/spot_1.webp", f"{pid}/spot.webp"):
            r = process_image(rel)
            if r:
                cover = r[1]
                break

        payload = {"overview": base.get("overview", {}), "items": items,
                   "foods": food, "spots": spot, "areas": areas}
        (OUT_DATA / f"p_{pid}.js").write_text(
            f"(window.JP_P=window.JP_P||{{}})['{pid}']="
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
            encoding="utf-8")
        totals["pref_files"] += 1
        prefs_meta.append({
            "id": pid, "code": code, "name_zh": base.get("name_zh", ""),
            "name_ja": base.get("name_ja", ""), "region": base.get("region", ""),
            "capital_zh": (base.get("overview") or {}).get("capital_zh", ""),
            "cover": cover, "counts": counts})

    regions = []
    for rid, zh, ja, lo, hi in REGIONS:
        regions.append({"id": rid, "name_zh": zh, "name_ja": ja,
                        "prefs": [pid for c, pid in PREFS if lo <= int(c) <= hi]})
    index = {"regions": regions, "prefs": prefs_meta, "search": search}
    (OUT_DATA / "index.js").write_text(
        "window.JP_INDEX=" + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")

    print(f"縣檔輸出：{totals['pref_files']}/47　搜尋條目：{len(search)}")
    print(f"有圖張數（來源）— 九類 {totals['core']}、美食 {totals['food']}、"
          f"景點 {totals['spot']}、地區 {totals['area']}")
    print(f"圖片處理：新寫大圖 {stats['full']}、新寫縮圖 {stats['thumb']}、"
          f"已最新跳過 {stats['skipped']}、壞圖略過 {stats['bad']}")


if __name__ == "__main__":
    build()
