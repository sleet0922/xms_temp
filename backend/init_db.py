"""SQLite 数据库初始化：建表 + 灌入演示种子数据（幂等，可反复执行）"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Base, engine, SessionLocal, DATABASE_URL
from models import (
    User, Book, BookCopy, BorrowRecord, Reservation,
    FineRecord, Category, ShelfLocation, Announcement,
    AuditLog, SystemSetting
)
from auth import get_password_hash

DEFAULT_PASSWORD = "admin123"

SETTINGS = [
    ("library_name", "未来智慧云图书馆", "图书馆全局名称"),
    ("default_borrow_days", "30", "默认借阅天数"),
    ("max_renew_times", "2", "最大允许续借次数"),
    ("renew_days", "15", "每次续借延长天数"),
    ("daily_fine_rate", "0.50", "每日逾期罚金(元/天)"),
    ("max_borrow_books", "8", "普通读者最大借阅本数"),
    ("reservation_expire_days", "7", "预约到书后的保留天数"),
    ("due_reminder_days", "3", "借阅到期前提醒天数"),
]

CATEGORIES = [
    ("计算机与AI", "TP3", "软件开发、算法数据结构、人工智能大模型", "mdi-laptop"),
    ("文学小说", "I2", "中外文学经典、现代当代小说、散文诗歌", "mdi-book-open-page-variant"),
    ("历史传记", "K2", "世界通史、人物传记、中国历史断代史", "mdi-history"),
    ("经济与管理", "F2", "商业金融、经济学理论、企业经营管理", "mdi-chart-line"),
    ("自然科学", "N0", "数学物理、宇宙探索、生命科学前沿", "mdi-atom"),
    ("哲学心理", "B0", "认知心理学、中西方哲学典籍、思维模型", "mdi-head-heart"),
]

LOCATIONS = [
    ("A区科技阅览室 01架", "A-1F-01", "1楼", "计算机、人工智能前沿专架"),
    ("A区科技阅览室 02架", "A-1F-02", "1楼", "软件工程、操作系统网络专架"),
    ("B区社科经管 01架", "B-1F-01", "1楼", "经济学、商业管理综合书架"),
    ("C区文学经典 01架", "C-2F-01", "2楼", "国内外名著长篇小说架"),
    ("C区人文社科 02架", "C-2F-02", "2楼", "历史、哲学与心理学书架"),
    ("D区综合阅览 01架", "D-2F-01", "2楼", "科普读物、自然科学精品架"),
]

# username, email, full_name, phone, role, card_number, max_borrow_limit, balance
USERS = [
    ("admin", "admin@future-lib.com", "超级系统管理员", "13800000001", "admin", "CARD-888801", 20, "100.00"),
    ("librarian", "librarian@future-lib.com", "王馆员 (服务台)", "13800000002", "librarian", "CARD-888802", 15, "50.00"),
    ("student", "student@future-lib.com", "李同学 (读者)", "13800000003", "reader", "CARD-202601", 8, "20.00"),
    ("zhangsan", "zhangsan@future-lib.com", "张三 (研一)", "13800000004", "reader", "CARD-202602", 8, "0.00"),
    ("lisi", "lisi@future-lib.com", "李四 (学者)", "13800000005", "reader", "CARD-202603", 10, "50.00"),
]

# title, author, isbn, publisher, publish_date, category_idx, location_idx, price, description, cover_url, tags, total, available, borrow_count
BOOKS = [
    ("深度学习与大模型导论", "Ian Goodfellow / Yoshua Bengio", "9787115461471", "人民邮电出版社", "2024-03", 1, 1, "128.00",
     "大模型时代必读圣经，全面涵盖Transformer、自监督学习、强化学习与多模态架构设计。",
     "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400", "人工智能,大模型,机器学习", 4, 3, 28),
    ("Python高级编程架构实战", "Luciano Ramalho", "9787115454157", "人民邮电出版社", "2023-08", 1, 2, "99.00",
     "深入理解 Python 语言精髓，涵盖元编程、并发与异步IO、数据模型与性能极致调优。",
     "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400", "Python,架构,后端开发", 3, 2, 19),
    ("云原生架构设计：容器与微服务", "Brendan Burns", "9787111649984", "机械工业出版社", "2023-11", 1, 2, "89.00",
     "Kubernetes与微服务分布式系统权威指南，由K8s联合创始人倾力打造。",
     "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400", "云原生,Docker,微服务", 3, 3, 14),
    ("百年孤独 (精装典藏版)", "加夫列尔·加西亚·马尔克斯", "9787544253994", "南海出版公司", "2022-01", 2, 4, "68.00",
     "魔幻现实主义文学巅峰之作，讲述布恩迪亚家族七代人的传奇故事与孤独宿命。",
     "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400", "诺贝尔文学奖,经典名著,小说", 5, 4, 45),
    ("三体全集 (1-3部)", "刘慈欣", "9787536692930", "重庆出版社", "2021-06", 2, 4, "98.00",
     "中国科幻里程碑巨著，雨果奖获奖作品，展现宏伟苍凉的宇宙文明兴衰图景。",
     "https://images.unsplash.com/photo-1532012164546-f432f2e3777f?w=400", "科幻,雨果奖,硬核科幻", 6, 4, 62),
    ("人类简史：从动物到上帝", "尤瓦尔·赫拉利", "9787508647357", "中信出版社", "2022-09", 3, 5, "75.00",
     "打破学科边界，从认知革命、农业革命到科学革命，重新认知人类演化宏大历程。",
     "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=400", "历史,演化,社会学", 4, 3, 37),
    ("原则 (Life and Work Principles)", "瑞·达利欧 (Ray Dalio)", "9787508684031", "中信出版社", "2021-04", 4, 3, "98.00",
     "桥水基金创始人瑞·达利欧数十载人生与投资管理核心心法，极度求真与极度透明。",
     "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=400", "投资,商业管理,个人成长", 3, 2, 25),
    ("思考，快与慢", "丹尼尔·卡尼曼", "9787508633557", "中信出版社", "2022-05", 6, 5, "69.00",
     "诺贝尔经济学奖得主开创性巨作，系统1与系统2的认知机制揭示人类决策盲区。",
     "https://images.unsplash.com/photo-1507842229456-8a7e08e6c43d?w=400", "行为经济学,心理学,认知", 4, 4, 31),
]

# book_idx, barcode, status, condition_status, location_note
COPIES = [
    (1, "BK-2026-0101", "available", "good", "A-1F-01-A"),
    (1, "BK-2026-0102", "available", "good", "A-1F-01-A"),
    (1, "BK-2026-0103", "borrowed", "good", "借阅流转中"),
    (1, "BK-2026-0104", "available", "good", "A-1F-01-A"),
    (2, "BK-2026-0201", "available", "good", "A-1F-02-B"),
    (2, "BK-2026-0202", "borrowed", "good", "借阅流转中"),
    (2, "BK-2026-0203", "available", "good", "A-1F-02-B"),
    (3, "BK-2026-0301", "available", "good", "A-1F-02-C"),
    (3, "BK-2026-0302", "available", "good", "A-1F-02-C"),
    (3, "BK-2026-0303", "available", "good", "A-1F-02-C"),
    (4, "BK-2026-0401", "available", "good", "C-2F-01-A"),
    (4, "BK-2026-0402", "available", "good", "C-2F-01-A"),
    (4, "BK-2026-0403", "available", "good", "C-2F-01-A"),
    (4, "BK-2026-0404", "borrowed", "good", "借阅流转中"),
    (4, "BK-2026-0405", "available", "minor_damage", "C-2F-01-A"),
    (5, "BK-2026-0501", "available", "good", "C-2F-01-B"),
    (5, "BK-2026-0502", "borrowed", "good", "借阅流转中 (逾期)"),
    (5, "BK-2026-0503", "borrowed", "good", "借阅流转中"),
    (5, "BK-2026-0504", "available", "good", "C-2F-01-B"),
    (5, "BK-2026-0505", "available", "good", "C-2F-01-B"),
    (5, "BK-2026-0506", "available", "good", "C-2F-01-B"),
    (6, "BK-2026-0601", "available", "good", "C-2F-02-A"),
    (6, "BK-2026-0602", "borrowed", "good", "借阅流转中"),
    (6, "BK-2026-0603", "available", "good", "C-2F-02-A"),
    (6, "BK-2026-0604", "available", "good", "C-2F-02-A"),
    (7, "BK-2026-0701", "available", "good", "B-1F-01-A"),
    (7, "BK-2026-0702", "borrowed", "good", "借阅流转中"),
    (7, "BK-2026-0703", "available", "good", "B-1F-01-A"),
    (8, "BK-2026-0801", "available", "good", "C-2F-02-B"),
    (8, "BK-2026-0802", "available", "good", "C-2F-02-B"),
    (8, "BK-2026-0803", "available", "good", "C-2F-02-B"),
    (8, "BK-2026-0804", "available", "good", "C-2F-02-B"),
]

# username, book_idx, copy_barcode, borrow_days(负数为过去), due_days, return_days(None 表示未还), renew_count, status, notes
BORROWS = [
    ("student", 1, "BK-2026-0103", -10, 20, None, 0, "borrowed", "正常借出"),
    ("student", 2, "BK-2026-0202", -5, 25, None, 0, "borrowed", "正常借出"),
    ("student", 4, "BK-2026-0401", -40, -10, -12, 1, "returned", "提前按期归还完好"),
    ("zhangsan", 5, "BK-2026-0502", -35, -5, None, 0, "overdue", "逾期未还，已触发欠费计算"),
    ("lisi", 6, "BK-2026-0602", -12, 18, None, 1, "borrowed", "已办理一次延期续借"),
    ("lisi", 7, "BK-2026-0702", -3, 27, None, 0, "borrowed", "前台自助借阅"),
]

ANNOUNCEMENTS = [
    ("关于2026秋季学期图书馆开放时间延长的通知",
     "为满足全校师生科研学习需求，自即日起科技阅览区开放时间延长至每晚 23:30，欢迎各位读者自习阅览。",
     "important", "admin"),
    ("智慧图书借还一体化服务系统正式上线",
     "全馆支持实体条形码扫描快速借还、个人中心在线续借与图书排队预约功能。如遇借阅问题请前往 1 楼服务台咨询。",
     "normal", "admin"),
    ("关于逾期图书归还及免罚周活动的温馨提示",
     "本月最后一周将开展“图书关怀周”活动，活动期间归还所有逾期图书均可申请免收滞纳金，请持有逾期图书的读者及时前往还书。",
     "urgent", "librarian"),
]

AUDIT_LOGS = [
    ("admin", "SYSTEM_INIT", "DATABASE", "ALL", "系统首次初始化数据表与基础种子数据加载完成"),
    ("admin", "CONFIG_UPDATE", "SETTINGS", "RULES", "更新借阅期限与逾期罚款费率"),
    ("librarian", "BOOK_IMPORT", "BOOK", "1-8", "完成首批8部科技人文典藏书目采编入库"),
]


def seed(db):
    now = datetime.now()
    day = lambda n: now + timedelta(days=n)

    for key, value, desc in SETTINGS:
        db.add(SystemSetting(setting_key=key, setting_value=value, description=desc))

    for name, code, desc, icon in CATEGORIES:
        db.add(Category(name=name, code=code, description=desc, icon=icon))

    for name, code, floor, desc in LOCATIONS:
        db.add(ShelfLocation(name=name, code=code, floor=floor, description=desc))

    db.flush()

    pwd_hash = get_password_hash(DEFAULT_PASSWORD)
    for username, email, full_name, phone, role, card_no, limit, balance in USERS:
        db.add(User(
            username=username, email=email, full_name=full_name, phone=phone,
            hashed_password=pwd_hash, role=role, card_number=card_no,
            max_borrow_limit=limit, balance=Decimal(balance), status="active"
        ))

    for (title, author, isbn, publisher, publish_date, cat_idx, loc_idx, price,
         description, cover_url, tags, total, available, borrow_count) in BOOKS:
        db.add(Book(
            title=title, author=author, isbn=isbn, publisher=publisher, publish_date=publish_date,
            category_id=cat_idx, location_id=loc_idx, price=Decimal(price), description=description,
            cover_url=cover_url, tags=tags, total_copies=total, available_copies=available,
            borrow_count=borrow_count
        ))

    for book_idx, barcode, status, condition, note in COPIES:
        db.add(BookCopy(book_id=book_idx, barcode=barcode, status=status,
                        condition_status=condition, location_note=note))

    db.flush()

    user_ids = {u.username: u.id for u in db.query(User).all()}
    copy_ids = {c.barcode: c.id for c in db.query(BookCopy).all()}
    librarian_id = user_ids["librarian"]

    borrow_ids = {}
    for idx, (username, book_idx, barcode, borrow_days, due_days, return_days,
              renew, status, notes) in enumerate(BORROWS, start=1):
        rec = BorrowRecord(
            user_id=user_ids[username], book_id=book_idx, copy_id=copy_ids[barcode],
            borrow_date=day(borrow_days), due_date=day(due_days),
            return_date=day(return_days) if return_days is not None else None,
            renew_count=renew, status=status, librarian_id=librarian_id, notes=notes
        )
        db.add(rec)
        borrow_ids[idx] = rec

    db.flush()

    db.add(FineRecord(
        user_id=user_ids["zhangsan"], borrow_id=borrow_ids[4].id, amount=Decimal("2.50"),
        reason="overdue", status="unpaid", notes="三体全集逾期 5 天，费率 0.50 元/天"
    ))

    db.add(Reservation(
        user_id=user_ids["student"], book_id=5, reserve_date=day(-1),
        expire_date=day(6), status="waiting"
    ))

    for title, content, priority, username in ANNOUNCEMENTS:
        db.add(Announcement(
            title=title, content=content, priority=priority, is_active=True,
            author_id=user_ids[username]
        ))

    for username, action, target_type, target_id, detail in AUDIT_LOGS:
        db.add(AuditLog(
            user_id=user_ids[username], username=username, action=action,
            target_type=target_type, target_id=target_id, detail=detail, ip_address="127.0.0.1"
        ))

    db.commit()


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print(f"数据库已存在业务数据，跳过种子写入: {DATABASE_URL}")
            return
        seed(db)
        print(f"数据库初始化完成，已写入演示种子数据: {DATABASE_URL}")
        print("默认账号: admin / librarian / student / zhangsan / lisi，初始密码均为 admin123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
