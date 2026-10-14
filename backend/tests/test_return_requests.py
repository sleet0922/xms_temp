from models import BorrowRecord


def test_reader_can_request_early_return_and_librarian_approves(client, db, reader_headers, librarian_headers):
    # Fixture data includes an active record for the student reader.
    reader_record = db.query(BorrowRecord).filter(
        BorrowRecord.return_date.is_(None),
        BorrowRecord.user.has(username="student"),
    ).first()
    assert reader_record is not None

    requested = client.post(f"/api/borrows/{reader_record.id}/return-request", headers=reader_headers)
    assert requested.status_code == 200, requested.text
    assert requested.json()["return_request_status"] == "pending"

    pending = client.get(
        "/api/borrows",
        params={"status_filter": "return_requested"},
        headers=librarian_headers,
    )
    assert pending.status_code == 200
    assert any(item["id"] == reader_record.id for item in pending.json())

    approved = client.post(
        f"/api/circulation/return-requests/{reader_record.id}/approve",
        headers=librarian_headers,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "returned"
    assert approved.json()["return_request_status"] == "approved"
