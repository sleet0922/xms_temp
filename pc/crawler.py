#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""知海图书馆 中图分类书目爬虫

两阶段抓取：
  1. 列表页 —— 标题、链接、封面、格式、作者、出版社、出版日期、简介、浏览量
  2. 详情页 —— 作者、语言、类型、页数、大小、出版社、出版时间、ISBN、分类、内容简介、目录
详情与封面阶段使用线程池并发（默认 8 线程），封面存入 resources/covers/。

目标站没有读者评分字段，为保证书目大厅星级、「读者评分」排序可用，
抓取结束后会为每本书离线合成一组演示评分与书评（见 generate_fake_ratings）。

用法:
    python crawler.py                       # 默认抓取 历史、地理(zhongtu-k) 前 16 页（含详情与封面）
    python crawler.py --pages 4             # 抓取前 4 页
    python crawler.py --workers 16          # 提高并发
    python crawler.py --category zhongtu-i  # 换分类（文学）
    python crawler.py --no-covers           # 只抓数据不下载封面
    python crawler.py --list-only           # 只抓列表页
    python crawler.py --no-fake-ratings     # 不合成演示评分
    python crawler.py --fake-only           # 不访问目标站，只给已有 JSON 重算演示评分
"""

import argparse
import csv
import json
import os
import random
import re
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

import requests
from bs4 import BeautifulSoup

_thread_local = threading.local()

# 强制 IPv4：目标站走 Cloudflare，解析器有时只返回 AAAA 记录，
# 而本机无 IPv6 出口，会导致整批请求 getaddrinfo 失败。
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = _ipv4_getaddrinfo

BASE_URL = "https://www.zhihailib.com"
CATEGORIES = {
    "zhongtu-a": "马列毛邓理论", "zhongtu-b": "哲学、宗教", "zhongtu-c": "社会科学总论",
    "zhongtu-d": "政治、法律", "zhongtu-e": "军事", "zhongtu-f": "经济",
    "zhongtu-g": "文化、科学、教育、体育", "zhongtu-h": "语言、文字", "zhongtu-i": "文学",
    "zhongtu-j": "艺术", "zhongtu-k": "历史、地理", "zhongtu-n": "自然科学总论",
    "zhongtu-o": "数理科学和化学", "zhongtu-p": "天文学、地球科学", "zhongtu-q": "生物科学",
    "zhongtu-r": "医药、卫生", "zhongtu-s": "农业科学", "zhongtu-t": "工业技术",
    "zhongtu-u": "交通运输", "zhongtu-v": "航空、航天", "zhongtu-x": "环境科学、安全科学",
    "zhongtu-z": "综合性图书",
}

FORMAT_RE = re.compile(r"^(EPUB|AZW3|MOBI|PDF|TXT)\s*(.*)$", re.I)
DATE_RE = re.compile(r"^\d{4}(-\d{2}){0,2}$")
PUBLISHER_RE = re.compile(r"出版社|出版公司|出版集团|书局|书店|杂志社|印书馆|Press|Publish", re.I)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": BASE_URL + "/",
}


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
def parse_views(text):
    """把 1k / 2.3k / 486 这类计数文本转成整数。"""
    text = (text or "").strip().lower().replace(",", "")
    if not text:
        return 0
    try:
        if text.endswith("k"):
            return int(float(text[:-1]) * 1000)
        if text.endswith("w"):
            return int(float(text[:-1]) * 10000)
        return int(float(text))
    except ValueError:
        return 0


def text_with_breaks(node):
    """取文本但保留 <br> 换行，用于目录等结构化内容。"""
    if node is None:
        return ""
    for br in node.find_all("br"):
        br.replace_with("\n")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in node.get_text("\n").split("\n")]
    return "\n".join(ln for ln in lines if ln)


def get_session():
    """每个线程持有独立 Session（requests.Session 不是线程安全的）。"""
    if not getattr(_thread_local, "session", None):
        _thread_local.session = requests.Session()
    return _thread_local.session


def fetch(url, session=None, retries=3, timeout=30):
    session = session or get_session()
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp
        except Exception as exc:
            if attempt == retries:
                print(f"  [失败] {url} -> {exc}", file=sys.stderr)
                return None
            time.sleep(attempt)
    return None


# --------------------------------------------------------------------------- #
# 解析：列表页
# --------------------------------------------------------------------------- #
def parse_excerpt(text):
    """解析 `格式 / 作者 / 出版社 / 出版日期 / 简介` 形式的摘要行。

    站点数据并不规整：格式存在 `PDF扫描版` 之类变体，作者/出版社/日期经常缺省。
    因此按特征逐段归类，而不是按固定下标取值。
    """
    parts = [p.strip() for p in re.split(r"\s+/\s+", (text or "").strip()) if p.strip()]
    if not parts:
        return {}

    fmt, fmt_note = "", ""
    m = FORMAT_RE.match(parts[0])
    if m:
        fmt = m.group(1).upper()
        fmt_note = m.group(2).strip()
        parts.pop(0)

    # 简介段落常以「内容简介」开头，其后全部视作简介
    desc_head = next((i for i, p in enumerate(parts) if p.startswith("内容简介")), None)
    if desc_head is not None:
        head, tail = parts[:desc_head], parts[desc_head:]
        publish_date = next((p for p in head if DATE_RE.match(p)), "")
        publisher = next((p for p in head if PUBLISHER_RE.search(p)), "")
        consumed = {publish_date, publisher}
        authors = [p for p in head if p not in consumed]
    else:
        date_idx = next((i for i, p in enumerate(parts) if DATE_RE.match(p)), None)
        if date_idx is not None:
            publish_date = parts[date_idx]
            publisher = parts[date_idx - 1] if date_idx >= 1 else ""
            authors = parts[: max(date_idx - 1, 0)]
            tail = parts[date_idx + 1:]
        else:
            publish_date = ""
            pub_idx = next((i for i, p in enumerate(parts) if PUBLISHER_RE.search(p)), None)
            if pub_idx is not None:
                publisher = parts[pub_idx]
                authors = parts[:pub_idx]
                tail = parts[pub_idx + 1:]
            else:
                # 无出版社也无日期：单段且较长视为简介，否则视为作者
                publisher = ""
                if len(parts) == 1 and len(parts[0]) > 25:
                    authors, tail = [], parts
                else:
                    authors, tail = parts, []

    # 0101-01-01 这类占位日期视为未知
    if publish_date.startswith("0101"):
        publish_date = ""

    desc = " / ".join(p for p in tail if p).strip()
    desc = re.sub(r"^内容简介\s*[:：]?\s*", "", desc)

    return {
        "format": fmt,
        "format_note": fmt_note,
        "author": ", ".join(a for a in authors if a),
        "publisher": publisher,
        "publish_date": publish_date,
        "description": desc,
    }


def parse_list_item(item, category_slug, category_name, page_no):
    link = item.select_one(".post-info h2 a") or item.select_one("a.thumb-link")
    if not link or not link.get("href"):
        return None

    url = link["href"]
    if url.startswith("/"):
        url = BASE_URL + url

    title = link.get_text(strip=True).replace("\u200b", "").strip()
    book_id = url.rstrip("/").rsplit("/", 1)[-1]

    img = item.select_one("img.post-thumb")
    source = item.select_one(".post-module-thumb source")
    excerpt_el = item.select_one(".post-excerpt")

    record = {
        "id": book_id,
        "title": title,
        "url": url,
        "cover_url": img.get("src") if img else "",
        "cover_webp": source.get("srcset") if source else "",
        "category_slug": category_slug,
        "category": category_name,
        "source_page": page_no,
    }
    record.update(parse_excerpt(excerpt_el.get_text(strip=True) if excerpt_el else ""))

    for key, cls in (("likes", "like"), ("comments", "comment"), ("views", "views")):
        el = item.select_one(f".post-list-meta-{cls} span")
        record[key] = parse_views(el.get_text(strip=True) if el else "0")

    return record


# --------------------------------------------------------------------------- #
# 解析：详情页
# --------------------------------------------------------------------------- #
META_MAP = {
    "作者": "author", "语言": "language", "类型": "format", "页数": "pages",
    "大小": "file_size", "出版社": "publisher", "出版时间": "publish_date",
    "ISBN": "isbn", "分类": "category",
}

# entry-content 内的站点 UI 块，必须剔除（下载控件、免责声明、捐赠区）
NOISE_CLASSES = {"download-box", "post-note", "support-section", "mg-b"}
TOC_CLASSES = {"book-toc", "toc-content", "book-toc-content"}
# 文本兜底过滤：站点 UI 文案若混入正文则整行丢弃
NOISE_LINE_RE = re.compile(
    r"下载权限|免费下载|登录后下载|评论并刷新|查看演示|您当前的等级|小黑屋反思|"
    r"升级会员|以后下载|立即支付|网盘链接如果失效|您已获得下载权限|登录后免费下载"
)


def clean_lines(text):
    """按行剔除站点 UI 文案。"""
    lines = [ln.strip() for ln in (text or "").split("\n")]
    return "\n".join(ln for ln in lines if ln and not NOISE_LINE_RE.search(ln))


def parse_detail(html):
    """解析详情页：meta-row 字段表 + 内容简介/作者简介/目录 三段正文。

    entry-content 的直接子元素才是正文（h2 分段标题、p 段落、div 仅可能为目录容器），
    内嵌的站点 UI 块（download-box / post-note / support-section）一律丢弃。
    """
    soup = BeautifulSoup(html, "lxml")
    detail = {}

    for row in soup.select(".meta-row"):
        label = row.select_one(".meta-label")
        value = row.select_one(".meta-value")
        if not label or not value:
            continue
        key = label.get_text(strip=True).rstrip("：:").strip()
        val = value.get_text(" ", strip=True)
        if key in META_MAP:
            detail[META_MAP[key]] = val

    # 封面（详情页图中通常比列表页清晰）
    cover = soup.select_one("img.book-cover-img")
    if cover and cover.get("src"):
        detail["cover_url"] = cover["src"]

    # 正文分段：只遍历直接子元素
    entry = soup.select_one(".entry-content")
    if entry:
        sections = {}
        current = None
        for node in entry.children:
            name = getattr(node, "name", None)
            if not name:
                continue

            if name in ("h2", "h3"):
                current = node.get_text(strip=True)
                sections.setdefault(current, [])
                continue
            if current is None:
                continue

            classes = set(node.get("class") or [])
            if classes & NOISE_CLASSES:
                continue

            if name == "div":
                # div 仅接受目录容器，其余（未知 UI 块）丢弃
                toc = node if classes & TOC_CLASSES else node.select_one(".book-toc, .toc-content")
                if toc is not None:
                    text = clean_lines(text_with_breaks(toc))
                    if text:
                        sections[current].append(text)
                continue

            text = clean_lines(text_with_breaks(node))
            if text:
                sections[current].append(text)

        def section_text(keyword):
            for name, chunks in sections.items():
                if keyword in name:
                    return "\n".join(chunks).strip()
            return ""

        detail["description"] = section_text("内容简介")
        detail["author_bio"] = section_text("作者简介")
        detail["toc"] = section_text("目录")

    # meta description 兜底（含作者/出版社/日期/语言/格式/大小）
    meta_desc = soup.select_one('meta[name="description"]')
    if meta_desc and meta_desc.get("content"):
        content = meta_desc["content"]
        pairs = {"作者": "author", "出版社": "publisher", "出版日期": "publish_date",
                 "语言": "language", "文件格式": "format", "文件大小": "file_size"}
        for cn, en in pairs.items():
            m = re.search(rf"{cn}[:：]\s*([^,，]+)", content)
            if m and not detail.get(en):
                detail[en] = m.group(1).strip()

    return {k: v for k, v in detail.items() if v}


# --------------------------------------------------------------------------- #
# 封面下载
# --------------------------------------------------------------------------- #
def download_cover(url, dest_dir, book_id, timeout=30):
    """下载封面到 dest_dir，返回保存的文件名（失败返回空串）。已存在的文件跳过。"""
    if not url:
        return ""
    ext = os.path.splitext(url.split("?")[0])[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    filename = f"{book_id}{ext}"
    path = os.path.join(dest_dir, filename)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return filename
    try:
        resp = get_session().get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        if len(resp.content) < 512:
            return ""
        with open(path, "wb") as f:
            f.write(resp.content)
        return filename
    except Exception as exc:
        print(f"  [封面失败] {book_id} -> {exc}", file=sys.stderr)
        return ""


# --------------------------------------------------------------------------- #
# 演示评分与书评合成（离线生成，不来自目标站）
#
# 目标站只暴露浏览量/点赞/评论数，没有读者评分。而书目大厅的星级、
# 「读者评分」排序都依赖 Book.rating / Book.rating_count 聚合值。
# 这里按 book id 派生确定性伪随机序列，为每本书合成一组整数星级书评，
# 并令 rating = 这组书评的均值、rating_count = 书评条数，
# 保证「平均分 / 评价人数 / 书评列表」三者完全自洽（不会出现有分数没书评）。
# --------------------------------------------------------------------------- #
REVIEW_TEXTS = {
    5: [
        "内容扎实、结构清晰，读完收获很大，强烈推荐。",
        "经典之作，值得反复翻阅，每次都有新的体会。",
        "论证透彻，资料翔实，同类读物里最好的之一。",
        "非常喜欢，已经推荐给同学一起读了。",
        "从入门到进阶都合适，可读性很强。",
        "观点新颖，案例丰富，几乎一口气读完。",
    ],
    4: [
        "整体不错，个别章节略显冗长。",
        "内容有价值，翻译偶有生硬之处。",
        "值得一读，少数观点可以商榷。",
        "脉络清楚，案例贴切，读起来比较顺畅。",
        "有启发，但深度还可以再挖一挖。",
        "适合作为入门参考，推荐阅读。",
    ],
    3: [
        "中规中矩，翻翻即可，不必精读。",
        "内容尚可，但同题材里有更好的选择。",
        "前几章精彩，后面略显注水。",
        "开卷有益，但谈不上惊艳。",
        "当作消遣读物还可以。",
    ],
    2: [
        "内容偏浅，与预期差距较大。",
        "信息量一般，重复内容较多。",
        "校对和排版有些问题，阅读体验一般。",
    ],
}

# 合成书评的虚拟评分人数量：同一本书内的评分人互不重复，
# 导入脚本会按 slot 映射到对应数量的演示读者账号。
FAKE_REVIEWER_COUNT = 12


def generate_fake_ratings(books, seed=20261013, min_reviews=2, max_reviews=9):
    """为每本书补上 {rating, rating_count, reviews} 三个字段（原地修改）。

    reviews 元素为 {reviewer_slot, rating, content, days_ago}，
    其中 reviewer_slot ∈ [0, FAKE_REVIEWER_COUNT) 且同书内唯一，
    以便导入时落在不同的读者账号上（reviews 表对 (user_id, book_id) 有唯一约束）。
    """
    for book in books:
        rng = random.Random(f"{seed}:{book.get('id')}")
        n = rng.randint(min_reviews, max_reviews)

        # 浏览量高的书略微偏高分：热门读物口碑更稳
        hot = min(int(book.get("views") or 0), 8000) / 8000
        stars = rng.choices([5, 4, 3, 2, 1], weights=[42 + 8 * hot, 34, 15, 6, 3], k=n)

        slots = rng.sample(range(FAKE_REVIEWER_COUNT), n)
        used_texts = set()
        reviews = []
        for slot, star in zip(slots, stars):
            pool = REVIEW_TEXTS.get(star, REVIEW_TEXTS[4])
            fresh = [t for t in pool if t not in used_texts]
            text = rng.choice(fresh or pool)  # 同书内尽量不重复文案
            used_texts.add(text)
            reviews.append({
                "reviewer_slot": slot,
                "rating": star,
                "content": text,
                "days_ago": rng.randint(1, 420),
            })
        book["reviews"] = reviews
        # 与后端 services/reviews.py 的 quantize(0.01, ROUND_HALF_UP) 保持一致，
        # 保证「显示的平均分」与「重算平均分」完全相等
        avg = (Decimal(sum(stars)) / Decimal(n)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        book["rating"] = float(avg)
        book["rating_count"] = n

    return books


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def save(books, out_dir, category_slug, category_name, pages, total_pages, extra):
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"{category_slug}_books.json")
    csv_path = os.path.join(out_dir, f"{category_slug}_books.csv")

    payload = {
        "source": BASE_URL,
        "category": category_name,
        "category_slug": category_slug,
        "pages_crawled": pages,
        "total_pages_available": total_pages,
        "total": len(books),
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    payload.update(extra)
    payload["books"] = books
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    cols = ["id", "title", "author", "author_bio", "language", "format", "format_note",
            "pages", "file_size", "publisher", "publish_date", "isbn", "category",
            "description", "toc", "cover_file", "cover_url", "url",
            "likes", "comments", "views", "rating", "rating_count", "source_page"]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(books)

    return json_path, csv_path


def process_book(book, with_detail, with_covers, covers_dir, cover_delay):
    """单个书籍的详情抓取 + 封面下载，供线程池调用。原地更新 book。"""
    result = {"detail": False, "cover": False}

    if with_detail:
        resp = fetch(book["url"])
        if resp is not None:
            info = parse_detail(resp.text)
            # 详情页字段更权威，覆盖列表页解析结果
            for key, value in info.items():
                if key == "format":
                    book["format"] = value.split()[0].upper() if value else book.get("format", "")
                else:
                    book[key] = value
            result["detail"] = True

    if with_covers:
        name = download_cover(book.get("cover_url"), covers_dir, book["id"])
        book["cover_file"] = name
        result["cover"] = bool(name)
        if cover_delay:
            time.sleep(cover_delay)

    return result


def crawl(category_slug, pages, delay, out_dir, with_detail, with_covers, cover_delay, workers,
          with_fake=True):
    category_name = CATEGORIES.get(category_slug, category_slug)
    session = requests.Session()
    books, seen = [], set()
    total_pages = None
    covers_dir = os.path.join(out_dir, "covers")

    print(f"分类: {category_name} ({category_slug})    列表页: 1-{pages}    间隔: {delay}s")
    print("-" * 62)

    # 阶段一：列表页（仅 16 个请求，顺序抓取）
    for page_no in range(1, pages + 1):
        url = f"{BASE_URL}/book/{category_slug}/page/{page_no}"
        print(f"[列表 {page_no}/{pages}] {url}")
        resp = fetch(url, session)
        if resp is None:
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        if total_pages is None:
            nav = soup.select_one(".b2-pagenav [pages]")
            if nav:
                total_pages = int(nav["pages"])

        items = soup.select("li.post-list-item")
        added = 0
        for item in items:
            record = parse_list_item(item, category_slug, category_name, page_no)
            if not record or record["id"] in seen:
                continue
            seen.add(record["id"])
            books.append(record)
            added += 1
        print(f"          解析 {len(items)} 条，新增 {added} 条，累计 {len(books)} 条")

        if page_no < pages:
            time.sleep(delay)

    if not books:
        print("未抓取到任何数据", file=sys.stderr)
        return []

    # 合成演示评分与书评（目标站无评分字段）
    extra = {"fake_ratings": with_fake}
    if with_fake:
        generate_fake_ratings(books)
        print("-" * 62)
        print(f"已为 {len(books)} 本书合成演示评分与书评"
              f"（每本 2-9 条，评分 {min(b['rating'] for b in books):.2f}"
              f"~{max(b['rating'] for b in books):.2f}）")

    # 阶段二：详情页 + 封面，线程池并发
    if with_detail or with_covers:
        os.makedirs(covers_dir, exist_ok=True)
        print("-" * 62)
        print(f"开始并发抓取详情页（{len(books)} 本，{workers} 线程）"
              f"{'，同时下载封面' if with_covers else ''}")
        stats = {"detail_ok": 0, "detail_fail": 0, "cover_ok": 0, "cover_fail": 0}
        started = time.time()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(process_book, b, with_detail, with_covers, covers_dir, cover_delay)
                for b in books
            ]
            for done, future in enumerate(as_completed(futures), start=1):
                res = future.result()
                if with_detail:
                    stats["detail_ok" if res["detail"] else "detail_fail"] += 1
                if with_covers:
                    stats["cover_ok" if res["cover"] else "cover_fail"] += 1

                if done % 25 == 0 or done == len(books):
                    elapsed = time.time() - started
                    rate = done / elapsed if elapsed else 0
                    eta = (len(books) - done) / rate if rate else 0
                    print(f"  [{done}/{len(books)}] 详情成功 {stats['detail_ok']} / 失败 {stats['detail_fail']}"
                          f"    封面成功 {stats['cover_ok']} / 失败 {stats['cover_fail']}"
                          f"    {rate:.1f} 本/秒  剩余 {eta:.0f}s")
                    save(books, out_dir, category_slug, category_name, pages, total_pages, extra)

        print("-" * 62)

    json_path, csv_path = save(books, out_dir, category_slug, category_name, pages, total_pages, extra)
    print(f"\n完成: {len(books)} 条书目")
    print(f"  JSON   -> {json_path}")
    print(f"  CSV    -> {csv_path}")
    if with_covers:
        print(f"  封面   -> {covers_dir}")
    return books


def main():
    parser = argparse.ArgumentParser(description="知海图书馆分类书目爬虫")
    parser.add_argument("--category", default="zhongtu-k",
                        help="中图分类代号，默认 zhongtu-k（历史、地理）")
    parser.add_argument("--pages", type=int, default=16, help="抓取页数，默认 16")
    parser.add_argument("--delay", type=float, default=1.5, help="列表页请求间隔秒数，默认 1.5")
    parser.add_argument("--cover-delay", type=float, default=0.2,
                        help="每个线程下载封面后的间隔秒数，默认 0.2（0 表示不限速）")
    parser.add_argument("--workers", type=int, default=8, help="并发线程数，默认 8")
    parser.add_argument("--out", default=None, help="输出目录，默认 ../resources")
    parser.add_argument("--list-only", action="store_true", help="只抓列表页，不抓详情")
    parser.add_argument("--no-covers", action="store_true", help="不下载封面")
    parser.add_argument("--no-fake-ratings", action="store_true", help="不合成演示评分与书评")
    parser.add_argument("--fake-only", action="store_true",
                        help="不访问目标站，仅对已抓取的 JSON 重新合成演示评分")
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = args.out or os.path.join(os.path.dirname(here), "resources")

    if args.fake_only:
        json_path = os.path.join(out_dir, f"{args.category}_books.json")
        if not os.path.exists(json_path):
            raise SystemExit(f"[错误] 未找到已抓取数据: {json_path}")
        with open(json_path, encoding="utf-8") as f:
            payload = json.load(f)
        books = payload.get("books") or []
        generate_fake_ratings(books)
        save(books, out_dir, args.category, payload.get("category"),
             payload.get("pages_crawled") or 0, payload.get("total_pages_available"),
             {"fake_ratings": True, "fake_only": True})
        print(f"完成: 已为 {len(books)} 本书重算演示评分与书评（未访问目标站）")
        return

    crawl(
        category_slug=args.category,
        pages=args.pages,
        delay=args.delay,
        out_dir=out_dir,
        with_detail=not args.list_only,
        with_covers=not args.no_covers and not args.list_only,
        cover_delay=args.cover_delay,
        workers=args.workers,
        with_fake=not args.no_fake_ratings,
    )


if __name__ == "__main__":
    main()