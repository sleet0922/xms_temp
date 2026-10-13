"""电子馆藏导入脚本：把爬虫产物 resources/zhongtu-k_books.json 灌入图书馆数据库

用法：
    .venv\\Scripts\\python.exe pc\\import_books.py            # 全量导入（幂等，可反复执行）
    .venv\\Scripts\\python.exe pc\\import_books.py --dry-run  # 只做统计分类，不写库

处理内容：
    1) 分类映射：按标题/简介/目录关键词把电子书归入馆内六大分类
    2) 书架分配：按分类落到对应阅览室书架
    3) 复本与条码：每本生成 3 册可借复本，条码 BK-{年月}-{书号}-{序号}
    4) 封面托管：resources/covers/*.jpg → backend/static/covers/，并写入 cover_file
    5) 演示评分：写入爬虫合成的 rating/rating_count，并把 reviews 落成真实书评行
    6) 幂等：按 source_url（缺失时用 书名+作者）去重，已存在的书目跳过
"""
import argparse
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from auth import get_password_hash  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402
from models import Book, BookCopy, Category, Review, ShelfLocation, User  # noqa: E402

JSON_PATH = ROOT / "resources" / "zhongtu-k_books.json"
COVERS_SRC = ROOT / "resources" / "covers"
COVERS_DST = BACKEND / "static" / "covers"

COPIES_PER_BOOK = 3  # 电子馆藏复本数（支持并发借阅演示）

# 演示评分人：爬虫合成的书评按 reviewer_slot 落到这些账号上。
# 数量必须 >= crawler.py 的 FAKE_REVIEWER_COUNT，且同书内 slot 唯一
# （reviews 表对 (user_id, book_id) 有唯一约束）。
FAKE_REVIEWERS = [
    ("demo_reader01", "李静"), ("demo_reader02", "王强"), ("demo_reader03", "陈晨"),
    ("demo_reader04", "赵敏"), ("demo_reader05", "刘洋"), ("demo_reader06", "孙丽"),
    ("demo_reader07", "周杰"), ("demo_reader08", "吴倩"), ("demo_reader09", "郑凯"),
    ("demo_reader10", "冯雪"), ("demo_reader11", "许阳"), ("demo_reader12", "何雨"),
]
FAKE_REVIEWER_PASSWORD = "admin123"  # 与其它演示账号一致


def ensure_fake_reviewers(db):
    """确保演示评分人账号存在（幂等），返回 slot -> User 映射"""
    reviewers = {}
    for slot, (username, full_name) in enumerate(FAKE_REVIEWERS):
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(
                username=username,
                email=f"{username}@demo.library",
                full_name=full_name,
                phone="",
                hashed_password=get_password_hash(FAKE_REVIEWER_PASSWORD),
                role="reader",
                card_number=f"CARD-97{slot + 1:04d}",
                max_borrow_limit=5,
                balance=Decimal("0.00"),
                status="active",
            )
            db.add(user)
            db.flush()
        reviewers[slot] = user
    return reviewers

# 分类关键词表：命中越多得分越高，全无命中时归入「历史传记」
CATEGORY_KEYWORDS = {
    "TP3": ["计算机", "编程", "程序", "算法", "数据", "人工智能", "互联网", "软件", "网络",
            "机器学习", "深度学习", "芯片", "科技", "计算", "代码", "系统架构", "数字化"],
    "F2": ["经济", "管理", "商业", "金融", "投资", "企业", "市场", "营销", "财务", "贸易",
           "货币", "创业", "领导力", "组织", "战略", "品牌", "财富"],
    "I2": ["小说", "文学", "散文", "诗歌", "随笔", "文集", "戏剧", "译本", "作家", "叙事"],
    "N0": ["物理", "数学", "化学", "生物", "天文", "宇宙", "自然", "医学", "生命", "地质",
           "物种", "进化", "生态", "脑", "基因", "气候"],
    "B0": ["哲学", "心理", "思维", "认知", "逻辑", "伦理", "宗教", "心智", "意识", "禅",
           "幸福", "情绪", "自我"],
    "K2": ["历史", "地理", "传", "战争", "帝国", "王朝", "文明", "考古", "民族", "政治",
           "社会", "革命", "丝绸之路", "大航海"],
}

# 分类 → 书架编码（与 init_db 种子书架一一对应）
LOCATION_BY_CATEGORY = {
    "TP3": "A-1F-01",
    "F2": "B-1F-01",
    "I2": "C-2F-01",
    "K2": "C-2F-02",
    "N0": "D-2F-01",
    "B0": "C-2F-02",
}

DEFAULT_CATEGORY = "K2"


# 高频通用词：只在标题里计分，避免简介中的泛化用词把书目误判成历史类
GENERIC_WORDS = {"传", "社会", "政治", "民族", "历史", "文化", "科技", "数据", "自然"}


def classify(record: dict) -> str:
    """按关键词命中数归类，标题权重更高；无有效信号时归入默认分类"""
    title = (record.get("title") or "")
    body = " ".join([
        record.get("description") or "",
        record.get("toc") or "",
        record.get("author_bio") or "",
        record.get("category") or "",
    ])
    scores = {}
    for code, words in CATEGORY_KEYWORDS.items():
        score = 0
        for w in words:
            if w in title:
                score += 5
            elif w not in GENERIC_WORDS:
                score += body.count(w)
        scores[code] = score

    best_code, best_score = max(scores.items(), key=lambda kv: kv[1])
    return best_code if best_score > 0 else DEFAULT_CATEGORY


def normalize_format(raw) -> str:
    fmt = (raw or "").strip().upper()
    if fmt.startswith("PDF"):
        return "PDF"
    return fmt or "EPUB"


def to_int(value, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def import_books(dry_run: bool = False) -> None:
    if not JSON_PATH.exists():
        raise SystemExit(f"[错误] 未找到爬虫数据文件: {JSON_PATH}")

    payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    records = payload["books"] if isinstance(payload, dict) else payload
    print(f"[读取] {JSON_PATH.name} 共 {len(records)} 条电子馆藏记录")

    cat_counter = Counter(classify(r) for r in records)
    if dry_run:
        code_name = {}
        print("[分类映射统计]", {f"{code}:{cnt}" for code, cnt in cat_counter.items()})
        return

    Base.metadata.create_all(bind=engine)
    COVERS_DST.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        cats = {c.code: c for c in db.query(Category).all()}
        locs = {l.code: l for l in db.query(ShelfLocation).all()}
        if not cats:
            raise SystemExit("[错误] 数据库缺少分类数据，请先执行 backend/init_db.py")

        reviewers = ensure_fake_reviewers(db)

        existing_urls = {u for (u,) in db.query(Book.source_url).filter(Book.source_url.isnot(None)).all()}
        existing_keys = {(t, a) for t, a in db.query(Book.title, Book.author).all()}
        used_isbns = {i for (i,) in db.query(Book.isbn).filter(Book.isbn.isnot(None)).all()}

        now = datetime.now()
        barcode_month = now.strftime("%Y%m")

        created = skipped = cover_copied = review_created = 0
        for rec in records:
            title = (rec.get("title") or "").strip()
            author = (rec.get("author") or "佚名").strip()
            source_url = rec.get("url")
            if not title:
                continue
            if source_url and source_url in existing_urls:
                skipped += 1
                continue
            if not source_url and (title, author) in existing_keys:
                skipped += 1
                continue

            code = classify(rec)
            category = cats.get(code) or cats.get(DEFAULT_CATEGORY)
            location = locs.get(LOCATION_BY_CATEGORY.get(code, ""))

            cover_file = (rec.get("cover_file") or "").strip()
            if cover_file:
                src = COVERS_SRC / cover_file
                dst = COVERS_DST / cover_file
                if src.exists() and not dst.exists():
                    shutil.copy2(src, dst)
                    cover_copied += 1
                if not dst.exists():
                    cover_file = None

            isbn = (rec.get("isbn") or "").strip() or None
            if isbn and isbn in used_isbns:
                isbn = None
            if isbn:
                used_isbns.add(isbn)

            fmt = normalize_format(rec.get("format"))
            raw_category = (rec.get("category") or "").strip()

            # 合成书评：同一本书内 slot 去重，避免撞 (user_id, book_id) 唯一约束
            review_rows, seen_slots = [], set()
            for rv in (rec.get("reviews") or []):
                slot = to_int(rv.get("reviewer_slot"), 0) % len(FAKE_REVIEWERS)
                if slot in seen_slots:
                    continue
                seen_slots.add(slot)
                review_rows.append((slot, rv))

            if review_rows:
                rating_value = Decimal(str(rec.get("rating") or 0))
                rating_count_value = len(review_rows)
            else:
                rating_value, rating_count_value = Decimal("0.00"), 0

            book = Book(
                title=title[:200],
                author=author[:100],
                isbn=isbn,
                publisher=(rec.get("publisher") or None),
                publish_date=(rec.get("publish_date") or None),
                category_id=category.id if category else None,
                location_id=location.id if location else None,
                price=0,
                description=rec.get("description"),
                cover_url=rec.get("cover_url"),
                cover_file=cover_file,
                tags=",".join(x for x in [raw_category, fmt, rec.get("language") or ""] if x),
                language=(rec.get("language") or None),
                format=fmt,
                pages=to_int(rec.get("pages")) or None,
                file_size=(rec.get("file_size") or None),
                toc=rec.get("toc"),
                author_bio=rec.get("author_bio"),
                source_url=source_url,
                source_views=to_int(rec.get("views")),
                source_likes=to_int(rec.get("likes")),
                source_comments=to_int(rec.get("comments")),
                rating=rating_value,
                rating_count=rating_count_value,
                total_copies=COPIES_PER_BOOK,
                available_copies=COPIES_PER_BOOK,
                borrow_count=0,
            )
            db.add(book)
            db.flush()

            for i in range(1, COPIES_PER_BOOK + 1):
                db.add(BookCopy(
                    book_id=book.id,
                    barcode=f"BK-{barcode_month}-{book.id:04d}-{i:02d}",
                    status="available",
                    condition_status="good",
                    location_note=f"电子馆藏复本 · {location.name if location else '综合阅览'}",
                ))

            # 合成书评落库，时间回填到过去，让书评列表有先后顺序
            for slot, rv in review_rows:
                created_at = now - timedelta(days=to_int(rv.get("days_ago"), 1))
                db.add(Review(
                    user_id=reviewers[slot].id,
                    book_id=book.id,
                    rating=max(1, min(5, to_int(rv.get("rating"), 5))),
                    content=rv.get("content"),
                    is_hidden=False,
                    created_at=created_at,
                    updated_at=created_at,
                ))
                review_created += 1

            if source_url:
                existing_urls.add(source_url)
            existing_keys.add((title, author))
            created += 1

            if created % 50 == 0:
                db.commit()
                print(f"  ... 已写入 {created} 本")

        db.commit()
        total_books = db.query(Book).count()
        total_copies = db.query(BookCopy).count()
        total_reviews = db.query(Review).count()
        rated = db.query(Book).filter(Book.rating_count > 0).count()
        print(f"[完成] 新增书目 {created} 本，跳过已存在 {skipped} 本，"
              f"新增封面 {cover_copied} 张，新增书评 {review_created} 条")
        print(f"[统计] 当前馆藏: 书目 {total_books} 种 / 复本 {total_copies} 册 / 书评 {total_reviews} 条")
        print(f"[评分] 已合成评分书目 {rated} 本（演示评分人 {len(FAKE_REVIEWERS)} 个）")
        print(f"[分类] 本次归类分布: {dict(cat_counter)}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导入爬取的电子馆藏数据")
    parser.add_argument("--dry-run", action="store_true", help="仅统计分类结果，不写入数据库")
    args = parser.parse_args()
    import_books(dry_run=args.dry_run)