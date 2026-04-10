#!/usr/bin/env python3
"""
Tushare API 文档爬取脚本
将 tushare.pro/wctapi/documents/ 的所有接口文档抓取到本地

用法:
    python3 crawl_docs.py           # 增量模式(跳过已存在文件)
    python3 crawl_docs.py --force   # 强制重新抓取全部
    python3 crawl_docs.py --dry-run # 只显示待抓取 URL，不实际下载

输出目录: ~/.claude/data/tushare/docs/
"""

import os
import re
import sys
import time
import json
import argparse
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── 配置 ──────────────────────────────────────────────────────────────────────
BASE_URL    = "https://tushare.pro/wctapi/documents/{id}.md"
_HERE       = Path(__file__).parent
SKILL_INDEX = _HERE / "../references/数据接口.md"
OUTPUT_DIR  = _HERE / "../docs"
INDEX_FILE  = _HERE / "../docs-index.json"

MAX_WORKERS   = 8    # 并发线程数
DELAY_BETWEEN = 0.05 # 每个请求之间最小间隔(秒)，控制礼貌速率
TIMEOUT       = 15   # 请求超时(秒)
# ID 扫描范围：从 skill index 已知 ID + 盲扫 1~450 补漏
SCAN_RANGE    = range(1, 451)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TushareDocCrawler/1.0; research purposes)",
    "Accept": "text/plain, text/markdown, */*",
}


def extract_ids_from_index(path: Path) -> set[int]:
    """从 references/数据接口.md 提取所有文档 ID"""
    ids = set()
    if not path.exists():
        print(f"[WARN] index file not found: {path}")
        return ids
    content = path.read_text(encoding="utf-8")
    for m in re.finditer(r"documents/(\d+)\.md", content):
        ids.add(int(m.group(1)))
    return ids


def fetch_doc(doc_id: int) -> tuple[int, str | None, str | None]:
    """
    返回 (id, content, error)
    content=None 表示 404/无内容; error=None 表示成功
    """
    url = BASE_URL.format(id=doc_id)
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            content = resp.read().decode("utf-8").strip()
            if not content or len(content) < 20:
                return doc_id, None, "empty"
            return doc_id, content, None
    except HTTPError as e:
        if e.code == 404:
            return doc_id, None, "404"
        return doc_id, None, f"HTTP {e.code}"
    except URLError as e:
        return doc_id, None, f"URLError: {e.reason}"
    except Exception as e:
        return doc_id, None, f"Error: {e}"


def extract_interface_name(content: str) -> str | None:
    """从 Markdown 内容中提取接口名"""
    m = (re.search(r"接口[：: ]+([a-zA-Z0-9_]+)", content) or
         re.search(r"\*\*接口名称\*\*[：: ]+([a-zA-Z0-9_]+)", content) or
         re.search(r"\*\*接口\*\*[：: ]+([a-zA-Z0-9_]+)", content))
    return m.group(1).strip() if m else None


def extract_title(content: str) -> str | None:
    """提取文档标题（第一行 ## 标题）"""
    m = re.match(r"^#+\s+(.+)", content, re.MULTILINE)
    return m.group(1).strip() if m else None


def extract_description(content: str) -> str | None:
    """提取描述"""
    m = re.search(r"描述[：: ]+(.+)", content)
    return m.group(1).strip() if m else None


def save_doc(doc_id: int, content: str, index: dict) -> None:
    """保存文档并更新索引"""
    iface = extract_interface_name(content)
    title = extract_title(content)
    desc  = extract_description(content)

    filename = f"{doc_id:04d}"
    if iface:
        # 文件名: 0001_daily.md 格式
        filename = f"{doc_id:04d}_{iface}"
    filepath = OUTPUT_DIR / f"{filename}.md"
    filepath.write_text(content, encoding="utf-8")

    index[str(doc_id)] = {
        "id":        doc_id,
        "interface": iface,
        "title":     title,
        "desc":      desc,
        "file":      str(filepath),
    }


LOG_FILE = _HERE / "../crawl-logs.md"

def append_crawl_log(success: int, skipped: int, failed: int, total_interfaces: int) -> None:
    """在 crawl-logs.md 表格末尾追加一行"""
    from datetime import date
    if not LOG_FILE.exists():
        LOG_FILE.write_text(
            "# Crawl Logs\n\n"
            "| 日期 | 成功 | 跳过(404) | 失败 | 有效接口数 |\n"
            "|------|------|----------|------|----------|\n",
            encoding="utf-8",
        )
    row = f"| {date.today()} | {success} | {skipped} | {failed} | {total_interfaces} |\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(row)


def main():
    parser = argparse.ArgumentParser(description="Tushare 文档爬取工具")
    parser.add_argument("--force",   action="store_true", help="强制重新抓取已存在文件")
    parser.add_argument("--dry-run", action="store_true", help="只打印待抓取列表，不下载")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 加载已有索引
    index = {}
    if INDEX_FILE.exists():
        try:
            index = json.loads(INDEX_FILE.read_text())
        except Exception:
            pass

    # 从 skill index 提取已知 ID，合并盲扫范围
    known_ids  = extract_ids_from_index(SKILL_INDEX)
    all_ids    = sorted(set(SCAN_RANGE) | known_ids)
    print(f"已知 ID: {len(known_ids)} 个 | 总扫描范围: {min(all_ids)}~{max(all_ids)} ({len(all_ids)} 个)")

    # 过滤：跳过已下载(非强制模式)
    if not args.force:
        existing_ids = {int(k) for k in index.keys()}
        pending_ids  = [i for i in all_ids if i not in existing_ids]
        print(f"已缓存: {len(existing_ids)} 个 | 待抓取: {len(pending_ids)} 个")
    else:
        pending_ids = all_ids
        print(f"强制模式：重抓全部 {len(pending_ids)} 个")

    if args.dry_run:
        print("\n[DRY RUN] 待抓取 URL:")
        for i in pending_ids[:20]:
            print(f"  {BASE_URL.format(id=i)}")
        if len(pending_ids) > 20:
            print(f"  ... 还有 {len(pending_ids)-20} 个")
        return

    if not pending_ids:
        print("无需更新，所有文档已是最新。")
        return

    # 并发抓取
    success = skipped = failed = 0
    start   = time.time()

    def rate_limited_fetch(doc_id):
        time.sleep(DELAY_BETWEEN)
        return fetch_doc(doc_id)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(rate_limited_fetch, i): i for i in pending_ids}
        done    = 0
        total   = len(pending_ids)

        for future in as_completed(futures):
            doc_id, content, error = future.result()
            done += 1

            if content:
                save_doc(doc_id, content, index)
                success += 1
                iface = index[str(doc_id)].get("interface") or ""
                status = f"✓  {doc_id:4d}  {iface:<30s}"
            elif error == "404" or error == "empty":
                skipped += 1
                status = f"   {doc_id:4d}  (不存在)"
            else:
                failed += 1
                status = f"✗  {doc_id:4d}  {error}"

            pct = done / total * 100
            print(f"[{pct:5.1f}%] {status}", flush=True)

            # 每 50 条保存一次索引，防止中途中断丢失
            if done % 50 == 0:
                INDEX_FILE.write_text(
                    json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
                )

    # 最终保存索引
    INDEX_FILE.write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    elapsed = time.time() - start
    total_ifaces = sum(1 for v in index.values() if v["interface"])
    print(f"\n{'='*60}")
    print(f"完成: 成功={success}  跳过(404)={skipped}  失败={failed}")
    print(f"耗时: {elapsed:.1f}s  |  文档目录: {OUTPUT_DIR}")
    print(f"索引文件: {INDEX_FILE}")
    print(f"有效接口数: {total_ifaces}")
    append_crawl_log(success, skipped, failed, total_ifaces)


if __name__ == "__main__":
    main()
