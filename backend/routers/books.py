"""书目与馆藏实体管理：分类 / 书架 / 图书 CRUD / 单册条码 / CSV 导出"""
import csv
import io
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import desc, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import require_admin, require_librarian
from database import get_db
from models import Book, BookCopy, BorrowRecord, Category, ShelfLocation, User
from schemas import (
    BookCopyCreate, BookCopyResponse, BookCreate, BookResponse, BookUpdate,
    CategoryCreate, CategoryResponse, ShelfLocationCreate, ShelfLocationResponse,
)
from services.audit import record_audit

router = APIRouter(tags=["书目与馆藏"])


# ============ 分类与书架位置 ============

@router.get("/api/categories", response_model=List[CategoryResponse], summary="分类列表（含藏书量）")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(Category).all()
    res = []
    for c in cats:
        cnt = db.query(Book).filter(Book.category_id == c.id).count()
        res.append({
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "description": c.description,
            "icon": c.icon,
            "created_at": c.created_at,
            "book_count": cnt,
        })
    return res


@router.post("/api/categories", response_model=CategoryResponse, summary="新增分类")
def create_category(
    cat: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    if db.query(Category).filter(or_(Category.code == cat.code, Category.name == cat.name)).first():
        raise HTTPException(status_code=400, detail="分类名称或编码已存在")
    new_cat = Category(**cat.model_dump())
    db.add(new_cat)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="分类名称或编码已存在")
    db.refresh(new_cat)
    return new_cat


@router.get("/api/shelf-locations", response_model=List[ShelfLocationResponse], summary="书架位置列表")
def list_shelf_locations(db: Session = Depends(get_db)):
    return db.query(ShelfLocation).all()


@router.post("/api/shelf-locations", response_model=ShelfLocationResponse, summary="新增书架位置")
def create_shelf_location(
    loc: ShelfLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    if db.query(ShelfLocation).filter(ShelfLocation.code == loc.code).first():
        raise HTTPException(status_code=400, detail="书架位置编码已存在")
    new_loc = ShelfLocation(**loc.model_dump())
    db.add(new_loc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="书架位置编码已存在")
    db.refresh(new_loc)
    return new_loc


# ============ 图书检索与聚合筛选 ============

@router.get("/api/books/facets", summary="检索筛选项（语言/格式/分类分布）")
def book_facets(db: Session = Depends(get_db)):
    def _distinct(column):
        rows = db.query(column, func.count(Book.id)).filter(column.isnot(None), column != "").group_by(column).all()
        return [{"value": v, "count": c} for v, c in rows if v]

    cats = db.query(Category).all()
    return {
        "total": db.query(Book).count(),
        "languages": _distinct(Book.language),
        "formats": _distinct(Book.format),
        "categories": [{"value": c.id, "label": c.name, "count": db.query(Book).filter(Book.category_id == c.id).count()} for c in cats],
    }


@router.get("/api/books", response_model=List[BookResponse], summary="图书检索（关键词/分类/语言/格式/在馆/排序）")
def list_books(
    search: Optional[str] = None,
    author: Optional[str] = None,
    category_id: Optional[int] = None,
    location_id: Optional[int] = None,
    language: Optional[str] = None,
    format: Optional[str] = None,
    in_stock_only: bool = False,
    sort_by: str = "created_at",
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Book)
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                Book.title.like(s),
                Book.author.like(s),
                Book.isbn.like(s),
                Book.publisher.like(s),
                Book.tags.like(s),
                Book.description.like(s),
            )
        )
    if author:
        query = query.filter(Book.author.like(f"%{author}%"))
    if category_id:
        query = query.filter(Book.category_id == category_id)
    if location_id:
        query = query.filter(Book.location_id == location_id)
    if language:
        query = query.filter(Book.language == language)
    if format:
        query = query.filter(Book.format == format)
    if in_stock_only:
        query = query.filter(Book.available_copies > 0)

    if sort_by == "borrow_count":
        query = query.order_by(desc(Book.borrow_count))
    elif sort_by == "price":
        query = query.order_by(desc(Book.price))
    elif sort_by == "rating":
        query = query.order_by(desc(Book.rating), desc(Book.rating_count))
    elif sort_by == "title":
        query = query.order_by(Book.title)
    elif sort_by == "views":
        query = query.order_by(desc(Book.source_views))
    else:
        query = query.order_by(desc(Book.created_at))

    return query.offset(skip).limit(limit).all()


@router.get("/api/books-export", summary="导出全部书目 CSV")
def export_books_csv(db: Session = Depends(get_db)):
    books = db.query(Book).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "书名", "作者", "ISBN", "出版社", "出版日期", "定价", "总册数",
        "在馆册数", "借阅次数", "语言", "格式", "页数", "文件大小", "分类",
    ])
    for b in books:
        writer.writerow([
            b.id, b.title, b.author, b.isbn, b.publisher or "", b.publish_date or "",
            f"{(b.price if b.price is not None else Decimal('0.00')):.2f}", b.total_copies, b.available_copies, b.borrow_count,
            b.language or "", b.format or "", b.pages or "", b.file_size or "",
            b.category.name if b.category else "",
        ])
    return Response(
        content=output.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=library_books.csv"},
    )


@router.get("/api/books/{book_id}", response_model=BookResponse, summary="图书详情")
def get_book_detail(book_id: int, db: Session = Depends(get_db)):
    b = db.query(Book).filter(Book.id == book_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="图书不存在")
    return b


@router.post("/api/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED, summary="录入新书（自动生成条码）")
def create_book(
    book_in: BookCreate,
    copies_count: int = Query(1, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    if book_in.isbn and db.query(Book).filter(Book.isbn == book_in.isbn).first():
        raise HTTPException(status_code=400, detail="该 ISBN 书目已在馆内登记，请直接添加单册")
    if book_in.category_id is not None and not db.query(Category).filter(Category.id == book_in.category_id).first():
        raise HTTPException(status_code=404, detail="指定的图书分类不存在")
    if book_in.location_id is not None and not db.query(ShelfLocation).filter(ShelfLocation.id == book_in.location_id).first():
        raise HTTPException(status_code=404, detail="指定的书架位置不存在")

    book_values = book_in.model_dump(exclude={"total_copies"})
    if book_values.get("price") is None:
        book_values["price"] = Decimal("0.00")
    new_book = Book(
        **book_values,
        total_copies=copies_count,
        available_copies=copies_count,
        borrow_count=0,
    )
    db.add(new_book)
    db.flush()

    for i in range(1, copies_count + 1):
        barcode = f"BK-{datetime.now().strftime('%Y%m')}-{new_book.id:04d}-{i:02d}"
        db.add(BookCopy(
            book_id=new_book.id,
            barcode=barcode,
            status="available",
            condition_status="good",
            location_note="新编目入库",
        ))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="图书 ISBN 或其他唯一字段已存在")
    db.refresh(new_book)
    record_audit(db, current_user, "CREATE_BOOK", "BOOK", str(new_book.id),
                 f"录入新书: {new_book.title} (副本数: {copies_count})", request)
    return new_book


@router.put("/api/books/{book_id}", response_model=BookResponse, summary="编辑书目")
def update_book(
    book_id: int,
    book_in: BookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    b = db.query(Book).filter(Book.id == book_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="图书不存在")

    changes = book_in.model_dump(exclude_unset=True)
    if changes.get("isbn"):
        duplicate = db.query(Book).filter(Book.isbn == changes["isbn"], Book.id != book_id).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="该 ISBN 已被其他书目使用")
    if "category_id" in changes and changes["category_id"] is not None:
        if not db.query(Category).filter(Category.id == changes["category_id"]).first():
            raise HTTPException(status_code=404, detail="指定的图书分类不存在")
    if "location_id" in changes and changes["location_id"] is not None:
        if not db.query(ShelfLocation).filter(ShelfLocation.id == changes["location_id"]).first():
            raise HTTPException(status_code=404, detail="指定的书架位置不存在")
    for k, v in changes.items():
        setattr(b, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="图书信息已与现有书目冲突")
    db.refresh(b)
    return b


@router.delete("/api/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="注销下架图书")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    request: Request = None,
):
    b = db.query(Book).filter(Book.id == book_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="图书不存在")

    in_use = db.query(BorrowRecord).filter(
        BorrowRecord.book_id == book_id, BorrowRecord.return_date.is_(None)
    ).first()
    if in_use:
        raise HTTPException(status_code=400, detail="该图书尚有读者借阅未归还，无法注销下架")

    title = b.title
    db.delete(b)
    db.commit()
    record_audit(db, current_user, "DELETE_BOOK", "BOOK", str(book_id), f"注销图书: {title}", request)
    return None


@router.post("/api/books/{book_id}/copies", response_model=BookCopyResponse, summary="新增单册实体")
def add_book_copy(
    book_id: int,
    copy_in: BookCopyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    b = db.query(Book).filter(Book.id == book_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="图书不存在")
    if db.query(BookCopy).filter(BookCopy.barcode == copy_in.barcode).first():
        raise HTTPException(status_code=400, detail="条形码已存在")

    copy = BookCopy(
        book_id=book_id,
        barcode=copy_in.barcode,
        status="available",
        condition_status=copy_in.condition_status or "good",
        location_note=copy_in.location_note,
    )
    db.add(copy)
    db.flush()
    b.total_copies = db.query(BookCopy).filter(BookCopy.book_id == b.id).count()
    b.available_copies = db.query(BookCopy).filter(
        BookCopy.book_id == b.id, BookCopy.status == "available"
    ).count()
    db.commit()
    db.refresh(copy)
    record_audit(db, current_user, "ADD_BOOK_COPY", "BOOK", str(book_id),
                 f"为《{b.title}》补录单册 (条码: {copy.barcode})", request)
    return copy
