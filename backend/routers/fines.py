"""罚金与费用结算管理"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from auth import get_current_user, require_librarian
from database import get_db
from models import FineRecord, User
from schemas import FinePayRequest, FineRecordResponse
from services import notify
from services.audit import record_audit

router = APIRouter(prefix="/api/fines", tags=["罚金管理"])


@router.get("", response_model=List[FineRecordResponse], summary="罚金账单列表（读者仅见本人）")
def list_fines(
    status_filter: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(FineRecord)
    if current_user.role == "reader":
        query = query.filter(FineRecord.user_id == current_user.id)
    elif user_id:
        query = query.filter(FineRecord.user_id == user_id)
    if status_filter:
        query = query.filter(FineRecord.status == status_filter)
    return query.order_by(desc(FineRecord.created_at)).all()


@router.get("/summary", summary="罚金汇总（未缴/已缴/减免）")
def fines_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(FineRecord.status, func.sum(FineRecord.amount), func.count(FineRecord.id))
    if current_user.role == "reader":
        query = query.filter(FineRecord.user_id == current_user.id)
    rows = query.group_by(FineRecord.status).all()

    summary = {"unpaid": Decimal("0.00"), "paid": Decimal("0.00"), "waived": Decimal("0.00")}
    counts = {"unpaid": 0, "paid": 0, "waived": 0}
    for status_name, amount, cnt in rows:
        summary[status_name] = amount or Decimal("0.00")
        counts[status_name] = cnt
    return {"amount": summary, "count": counts, "total": sum(summary.values())}


@router.post("/{fine_id}/pay", response_model=FineRecordResponse, summary="结清 / 减免罚金")
def settle_fine(
    fine_id: int,
    pay_req: FinePayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    fine = db.query(FineRecord).filter(FineRecord.id == fine_id).first()
    if not fine:
        raise HTTPException(status_code=404, detail="未找到该罚金账单")
    if fine.status != "unpaid":
        raise HTTPException(status_code=400, detail="该账单已结清或已减免")

    if pay_req.waive:
        fine.status = "waived"
        fine.notes = f"管理员 {current_user.username} 予以特批减免: {pay_req.notes or '关怀政策'}"
    else:
        fine.status = "paid"
        fine.paid_at = datetime.now()
        fine.notes = f"服务台前台实收结算: {pay_req.notes or '现金/移动支付扫码'}"

    db.commit()
    db.refresh(fine)
    record_audit(db, current_user, "FINE_SETTLE", "FINE", str(fine.id),
                 f"处理罚金账单: {fine.status} ({fine.amount:.2f}元)", request)
    return fine


@router.post("/remind/{reader_id}", summary="催缴通知（馆员一键提醒未缴读者）")
def remind_reader(
    reader_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    reader = db.query(User).filter(User.id == reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="读者不存在")

    unpaid = db.query(FineRecord).filter(
        FineRecord.user_id == reader_id, FineRecord.status == "unpaid"
    ).all()
    if not unpaid:
        raise HTTPException(status_code=400, detail="该读者没有未缴纳的罚金账单")

    total = sum((f.amount for f in unpaid), Decimal("0.00"))
    note = notify.create_notification(
        db,
        reader_id,
        "fine",
        f"罚金催缴提醒：待缴 {total:.2f} 元",
        f"您当前有 {len(unpaid)} 笔逾期罚金未结清（合计 {total:.2f} 元），请前往 1 楼服务台办理结清，以免影响后续借阅。",
        "/fines",
    )
    return {"message": f"已向 {reader.full_name} 发送催缴通知", "notification_id": note.id, "amount": total}


@router.get("/amount-total", summary="全馆未缴罚金总额")
def unpaid_total(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(func.sum(FineRecord.amount)).filter(FineRecord.status == "unpaid")
    if current_user.role == "reader":
        query = query.filter(FineRecord.user_id == current_user.id)
    return {"unpaid_total": query.scalar() or Decimal("0.00")}