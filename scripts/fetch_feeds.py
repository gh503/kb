#!/usr/bin/env python3
"""抓取 feeds.opml 里的 RSS/Atom，归档成 docs/订阅/YYYY-MM-DD.md 并重建索引页。

设计约束（改之前先读）：
1. 归档即状态：不维护 seen 表，直接扫描已有页面里的链接去重。删掉某天文件，
   那天的条目就会在下次抓取时被重新拉回来——这是特性，不是 bug。
2. 只存 标题 / 时间 / 来源 / 链接，不存正文。版权上这是最安全的一档。
3. 每页 front matter 写 search.exclude，整页不进全局搜索——它每天在变，
   进了索引会把知识条目淹掉（Material 的 search 插件支持按页排除）。
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

CN = timezone(timedelta(hours=8))
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "订阅"
UA = "Mozilla/5.0 (compatible; kb-feed/1.0; +https://gh503.github.io/kb/)"

ITEM_RE = re.compile(r"^- (\d{2}:\d{2}) · \[(.+)\]\((\S+)\)$")
DAY_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


# ---------- 读源 ----------

def parse_opml(path: Path):
    body = ET.parse(path).getroot().find("body")
    out = []
    for cat in body.findall("outline"):
        for f in cat.findall("outline"):
            if f.get("xmlUrl"):
                out.append((cat.get("text"), f.get("text"), f.get("xmlUrl")))
    return out


def text_of(el, *tags):
    for t in tags:
        v = el.findtext(t)
        if v and v.strip():
            return v.strip()
    return ""


def parse_dt(raw: str) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def fetch(feed, attempts=3, backoff=(2, 6)):
    """抓一个源。失败重试两次——每周一 Substack 有约 20% 概率返回 HTTPError，
    单次失败会让那天的源整年缺一条，重试能把它吃掉。"""
    cat, name, url = feed
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read(8_000_000)
            # 有的源无视 Accept-Encoding: identity，照样回 gzip——不解压就是 ParseError
            if raw[:2] == b"\x1f\x8b":
                import gzip
                raw = gzip.decompress(raw)
            root = ET.fromstring(raw)
            break
        except Exception as e:
            last = f"{type(e).__name__}"
            if i < attempts - 1:
                time.sleep(backoff[min(i, len(backoff) - 1)])
    else:
        return [], last
    items = []
    atom = "{http://www.w3.org/2005/Atom}"
    for it in list(root.iter("item")) + list(root.iter(f"{atom}entry")):
        title = text_of(it, "title", f"{atom}title")
        link = text_of(it, "link")
        if not link:
            ln = it.find(f"{atom}link")
            link = (ln.get("href") or "") if ln is not None else ""
        if not title or not link:
            continue
        dt = parse_dt(text_of(it, "pubDate", "date", "{http://purl.org/dc/elements/1.1/}date",
                               f"{atom}updated", f"{atom}published"))
        items.append({"title": title, "url": link, "dt": dt, "source": name, "category": cat})
    return items, None


# ---------- 去重与归档 ----------

TRACKING = ("utm_", "at_", "fbclid", "gclid", "spm", "from")


def canon(url: str) -> str:
    s = urlsplit(url.strip())
    q = [(k, v) for k, v in parse_qsl(s.query, keep_blank_values=True)
         if not k.lower().startswith(TRACKING)]
    host = s.netloc.lower().removeprefix("www.")
    return urlunsplit((s.scheme.lower(), host, s.path.rstrip("/") or "/",
                       urlencode(q), ""))


def load_archive():
    days: dict[date, list[dict]] = {}
    seen: set[str] = set()
    if not OUT.exists():
        return days, seen
    for p in sorted(OUT.glob("2*.md")):
        m = DAY_FILE_RE.match(p.name)
        if not m:
            continue
        d = date.fromisoformat(m.group(1))
        cat = src = None
        buf = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                cat = line[3:].strip()
            elif line.startswith("**") and line.rstrip().endswith("**"):
                src = line.strip("* ").strip()
            elif (mm := ITEM_RE.match(line)):
                t, title, url = mm.groups()
                buf.append({"time": t, "title": title.replace("\\]", "]"),
                            "url": url, "source": src, "category": cat})
                seen.add(canon(url))
        days[d] = buf
    return days, seen


def render_day(d: date, items: list[dict]) -> str:
    order = {"世界与格局": 0, "政策与民生": 1, "科技与未来": 2, "深度与思想": 3,
             "经济与生活": 4, "健康与科学": 5, "监测": 6}
    items = sorted(items, key=lambda x: (order.get(x["category"], 99), x["category"],
                                         x["source"] or "", x["time"]), reverse=False)
    lines = ["---", "search:", "  exclude: true", "---", "", f"# {d.isoformat()}", ""]
    cats: dict[str, dict[str, list]] = {}
    for it in items:
        cats.setdefault(it["category"] or "未分类", {}).setdefault(it["source"] or "未知来源", []).append(it)
    for cat in sorted(cats, key=lambda c: order.get(c, 99)):
        lines += [f"## {cat}", ""]
        for src in sorted(cats[cat]):
            lines += [f"**{src}**", ""]
            for it in sorted(cats[cat][src], key=lambda x: x["time"], reverse=True):
                title = it["title"].replace("]", "\\]")
                lines.append(f"- {it['time']} · [{title}]({it['url']})")
            lines.append("")
    return "\n".join(lines)


def render_index(days: dict[date, list[dict]], run_stats: tuple) -> str:
    total = sum(len(v) for v in days.values())
    ok, n, fails, ts = run_stats
    out = [
        "# 订阅", "",
        f"> {n} 个信息源，每天 07:00 自动抓取。**只存标题和链接**，正文去原站读。", "",
        f"> 本区不进全局搜索——它每天在变，进了索引会把知识条目淹掉。"
        f"找某一天，从下面的月份里点。", "",
        f"**累计 {total} 条** · 覆盖 {len(days)} 天 · 最近一次抓取 "
        f"{ts.strftime('%Y-%m-%d %H:%M')}（{ok}/{n} 源成功）",
    ]
    if fails:
        out += ["", f"!!! warning \"{len(fails)} 个源这次没抓到\"",
                "\n".join(f"    - {f}" for f in fails)]
    out += ["", "## 怎么用", "",
            "- 想扫一眼今天有什么：点最新一天",
            "- 想找上周某条：按月份进去，浏览器里 `Ctrl+F`",
            "- 值得留下的：写成对应学科的条目，进正式索引（那边才搜得到）", ""]
    by_month: dict[str, list[date]] = {}
    for d in days:
        by_month.setdefault(f"{d.year}-{d.month:02d}", []).append(d)
    for month in sorted(by_month, reverse=True):
        ds = sorted(by_month[month], reverse=True)
        out += [f"## {month}", "", "| 日期 | 条目 |", "| --- | --- |"]
        for d in ds:
            out.append(f"| [{d.isoformat()}]({d.isoformat()}.md) | {len(days[d])} |")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feeds", default=str(ROOT / "feeds.opml"))
    ap.add_argument("--backfill", action="store_true", help="回填各源当前保留的全部条目")
    ap.add_argument("--max-age-days", type=int, default=365, help="超过这个天数的条目不收")
    ap.add_argument("--per-feed", type=int, default=30, help="每个源每次最多看多少条（--backfill 时提高到 1000）")
    args = ap.parse_args()

    feeds = parse_opml(Path(args.feeds))
    days, seen = load_archive()
    today = datetime.now(CN).date()
    newest = today - timedelta(days=args.max_age_days)

    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        for feed, (items, err) in zip(feeds, ex.map(fetch, feeds)):
            results.append((feed, items, err))

    cap = 1000 if args.backfill else args.per_feed
    added = 0
    undated = 0
    fails = []
    for (cat, name, _url), items, err in results:
        items = items[:cap]
        if err:
            fails.append(f"{name}（{err}）")
            continue
        for it in items:
            key = canon(it["url"])
            if key in seen:
                continue
            dt = it["dt"]
            if dt is None and args.backfill:
                undated += 1
                continue
            d = dt.astimezone(CN).date() if dt else today
            if d > today:
                d = today
            if d < newest:
                continue
            seen.add(key)
            items_ = days.setdefault(d, [])
            items_.append({"time": (dt.astimezone(CN).strftime("%H:%M") if dt else "00:00"),
                           "title": it["title"], "url": it["url"],
                           "source": name, "category": cat})
            added += 1

    OUT.mkdir(parents=True, exist_ok=True)
    for d, items in days.items():
        if not items:
            continue
        (OUT / f"{d.isoformat()}.md").write_text(render_day(d, items), encoding="utf-8")

    ok = len(feeds) - len(fails)
    ts = datetime.now(CN)
    # 没有新条目就不重写索引——否则每天的运行时间戳会造出一个空提交。
    # 但"源健康度"变了必须重写：否则修好一个源、索引里还挂着旧的失败警告。
    idx = OUT / "index.md"
    prev_health = ""
    if idx.exists():
        m = re.search(r"（(\d+)/(\d+) 源成功）", idx.read_text(encoding="utf-8"))
        prev_health = m.group(0) if m else ""
    health = f"（{ok}/{len(feeds)} 源成功）"
    if added or not idx.exists() or health != prev_health:
        idx.write_text(render_index(days, (ok, len(feeds), fails, ts)), encoding="utf-8")
    if undated:
        print(f"跳过 {undated} 条无日期的条目（回填时不猜日期）")
    print(f"新增 {added} 条 · 归档 {len(days)} 天 · 共 {sum(len(v) for v in days.values())} 条"
          f" · 源 {ok}/{len(feeds)} 成功")
    if fails:
        print("失败：" + "；".join(fails))
    return 0


if __name__ == "__main__":
    sys.exit(main())
