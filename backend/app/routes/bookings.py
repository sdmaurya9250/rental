# from fastapi import APIRouter, Request, Depends, HTTPException, status
# from models.user import BookingCreate, BookingReject, VerifyOtpRequest
# from routes.profile import get_current_user
# from pydantic import BaseModel, Field
# from typing import Optional
# import secrets
# import random
#
# router = APIRouter()
#
#
# class VerifyOtpRequest(BaseModel):
#     otp: str = Field(..., min_length=6, max_length=6)
#
#
# def _generate_otp() -> str:
#     return f"{random.randint(100000, 999999)}"
#
#
# def _format_booking(row: dict, current_user_id: str) -> dict:
#     is_incoming = row.get("rent_person_id") == current_user_id
#     direction = "incoming" if is_incoming else "outgoing"
#
#     if is_incoming:
#         person_name = row.get("customer_name") or "Customer"
#         person_image = row.get("customer_image") or ""
#     else:
#         person_name = row.get("rent_person_name") or "RentPeople"
#         person_image = row.get("rent_person_image") or ""
#
#     status_val = row.get("status") or "pending"
#     otp = row.get("otp") or ""
#     otp_verified = bool(row.get("otp_verified", 0)) or status_val == "completed"
#
#     # OTP only while approved and not yet verified/completed
#     show_otp = status_val == "approved" and bool(otp) and not otp_verified
#
#     return {
#         "id": row["id"],
#         "direction": direction,
#         "booking_status": status_val,
#         "booking_date": row.get("booking_date"),
#         "start_time": row.get("start_time"),
#         "end_time": row.get("end_time"),
#         "duration_minutes": row.get("duration_minutes") or 0,
#         "location_type": row.get("location_type"),
#         "location": row.get("location") or "",
#         "timezone": row.get("timezone") or "Asia/Kolkata",
#         "service_id": row.get("service_id"),
#         "service_name": row.get("service_name") or "Service",
#         "total_amount": row.get("total_amount") or 0,
#         "price": row.get("price") or 0,
#         "platform_fee": row.get("platform_fee") or 0,
#         "special_requirements": row.get("special_requirements") or "",
#         "customer_note": row.get("customer_note") or "",
#         "rejection_message": row.get("rejection_message") or "",
#         "cancellation_message": row.get("cancellation_message") or "",
#         "person_name": person_name,
#         "person_image": person_image,
#         "customer_id": row.get("customer_id"),
#         "rent_person_id": row.get("rent_person_id"),
#         "created_at": row.get("created_at"),
#         # OTP
#         "otp": otp if show_otp else None,
#         "otp_verified": otp_verified,
#         "show_otp": (not is_incoming) and show_otp,   # finder displays OTP
#         "needs_otp_entry": is_incoming and show_otp,  # provider enters OTP
#     }
#
#
# @router.post("/bookings", status_code=status.HTTP_201_CREATED)
# async def create_booking(
#     data: BookingCreate,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     customer_id = current_user["id"]
#
#     if data.rent_person_id == customer_id:
#         raise HTTPException(status_code=400, detail="You cannot book yourself")
#
#     person = await db.prepare(
#         "SELECT id, full_name FROM users WHERE id = ?"
#     ).bind(data.rent_person_id).first()
#
#     if not person:
#         raise HTTPException(status_code=404, detail="RentPeople not found")
#
#     if data.duration_minutes <= 0:
#         raise HTTPException(status_code=400, detail="Invalid duration")
#
#     if data.location_type == "in_person" and not (data.location or "").strip():
#         raise HTTPException(
#             status_code=400,
#             detail="Location is required for in-person bookings",
#         )
#
#     booking_id = secrets.token_hex(8)
#
#     await db.prepare(
#         """
#         INSERT INTO bookings (
#             id, customer_id, rent_person_id, service_id, service_name,
#             booking_date, start_time, end_time, timezone, duration_minutes,
#             location_type, location, special_requirements, customer_note,
#             price, platform_fee, total_amount, status
#         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         booking_id,
#         customer_id,
#         data.rent_person_id,
#         data.service_id,
#         data.service_name,
#         data.booking_date,
#         data.start_time,
#         data.end_time,
#         data.timezone or "Asia/Kolkata",
#         data.duration_minutes,
#         data.location_type,
#         data.location,
#         data.special_requirements,
#         data.customer_note,
#         data.price,
#         data.platform_fee,
#         data.total_amount,
#         "pending",
#     ).run()
#
#     return {
#         "id": booking_id,
#         "status": "pending",
#         "booking_status": "pending",
#         "message": "Booking request created successfully",
#         "booking_date": data.booking_date,
#         "start_time": data.start_time,
#         "end_time": data.end_time,
#         "total_amount": data.total_amount,
#         "rent_person_id": data.rent_person_id,
#     }
#
#
# @router.get("/bookings")
# async def my_bookings(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     outgoing = await db.prepare(
#         """
#         SELECT b.*,
#                u.full_name AS rent_person_name,
#                u.image AS rent_person_image
#         FROM bookings b
#         LEFT JOIN users u ON u.id = b.rent_person_id
#         WHERE b.customer_id = ?
#         ORDER BY b.created_at DESC
#         """
#     ).bind(user_id).all()
#
#     incoming = await db.prepare(
#         """
#         SELECT b.*,
#                u.full_name AS customer_name,
#                u.image AS customer_image
#         FROM bookings b
#         LEFT JOIN users u ON u.id = b.customer_id
#         WHERE b.rent_person_id = ?
#         ORDER BY b.created_at DESC
#         """
#     ).bind(user_id).all()
#
#     def to_list(rows):
#         items = rows.results if hasattr(rows, "results") else rows
#         return [dict(r) for r in items]
#
#     bookings = []
#     for row in to_list(outgoing):
#         bookings.append(_format_booking(row, user_id))
#     for row in to_list(incoming):
#         bookings.append(_format_booking(row, user_id))
#
#     bookings.sort(
#         key=lambda b: b.get("created_at") or b.get("booking_date") or "",
#         reverse=True,
#     )
#
#     return {
#         "bookings": bookings,
#         "count": len(bookings),
#     }
#
#
# @router.get("/bookings/{booking_id}")
# async def get_booking(
#     booking_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         """
#         SELECT b.*,
#                c.full_name AS customer_name, c.image AS customer_image,
#                r.full_name AS rent_person_name, r.image AS rent_person_image
#         FROM bookings b
#         LEFT JOIN users c ON c.id = b.customer_id
#         LEFT JOIN users r ON r.id = b.rent_person_id
#         WHERE b.id = ?
#         """
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#     if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
#         raise HTTPException(status_code=403, detail="Not allowed")
#
#     return _format_booking(booking, user_id)
#
#
# @router.post("/bookings/{booking_id}/approve")
# async def approve_booking(
#     booking_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """
#     RentPeople approves → generate 6-digit OTP.
#     Finder sees OTP; provider enters OTP to verify.
#     """
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["rent_person_id"] != user_id:
#         raise HTTPException(
#             status_code=403,
#             detail="Only the RentPeople can approve this booking",
#         )
#
#     if booking.get("status") != "pending":
#         raise HTTPException(
#             status_code=400,
#             detail=f"Cannot approve booking with status: {booking.get('status')}",
#         )
#
#     otp = _generate_otp()
#
#     await db.prepare(
#         """
#         UPDATE bookings
#         SET status = ?, otp = ?, otp_verified = 0
#         WHERE id = ?
#         """
#     ).bind("approved", otp, booking_id).run()
#
#     return {
#         "id": booking_id,
#         "booking_status": "approved",
#         "otp": otp,
#         "otp_verified": False,
#         "message": "Booking approved. OTP generated for meetup verification.",
#     }
#
# @router.post("/bookings/{booking_id}/verify-otp")
# async def verify_booking_otp(
#     booking_id: str,
#     data: VerifyOtpRequest,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """RentPeople enters OTP → mark booking completed."""
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["rent_person_id"] != user_id:
#         raise HTTPException(
#             status_code=403,
#             detail="Only the RentPeople can verify the OTP",
#         )
#
#     if booking.get("status") == "completed":
#         return {
#             "id": booking_id,
#             "booking_status": "completed",
#             "otp_verified": True,
#             "message": "Booking already completed",
#         }
#
#     if booking.get("status") != "approved":
#         raise HTTPException(
#             status_code=400,
#             detail="Booking must be approved before OTP verification",
#         )
#
#     if not booking.get("otp") or str(data.otp).strip() != str(booking["otp"]):
#         raise HTTPException(status_code=400, detail="Invalid OTP")
#
#     await db.prepare(
#         """
#         UPDATE bookings
#         SET otp_verified = 1, status = ?
#         WHERE id = ?
#         """
#     ).bind("completed", booking_id).run()
#
#     return {
#         "id": booking_id,
#         "booking_status": "completed",
#         "otp_verified": True,
#         "message": "OTP verified successfully. Booking completed.",
#     }
#
#
# @router.post("/bookings/{booking_id}/reject")
# async def reject_booking(
#     booking_id: str,
#     data: BookingReject,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["rent_person_id"] != user_id:
#         raise HTTPException(
#             status_code=403,
#             detail="Only the RentPeople can reject this booking",
#         )
#
#     if booking.get("status") != "pending":
#         raise HTTPException(
#             status_code=400,
#             detail=f"Cannot reject booking with status: {booking.get('status')}",
#         )
#
#     msg = (data.rejection_message or "").strip()
#
#     await db.prepare(
#         "UPDATE bookings SET status = ?, rejection_message = ? WHERE id = ?"
#     ).bind("rejected", msg, booking_id).run()
#
#     return {
#         "id": booking_id,
#         "booking_status": "rejected",
#         "rejection_message": msg,
#         "message": "Booking rejected",
#     }
#
#
# @router.post("/bookings/{booking_id}/cancel")
# async def cancel_booking(
#     booking_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
#         raise HTTPException(status_code=403, detail="Not allowed")
#
#     if booking.get("status") in ("completed", "cancelled", "rejected"):
#         raise HTTPException(status_code=400, detail="Cannot cancel this booking")
#
#     await db.prepare(
#         "UPDATE bookings SET status = ?, cancellation_message = ? WHERE id = ?"
#     ).bind("cancelled", "Cancelled by user", booking_id).run()
#
#     return {
#         "id": booking_id,
#         "booking_status": "cancelled",
#         "message": "Booking cancelled",
#     }



# from fastapi import APIRouter, Request, Depends, HTTPException, status
# from models.user import BookingCreate, BookingReject, VerifyOtpRequest
# from routes.profile import get_current_user
# from pydantic import BaseModel, Field
# from routes.notifications import create_notification
# from typing import Optional
# import secrets
# import random
#
# router = APIRouter()
#
#
# class VerifyOtpRequest(BaseModel):
#     otp: str = Field(..., min_length=6, max_length=6)
#
#
# def _generate_otp() -> str:
#     return f"{random.randint(100000, 999999)}"
#
#
# # ─────────────────────────────────────────────
# # Wallet helpers (used on approve + complete)
# # ─────────────────────────────────────────────
# async def debit_wallet_for_booking(
#     db,
#     user_id: str,
#     amount: float,
#     booking_id: str,
#     person_name: str = "",
# ):
#     """Finder pays for booking from wallet."""
#     amount = float(amount or 0)
#     if amount <= 0:
#         return None
#
#     user = await db.prepare(
#         "SELECT wallet_balance FROM users WHERE id = ?"
#     ).bind(user_id).first()
#
#     if not user:
#         raise HTTPException(status_code=404, detail="Customer not found")
#
#     balance = float(dict(user).get("wallet_balance") or 0)
#     if balance < amount:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Insufficient wallet balance. Need ₹{int(amount)}, have ₹{int(balance)}",
#         )
#
#     await db.prepare(
#         """
#         UPDATE users
#         SET wallet_balance = COALESCE(wallet_balance, 0) - ?,
#             total_spent = COALESCE(total_spent, 0) + ?
#         WHERE id = ?
#         """
#     ).bind(amount, amount, user_id).run()
#
#     tx_id = secrets.token_hex(8)
#     await db.prepare(
#         """
#         INSERT INTO wallet_transactions
#             (id, user_id, type, subtitle, amount, category, booking_id)
#         VALUES (?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         tx_id,
#         user_id,
#         "Booking Payment",
#         f"Booking with {person_name}" if person_name else "Booking payment",
#         -abs(amount),
#         "Spent",
#         booking_id,
#     ).run()
#
#     return tx_id
#
#
# async def credit_wallet_earning(
#     db,
#     user_id: str,
#     amount: float,
#     booking_id: str,
# ):
#     """RentPeople earns after booking completed."""
#     amount = float(amount or 0)
#     if amount <= 0:
#         return None
#
#     await db.prepare(
#         """
#         UPDATE users
#         SET wallet_balance = COALESCE(wallet_balance, 0) + ?
#         WHERE id = ?
#         """
#     ).bind(amount, user_id).run()
#
#     tx_id = secrets.token_hex(8)
#     await db.prepare(
#         """
#         INSERT INTO wallet_transactions
#             (id, user_id, type, subtitle, amount, category, booking_id)
#         VALUES (?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         tx_id,
#         user_id,
#         "Booking Earning",
#         "Earning from completed booking",
#         abs(amount),
#         "Added",
#         booking_id,
#     ).run()
#
#     return tx_id
#
#
# async def refund_wallet(
#     db,
#     user_id: str,
#     amount: float,
#     booking_id: str,
#     reason: str = "Booking cancelled/rejected",
# ):
#     """Refund finder if approved booking is cancelled (optional)."""
#     amount = float(amount or 0)
#     if amount <= 0:
#         return None
#
#     await db.prepare(
#         """
#         UPDATE users
#         SET wallet_balance = COALESCE(wallet_balance, 0) + ?,
#             total_spent = MAX(COALESCE(total_spent, 0) - ?, 0)
#         WHERE id = ?
#         """
#     ).bind(amount, amount, user_id).run()
#
#     tx_id = secrets.token_hex(8)
#     await db.prepare(
#         """
#         INSERT INTO wallet_transactions
#             (id, user_id, type, subtitle, amount, category, booking_id)
#         VALUES (?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         tx_id,
#         user_id,
#         "Booking Refund",
#         reason,
#         abs(amount),
#         "Refunded",
#         booking_id,
#     ).run()
#
#     return tx_id
#
#
# def _format_booking(row: dict, current_user_id: str) -> dict:
#     is_incoming = row.get("rent_person_id") == current_user_id
#     direction = "incoming" if is_incoming else "outgoing"
#
#     if is_incoming:
#         person_name = row.get("customer_name") or "Customer"
#         person_image = row.get("customer_image") or ""
#     else:
#         person_name = row.get("rent_person_name") or "RentPeople"
#         person_image = row.get("rent_person_image") or ""
#
#     status_val = row.get("status") or "pending"
#     otp = row.get("otp") or ""
#     otp_verified = bool(row.get("otp_verified", 0)) or status_val == "completed"
#     show_otp = status_val == "approved" and bool(otp) and not otp_verified
#
#     return {
#         "id": row["id"],
#         "direction": direction,
#         "booking_status": status_val,
#         "booking_date": row.get("booking_date"),
#         "start_time": row.get("start_time"),
#         "end_time": row.get("end_time"),
#         "duration_minutes": row.get("duration_minutes") or 0,
#         "location_type": row.get("location_type"),
#         "location": row.get("location") or "",
#         "timezone": row.get("timezone") or "Asia/Kolkata",
#         "service_id": row.get("service_id"),
#         "service_name": row.get("service_name") or "Service",
#         "total_amount": row.get("total_amount") or 0,
#         "price": row.get("price") or 0,
#         "platform_fee": row.get("platform_fee") or 0,
#         "special_requirements": row.get("special_requirements") or "",
#         "customer_note": row.get("customer_note") or "",
#         "rejection_message": row.get("rejection_message") or "",
#         "cancellation_message": row.get("cancellation_message") or "",
#         "person_name": person_name,
#         "person_image": person_image,
#         "customer_id": row.get("customer_id"),
#         "rent_person_id": row.get("rent_person_id"),
#         "created_at": row.get("created_at"),
#         "otp": otp if show_otp else None,
#         "otp_verified": otp_verified,
#         "show_otp": (not is_incoming) and show_otp,
#         "needs_otp_entry": is_incoming and show_otp,
#     }
#
#
# @router.post("/bookings", status_code=status.HTTP_201_CREATED)
# async def create_booking(
#     data: BookingCreate,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     customer_id = current_user["id"]
#
#     if data.rent_person_id == customer_id:
#         raise HTTPException(status_code=400, detail="You cannot book yourself")
#
#     person = await db.prepare(
#         "SELECT id, full_name FROM users WHERE id = ?"
#     ).bind(data.rent_person_id).first()
#
#     if not person:
#         raise HTTPException(status_code=404, detail="RentPeople not found")
#
#     if data.duration_minutes <= 0:
#         raise HTTPException(status_code=400, detail="Invalid duration")
#
#     if data.location_type == "in_person" and not (data.location or "").strip():
#         raise HTTPException(
#             status_code=400,
#             detail="Location is required for in-person bookings",
#         )
#
#     booking_id = secrets.token_hex(8)
#
#     await db.prepare(
#         """
#         INSERT INTO bookings (
#             id, customer_id, rent_person_id, service_id, service_name,
#             booking_date, start_time, end_time, timezone, duration_minutes,
#             location_type, location, special_requirements, customer_note,
#             price, platform_fee, total_amount, status
#         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         booking_id,
#         customer_id,
#         data.rent_person_id,
#         data.service_id,
#         data.service_name,
#         data.booking_date,
#         data.start_time,
#         data.end_time,
#         data.timezone or "Asia/Kolkata",
#         data.duration_minutes,
#         data.location_type,
#         data.location,
#         data.special_requirements,
#         data.customer_note,
#         data.price,
#         data.platform_fee,
#         data.total_amount,
#         "pending",
#     ).run()
#
#     return {
#         "id": booking_id,
#         "status": "pending",
#         "booking_status": "pending",
#         "message": "Booking request created successfully",
#         "booking_date": data.booking_date,
#         "start_time": data.start_time,
#         "end_time": data.end_time,
#         "total_amount": data.total_amount,
#         "rent_person_id": data.rent_person_id,
#     }
#
#
# @router.get("/bookings")
# async def my_bookings(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     outgoing = await db.prepare(
#         """
#         SELECT b.*,
#                u.full_name AS rent_person_name,
#                u.image AS rent_person_image
#         FROM bookings b
#         LEFT JOIN users u ON u.id = b.rent_person_id
#         WHERE b.customer_id = ?
#         ORDER BY b.created_at DESC
#         """
#     ).bind(user_id).all()
#
#     incoming = await db.prepare(
#         """
#         SELECT b.*,
#                u.full_name AS customer_name,
#                u.image AS customer_image
#         FROM bookings b
#         LEFT JOIN users u ON u.id = b.customer_id
#         WHERE b.rent_person_id = ?
#         ORDER BY b.created_at DESC
#         """
#     ).bind(user_id).all()
#
#     def to_list(rows):
#         items = rows.results if hasattr(rows, "results") else rows
#         return [dict(r) for r in items]
#
#     bookings = []
#     for row in to_list(outgoing):
#         bookings.append(_format_booking(row, user_id))
#     for row in to_list(incoming):
#         bookings.append(_format_booking(row, user_id))
#
#     bookings.sort(
#         key=lambda b: b.get("created_at") or b.get("booking_date") or "",
#         reverse=True,
#     )
#
#     return {"bookings": bookings, "count": len(bookings)}
#
#
# @router.get("/bookings/{booking_id}")
# async def get_booking(
#     booking_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         """
#         SELECT b.*,
#                c.full_name AS customer_name, c.image AS customer_image,
#                r.full_name AS rent_person_name, r.image AS rent_person_image
#         FROM bookings b
#         LEFT JOIN users c ON c.id = b.customer_id
#         LEFT JOIN users r ON r.id = b.rent_person_id
#         WHERE b.id = ?
#         """
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#     if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
#         raise HTTPException(status_code=403, detail="Not allowed")
#
#     return _format_booking(booking, user_id)
#
#
# @router.post("/bookings/{booking_id}/approve")
# async def approve_booking(
#     booking_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """
#     RentPeople approves → debit finder wallet → generate OTP.
#     """
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["rent_person_id"] != user_id:
#         raise HTTPException(
#             status_code=403,
#             detail="Only the RentPeople can approve this booking",
#         )
#
#     if booking.get("status") != "pending":
#         raise HTTPException(
#             status_code=400,
#             detail=f"Cannot approve booking with status: {booking.get('status')}",
#         )
#
#     total = float(booking.get("total_amount") or 0)
#     provider_name = current_user.get("full_name") or "RentPeople"
#
#     # 1) Debit FINDER wallet first
#     await debit_wallet_for_booking(
#         db,
#         user_id=booking["customer_id"],
#         amount=total,
#         booking_id=booking_id,
#         person_name=provider_name,
#     )
#
#     # 2) Approve + OTP
#     otp = _generate_otp()
#     await db.prepare(
#         """
#         UPDATE bookings
#         SET status = ?, otp = ?, otp_verified = 0
#         WHERE id = ?
#         """
#     ).bind("approved", otp, booking_id).run()
#
#     return {
#         "id": booking_id,
#         "booking_status": "approved",
#         "otp": otp,
#         "otp_verified": False,
#         "wallet_debited": total,
#         "message": "Booking approved. Finder wallet debited. OTP generated.",
#     }
#
#
# @router.post("/bookings/{booking_id}/verify-otp")
# async def verify_booking_otp(
#     booking_id: str,
#     data: VerifyOtpRequest,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """RentPeople enters OTP → completed → credit provider wallet."""
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["rent_person_id"] != user_id:
#         raise HTTPException(
#             status_code=403,
#             detail="Only the RentPeople can verify the OTP",
#         )
#
#     if booking.get("status") == "completed":
#         return {
#             "id": booking_id,
#             "booking_status": "completed",
#             "otp_verified": True,
#             "message": "Booking already completed",
#         }
#
#     if booking.get("status") != "approved":
#         raise HTTPException(
#             status_code=400,
#             detail="Booking must be approved before OTP verification",
#         )
#
#     if not booking.get("otp") or str(data.otp).strip() != str(booking["otp"]):
#         raise HTTPException(status_code=400, detail="Invalid OTP")
#
#     # Complete booking
#     await db.prepare(
#         """
#         UPDATE bookings
#         SET otp_verified = 1, status = ?
#         WHERE id = ?
#         """
#     ).bind("completed", booking_id).run()
#
#     # Credit PROVIDER (total - platform fee)
#     total = float(booking.get("total_amount") or 0)
#     platform_fee = float(booking.get("platform_fee") or 0)
#     provider_earning = max(total - platform_fee, 0)
#
#     await credit_wallet_earning(
#         db,
#         user_id=booking["rent_person_id"],
#         amount=provider_earning,
#         booking_id=booking_id,
#     )
#
#     return {
#         "id": booking_id,
#         "booking_status": "completed",
#         "otp_verified": True,
#         "provider_earning": provider_earning,
#         "message": "OTP verified successfully. Booking completed. Provider paid.",
#     }
#
#
# @router.post("/bookings/{booking_id}/reject")
# async def reject_booking(
#     booking_id: str,
#     data: BookingReject,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["rent_person_id"] != user_id:
#         raise HTTPException(
#             status_code=403,
#             detail="Only the RentPeople can reject this booking",
#         )
#
#     if booking.get("status") != "pending":
#         raise HTTPException(
#             status_code=400,
#             detail=f"Cannot reject booking with status: {booking.get('status')}",
#         )
#
#     msg = (data.rejection_message or "").strip()
#
#     await db.prepare(
#         "UPDATE bookings SET status = ?, rejection_message = ? WHERE id = ?"
#     ).bind("rejected", msg, booking_id).run()
#
#     # No wallet debit yet (debit only on approve) → no refund needed
#
#     return {
#         "id": booking_id,
#         "booking_status": "rejected",
#         "rejection_message": msg,
#         "message": "Booking rejected",
#     }
#
#
# @router.post("/bookings/{booking_id}/cancel")
# async def cancel_booking(
#     booking_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
#         raise HTTPException(status_code=403, detail="Not allowed")
#
#     if booking.get("status") in ("completed", "cancelled", "rejected"):
#         raise HTTPException(status_code=400, detail="Cannot cancel this booking")
#
#     prev_status = booking.get("status")
#
#     await db.prepare(
#         "UPDATE bookings SET status = ?, cancellation_message = ? WHERE id = ?"
#     ).bind("cancelled", "Cancelled by user", booking_id).run()
#
#     # If already approved (finder was debited) → refund finder
#     if prev_status == "approved":
#         total = float(booking.get("total_amount") or 0)
#         await refund_wallet(
#             db,
#             user_id=booking["customer_id"],
#             amount=total,
#             booking_id=booking_id,
#             reason="Booking cancelled after approval",
#         )
#
#     return {
#         "id": booking_id,
#         "booking_status": "cancelled",
#         "message": "Booking cancelled",
#         "refunded": prev_status == "approved",
#     }


# from fastapi import APIRouter, Request, Depends, HTTPException, status
# from models.user import BookingCreate, BookingReject, VerifyOtpRequest
# from routes.profile import get_current_user
# from routes.notifications import create_notification
# from pydantic import BaseModel, Field
# from typing import Optional
# import secrets
# import random
#
# router = APIRouter()
#
#
# class VerifyOtpRequest(BaseModel):
#     otp: str = Field(..., min_length=6, max_length=6)
#
#
# def _generate_otp() -> str:
#     return f"{random.randint(100000, 999999)}"
#
#
# # ─────────────────────────────────────────────
# # Wallet helpers
# # ─────────────────────────────────────────────
# async def debit_wallet_for_booking(
#     db,
#     user_id: str,
#     amount: float,
#     booking_id: str,
#     person_name: str = "",
# ):
#     amount = float(amount or 0)
#     if amount <= 0:
#         return None
#
#     user = await db.prepare(
#         "SELECT wallet_balance FROM users WHERE id = ?"
#     ).bind(user_id).first()
#
#     if not user:
#         raise HTTPException(status_code=404, detail="Customer not found")
#
#     balance = float(dict(user).get("wallet_balance") or 0)
#     if balance < amount:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Insufficient wallet balance. Need ₹{int(amount)}, have ₹{int(balance)}",
#         )
#
#     await db.prepare(
#         """
#         UPDATE users
#         SET wallet_balance = COALESCE(wallet_balance, 0) - ?,
#             total_spent = COALESCE(total_spent, 0) + ?
#         WHERE id = ?
#         """
#     ).bind(amount, amount, user_id).run()
#
#     tx_id = secrets.token_hex(8)
#     await db.prepare(
#         """
#         INSERT INTO wallet_transactions
#             (id, user_id, type, subtitle, amount, category, booking_id)
#         VALUES (?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         tx_id,
#         user_id,
#         "Booking Payment",
#         f"Booking with {person_name}" if person_name else "Booking payment",
#         -abs(amount),
#         "Spent",
#         booking_id,
#     ).run()
#
#     return tx_id
#
#
# async def credit_wallet_earning(
#     db,
#     user_id: str,
#     amount: float,
#     booking_id: str,
# ):
#     amount = float(amount or 0)
#     if amount <= 0:
#         return None
#
#     await db.prepare(
#         """
#         UPDATE users
#         SET wallet_balance = COALESCE(wallet_balance, 0) + ?
#         WHERE id = ?
#         """
#     ).bind(amount, user_id).run()
#
#     tx_id = secrets.token_hex(8)
#     await db.prepare(
#         """
#         INSERT INTO wallet_transactions
#             (id, user_id, type, subtitle, amount, category, booking_id)
#         VALUES (?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         tx_id,
#         user_id,
#         "Booking Earning",
#         "Earning from completed booking",
#         abs(amount),
#         "Added",
#         booking_id,
#     ).run()
#
#     return tx_id
#
#
# async def refund_wallet(
#     db,
#     user_id: str,
#     amount: float,
#     booking_id: str,
#     reason: str = "Booking cancelled/rejected",
# ):
#     amount = float(amount or 0)
#     if amount <= 0:
#         return None
#
#     await db.prepare(
#         """
#         UPDATE users
#         SET wallet_balance = COALESCE(wallet_balance, 0) + ?,
#             total_spent = MAX(COALESCE(total_spent, 0) - ?, 0)
#         WHERE id = ?
#         """
#     ).bind(amount, amount, user_id).run()
#
#     tx_id = secrets.token_hex(8)
#     await db.prepare(
#         """
#         INSERT INTO wallet_transactions
#             (id, user_id, type, subtitle, amount, category, booking_id)
#         VALUES (?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         tx_id,
#         user_id,
#         "Booking Refund",
#         reason,
#         abs(amount),
#         "Refunded",
#         booking_id,
#     ).run()
#
#     return tx_id
#
#
# def _format_booking(row: dict, current_user_id: str) -> dict:
#     is_incoming = row.get("rent_person_id") == current_user_id
#     direction = "incoming" if is_incoming else "outgoing"
#
#     if is_incoming:
#         person_name = row.get("customer_name") or "Customer"
#         person_image = row.get("customer_image") or ""
#     else:
#         person_name = row.get("rent_person_name") or "RentPeople"
#         person_image = row.get("rent_person_image") or ""
#
#     status_val = row.get("status") or "pending"
#     otp = row.get("otp") or ""
#     otp_verified = bool(row.get("otp_verified", 0)) or status_val == "completed"
#     show_otp = status_val == "approved" and bool(otp) and not otp_verified
#
#     return {
#         "id": row["id"],
#         "direction": direction,
#         "booking_status": status_val,
#         "booking_date": row.get("booking_date"),
#         "start_time": row.get("start_time"),
#         "end_time": row.get("end_time"),
#         "duration_minutes": row.get("duration_minutes") or 0,
#         "location_type": row.get("location_type"),
#         "location": row.get("location") or "",
#         "timezone": row.get("timezone") or "Asia/Kolkata",
#         "service_id": row.get("service_id"),
#         "service_name": row.get("service_name") or "Service",
#         "total_amount": row.get("total_amount") or 0,
#         "price": row.get("price") or 0,
#         "platform_fee": row.get("platform_fee") or 0,
#         "special_requirements": row.get("special_requirements") or "",
#         "customer_note": row.get("customer_note") or "",
#         "rejection_message": row.get("rejection_message") or "",
#         "cancellation_message": row.get("cancellation_message") or "",
#         "person_name": person_name,
#         "person_image": person_image,
#         "customer_id": row.get("customer_id"),
#         "rent_person_id": row.get("rent_person_id"),
#         "created_at": row.get("created_at"),
#         "otp": otp if show_otp else None,
#         "otp_verified": otp_verified,
#         "show_otp": (not is_incoming) and show_otp,
#         "needs_otp_entry": is_incoming and show_otp,
#     }
#
#
# @router.post("/bookings", status_code=status.HTTP_201_CREATED)
# async def create_booking(
#     data: BookingCreate,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     customer_id = current_user["id"]
#
#     if data.rent_person_id == customer_id:
#         raise HTTPException(status_code=400, detail="You cannot book yourself")
#
#     person = await db.prepare(
#         "SELECT id, full_name FROM users WHERE id = ?"
#     ).bind(data.rent_person_id).first()
#
#     if not person:
#         raise HTTPException(status_code=404, detail="RentPeople not found")
#
#     if data.duration_minutes <= 0:
#         raise HTTPException(status_code=400, detail="Invalid duration")
#
#     if data.location_type == "in_person" and not (data.location or "").strip():
#         raise HTTPException(
#             status_code=400,
#             detail="Location is required for in-person bookings",
#         )
#
#     booking_id = secrets.token_hex(8)
#
#     await db.prepare(
#         """
#         INSERT INTO bookings (
#             id, customer_id, rent_person_id, service_id, service_name,
#             booking_date, start_time, end_time, timezone, duration_minutes,
#             location_type, location, special_requirements, customer_note,
#             price, platform_fee, total_amount, status
#         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         booking_id,
#         customer_id,
#         data.rent_person_id,
#         data.service_id,
#         data.service_name,
#         data.booking_date,
#         data.start_time,
#         data.end_time,
#         data.timezone or "Asia/Kolkata",
#         data.duration_minutes,
#         data.location_type,
#         data.location,
#         data.special_requirements,
#         data.customer_note,
#         data.price,
#         data.platform_fee,
#         data.total_amount,
#         "pending",
#     ).run()
#
#     customer_name = current_user.get("full_name") or "Someone"
#     try:
#         await create_notification(
#             db,
#             user_id=data.rent_person_id,
#             title="New booking request",
#             body=f"{customer_name} requested a booking for {data.booking_date}.",
#             type="booking",
#             data={"booking_id": booking_id},
#         )
#     except Exception:
#         pass
#
#     return {
#         "id": booking_id,
#         "status": "pending",
#         "booking_status": "pending",
#         "message": "Booking request created successfully",
#         "booking_date": data.booking_date,
#         "start_time": data.start_time,
#         "end_time": data.end_time,
#         "total_amount": data.total_amount,
#         "rent_person_id": data.rent_person_id,
#     }
#
#
# @router.get("/bookings")
# async def my_bookings(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     outgoing = await db.prepare(
#         """
#         SELECT b.*,
#                u.full_name AS rent_person_name,
#                u.image AS rent_person_image
#         FROM bookings b
#         LEFT JOIN users u ON u.id = b.rent_person_id
#         WHERE b.customer_id = ?
#         ORDER BY b.created_at DESC
#         """
#     ).bind(user_id).all()
#
#     incoming = await db.prepare(
#         """
#         SELECT b.*,
#                u.full_name AS customer_name,
#                u.image AS customer_image
#         FROM bookings b
#         LEFT JOIN users u ON u.id = b.customer_id
#         WHERE b.rent_person_id = ?
#         ORDER BY b.created_at DESC
#         """
#     ).bind(user_id).all()
#
#     def to_list(rows):
#         items = rows.results if hasattr(rows, "results") else rows
#         return [dict(r) for r in items]
#
#     bookings = []
#     for row in to_list(outgoing):
#         bookings.append(_format_booking(row, user_id))
#     for row in to_list(incoming):
#         bookings.append(_format_booking(row, user_id))
#
#     bookings.sort(
#         key=lambda b: b.get("created_at") or b.get("booking_date") or "",
#         reverse=True,
#     )
#
#     return {"bookings": bookings, "count": len(bookings)}
#
#
# @router.get("/bookings/{booking_id}")
# async def get_booking(
#     booking_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         """
#         SELECT b.*,
#                c.full_name AS customer_name, c.image AS customer_image,
#                r.full_name AS rent_person_name, r.image AS rent_person_image
#         FROM bookings b
#         LEFT JOIN users c ON c.id = b.customer_id
#         LEFT JOIN users r ON r.id = b.rent_person_id
#         WHERE b.id = ?
#         """
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#     if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
#         raise HTTPException(status_code=403, detail="Not allowed")
#
#     return _format_booking(booking, user_id)
#
#
# @router.post("/bookings/{booking_id}/approve")
# async def approve_booking(
#     booking_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["rent_person_id"] != user_id:
#         raise HTTPException(
#             status_code=403,
#             detail="Only the RentPeople can approve this booking",
#         )
#
#     if booking.get("status") != "pending":
#         raise HTTPException(
#             status_code=400,
#             detail=f"Cannot approve booking with status: {booking.get('status')}",
#         )
#
#     # total = float(booking.get("total_amount") or 0)
#     # provider_name = current_user.get("full_name") or "RentPeople"
#     #
#     # await debit_wallet_for_booking(
#     #     db,
#     #     user_id=booking["customer_id"],
#     #     amount=total,
#     #     booking_id=booking_id,
#     #     person_name=provider_name,
#     # )
#     #
#     # otp = _generate_otp()
#
#
#     total = float(booking.get("total_amount") or 0)
#     provider_name = current_user.get("full_name") or "RentPeople"
#
#     try:
#         await debit_wallet_for_booking(
#             db,
#             user_id=booking["customer_id"],
#             amount=total,
#             booking_id=booking_id,
#             person_name=provider_name,
#         )
#     except HTTPException as e:
#         if e.status_code == 400 and "Insufficient wallet balance" in str(e.detail):
#             raise HTTPException(
#                 status_code=400,
#                 detail=(
#                     "Customer has insufficient wallet balance. "
#                     f"They need ₹{int(total)} to confirm this booking. "
#                     "Ask them to top up their wallet, then try Approve again."
#                 ),
#             )
#         raise
#
#     otp = _generate_otp()
#
#
#     await db.prepare(
#         """
#         UPDATE bookings
#         SET status = ?, otp = ?, otp_verified = 0
#         WHERE id = ?
#         """
#     ).bind("approved", otp, booking_id).run()
#
#     try:
#         await create_notification(
#             db,
#             user_id=booking["customer_id"],
#             title="Booking approved",
#             body="Your booking was approved. Open My Bookings to see the OTP.",
#             type="booking",
#             data={"booking_id": booking_id},
#         )
#     except Exception:
#         pass
#
#     return {
#         "id": booking_id,
#         "booking_status": "approved",
#         "otp": otp,
#         "otp_verified": False,
#         "wallet_debited": total,
#         "message": "Booking approved. Finder wallet debited. OTP generated.",
#     }
#
#
# @router.post("/bookings/{booking_id}/verify-otp")
# async def verify_booking_otp(
#     booking_id: str,
#     data: VerifyOtpRequest,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["rent_person_id"] != user_id:
#         raise HTTPException(
#             status_code=403,
#             detail="Only the RentPeople can verify the OTP",
#         )
#
#     if booking.get("status") == "completed":
#         return {
#             "id": booking_id,
#             "booking_status": "completed",
#             "otp_verified": True,
#             "message": "Booking already completed",
#         }
#
#     if booking.get("status") != "approved":
#         raise HTTPException(
#             status_code=400,
#             detail="Booking must be approved before OTP verification",
#         )
#
#     if not booking.get("otp") or str(data.otp).strip() != str(booking["otp"]):
#         raise HTTPException(status_code=400, detail="Invalid OTP")
#
#     await db.prepare(
#         """
#         UPDATE bookings
#         SET otp_verified = 1, status = ?
#         WHERE id = ?
#         """
#     ).bind("completed", booking_id).run()
#
#     total = float(booking.get("total_amount") or 0)
#     platform_fee = float(booking.get("platform_fee") or 0)
#     provider_earning = max(total - platform_fee, 0)
#
#     await credit_wallet_earning(
#         db,
#         user_id=booking["rent_person_id"],
#         amount=provider_earning,
#         booking_id=booking_id,
#     )
#
#     try:
#         await create_notification(
#             db,
#             user_id=booking["customer_id"],
#             title="Booking completed",
#             body="Meetup verified. You can rate your experience.",
#             type="booking",
#             data={"booking_id": booking_id},
#         )
#         await create_notification(
#             db,
#             user_id=booking["rent_person_id"],
#             title="Earning received",
#             body=f"₹{int(provider_earning)} credited to your wallet.",
#             type="wallet",
#             data={"booking_id": booking_id},
#         )
#     except Exception:
#         pass
#
#     return {
#         "id": booking_id,
#         "booking_status": "completed",
#         "otp_verified": True,
#         "provider_earning": provider_earning,
#         "message": "OTP verified successfully. Booking completed. Provider paid.",
#     }
#
#
# @router.post("/bookings/{booking_id}/reject")
# async def reject_booking(
#     booking_id: str,
#     data: BookingReject,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["rent_person_id"] != user_id:
#         raise HTTPException(
#             status_code=403,
#             detail="Only the RentPeople can reject this booking",
#         )
#
#     if booking.get("status") != "pending":
#         raise HTTPException(
#             status_code=400,
#             detail=f"Cannot reject booking with status: {booking.get('status')}",
#         )
#
#     msg = (data.rejection_message or "").strip()
#
#     await db.prepare(
#         "UPDATE bookings SET status = ?, rejection_message = ? WHERE id = ?"
#     ).bind("rejected", msg, booking_id).run()
#
#     try:
#         await create_notification(
#             db,
#             user_id=booking["customer_id"],
#             title="Booking rejected",
#             body=msg or "Your booking request was rejected.",
#             type="booking",
#             data={"booking_id": booking_id},
#         )
#     except Exception:
#         pass
#
#     return {
#         "id": booking_id,
#         "booking_status": "rejected",
#         "rejection_message": msg,
#         "message": "Booking rejected",
#     }
#
#
# @router.post("/bookings/{booking_id}/cancel")
# async def cancel_booking(
#     booking_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM bookings WHERE id = ?"
#     ).bind(booking_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Booking not found")
#
#     booking = dict(row)
#
#     if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
#         raise HTTPException(status_code=403, detail="Not allowed")
#
#     if booking.get("status") in ("completed", "cancelled", "rejected"):
#         raise HTTPException(status_code=400, detail="Cannot cancel this booking")
#
#     prev_status = booking.get("status")
#
#     await db.prepare(
#         "UPDATE bookings SET status = ?, cancellation_message = ? WHERE id = ?"
#     ).bind("cancelled", "Cancelled by user", booking_id).run()
#
#     if prev_status == "approved":
#         total = float(booking.get("total_amount") or 0)
#         await refund_wallet(
#             db,
#             user_id=booking["customer_id"],
#             amount=total,
#             booking_id=booking_id,
#             reason="Booking cancelled after approval",
#         )
#
#     other_id = (
#         booking["rent_person_id"]
#         if user_id == booking["customer_id"]
#         else booking["customer_id"]
#     )
#     try:
#         await create_notification(
#             db,
#             user_id=other_id,
#             title="Booking cancelled",
#             body="A booking was cancelled.",
#             type="booking",
#             data={"booking_id": booking_id},
#         )
#     except Exception:
#         pass
#
#     return {
#         "id": booking_id,
#         "booking_status": "cancelled",
#         "message": "Booking cancelled",
#         "refunded": prev_status == "approved",
#     }


from fastapi import APIRouter, Request, Depends, HTTPException, status
from models.user import BookingCreate, BookingReject, VerifyOtpRequest
from routes.profile import get_current_user
from routes.notifications import create_notification
from pydantic import BaseModel, Field
from typing import Optional
import secrets
import random

router = APIRouter()


class VerifyOtpRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6)


def _generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


# ─────────────────────────────────────────────
# Wallet: available vs held
# ─────────────────────────────────────────────
async def _get_balances(db, user_id: str) -> tuple[float, float]:
    row = await db.prepare(
        "SELECT wallet_balance, wallet_held FROM users WHERE id = ?"
    ).bind(user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    u = dict(row)
    return float(u.get("wallet_balance") or 0), float(u.get("wallet_held") or 0)


async def hold_for_booking(
    db,
    user_id: str,
    amount: float,
    booking_id: str,
    person_name: str = "",
):
    """available → held. Fails with structured error if insufficient."""
    amount = float(amount or 0)
    if amount <= 0:
        return None

    existing = await db.prepare(
        """
        SELECT id FROM wallet_transactions
        WHERE booking_id = ? AND user_id = ? AND category = 'Held'
        LIMIT 1
        """
    ).bind(booking_id, user_id).first()
    if existing:
        return dict(existing).get("id")

    available, _held = await _get_balances(db, user_id)
    if available < amount:
        need = round(amount - available, 2)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INSUFFICIENT_BALANCE",
                "message": "Insufficient wallet balance",
                "booking_amount": amount,
                "available_balance": available,
                "amount_needed": need,
            },
        )

    await db.prepare(
        """
        UPDATE users
        SET wallet_balance = COALESCE(wallet_balance, 0) - ?,
            wallet_held = COALESCE(wallet_held, 0) + ?,
            total_spent = COALESCE(total_spent, 0) + ?
        WHERE id = ?
        """
    ).bind(amount, amount, amount, user_id).run()

    tx_id = secrets.token_hex(8)
    await db.prepare(
        """
        INSERT INTO wallet_transactions
            (id, user_id, type, subtitle, amount, category, booking_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        tx_id,
        user_id,
        "Booking Hold",
        f"Held for booking with {person_name}" if person_name else "Booking amount held",
        -abs(amount),
        "Held",
        booking_id,
    ).run()
    return tx_id


async def release_to_companion(
    db,
    finder_id: str,
    companion_id: str,
    amount: float,
    platform_fee: float,
    booking_id: str,
):
    """Release hold: finder held ↓; companion available ↑. Idempotent."""
    amount = float(amount or 0)
    platform_fee = float(platform_fee or 0)
    earning = max(amount - platform_fee, 0)
    if amount <= 0:
        return None

    existing = await db.prepare(
        """
        SELECT id FROM wallet_transactions
        WHERE booking_id = ? AND category = 'Released'
        LIMIT 1
        """
    ).bind(booking_id).first()
    if existing:
        return None

    _, held = await _get_balances(db, finder_id)
    release_amt = min(amount, held)

    await db.prepare(
        """
        UPDATE users
        SET wallet_held = MAX(COALESCE(wallet_held, 0) - ?, 0)
        WHERE id = ?
        """
    ).bind(release_amt, finder_id).run()

    if earning > 0:
        await db.prepare(
            """
            UPDATE users
            SET wallet_balance = COALESCE(wallet_balance, 0) + ?
            WHERE id = ?
            """
        ).bind(earning, companion_id).run()

        tx_id = secrets.token_hex(8)
        await db.prepare(
            """
            INSERT INTO wallet_transactions
                (id, user_id, type, subtitle, amount, category, booking_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        ).bind(
            tx_id,
            companion_id,
            "Booking Earning",
            "Payment released to companion",
            abs(earning),
            "Released",
            booking_id,
        ).run()
    return True


async def refund_hold(
    db,
    user_id: str,
    amount: float,
    booking_id: str,
    reason: str = "Booking rejected — amount refunded",
):
    """held → available. Idempotent."""
    amount = float(amount or 0)
    if amount <= 0:
        return None

    existing = await db.prepare(
        """
        SELECT id FROM wallet_transactions
        WHERE booking_id = ? AND user_id = ? AND category = 'Refunded'
        LIMIT 1
        """
    ).bind(booking_id, user_id).first()
    if existing:
        return None

    _, held = await _get_balances(db, user_id)
    refund_amt = min(amount, held)

    await db.prepare(
        """
        UPDATE users
        SET wallet_held = MAX(COALESCE(wallet_held, 0) - ?, 0),
            wallet_balance = COALESCE(wallet_balance, 0) + ?,
            total_spent = MAX(COALESCE(total_spent, 0) - ?, 0)
        WHERE id = ?
        """
    ).bind(refund_amt, refund_amt, refund_amt, user_id).run()

    tx_id = secrets.token_hex(8)
    await db.prepare(
        """
        INSERT INTO wallet_transactions
            (id, user_id, type, subtitle, amount, category, booking_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        tx_id,
        user_id,
        "Booking Refund",
        reason,
        abs(refund_amt),
        "Refunded",
        booking_id,
    ).run()
    return tx_id


def _format_booking(row: dict, current_user_id: str) -> dict:
    is_incoming = row.get("rent_person_id") == current_user_id
    direction = "incoming" if is_incoming else "outgoing"

    if is_incoming:
        person_name = row.get("customer_name") or "Customer"
        person_image = row.get("customer_image") or ""
    else:
        person_name = row.get("rent_person_name") or "RentPeople"
        person_image = row.get("rent_person_image") or ""

    status_val = row.get("status") or "pending"
    otp = row.get("otp") or ""
    otp_verified = bool(row.get("otp_verified", 0)) or status_val == "completed"
    show_otp = status_val == "approved" and bool(otp) and not otp_verified

    return {
        "id": row["id"],
        "direction": direction,
        "booking_status": status_val,
        "payment_status": row.get("payment_status") or "none",
        "booking_date": row.get("booking_date"),
        "start_time": row.get("start_time"),
        "end_time": row.get("end_time"),
        "duration_minutes": row.get("duration_minutes") or 0,
        "location_type": row.get("location_type"),
        "location": row.get("location") or "",
        "timezone": row.get("timezone") or "Asia/Kolkata",
        "service_id": row.get("service_id"),
        "service_name": row.get("service_name") or "Service",
        "total_amount": row.get("total_amount") or 0,
        "price": row.get("price") or 0,
        "platform_fee": row.get("platform_fee") or 0,
        "special_requirements": row.get("special_requirements") or "",
        "customer_note": row.get("customer_note") or "",
        "rejection_message": row.get("rejection_message") or "",
        "cancellation_message": row.get("cancellation_message") or "",
        "person_name": person_name,
        "person_image": person_image,
        "customer_id": row.get("customer_id"),
        "rent_person_id": row.get("rent_person_id"),
        "created_at": row.get("created_at"),
        "otp": otp if show_otp else None,
        "otp_verified": otp_verified,
        "show_otp": (not is_incoming) and show_otp,
        "needs_otp_entry": is_incoming and show_otp,
    }


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    customer_id = current_user["id"]

    if data.rent_person_id == customer_id:
        raise HTTPException(status_code=400, detail="You cannot book yourself")

    person = await db.prepare(
        "SELECT id, full_name FROM users WHERE id = ?"
    ).bind(data.rent_person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="RentPeople not found")

    if data.duration_minutes <= 0:
        raise HTTPException(status_code=400, detail="Invalid duration")

    if data.location_type == "in_person" and not (data.location or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Location is required for in-person bookings",
        )

    booking_id = secrets.token_hex(8)
    total = float(data.total_amount or 0)
    person_name = dict(person).get("full_name") or "Companion"

    # Hold first — if insufficient, no booking is created
    await hold_for_booking(
        db,
        user_id=customer_id,
        amount=total,
        booking_id=booking_id,
        person_name=person_name,
    )

    await db.prepare(
        """
        INSERT INTO bookings (
            id, customer_id, rent_person_id, service_id, service_name,
            booking_date, start_time, end_time, timezone, duration_minutes,
            location_type, location, special_requirements, customer_note,
            price, platform_fee, total_amount, status, payment_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        booking_id,
        customer_id,
        data.rent_person_id,
        data.service_id,
        data.service_name,
        data.booking_date,
        data.start_time,
        data.end_time,
        data.timezone or "Asia/Kolkata",
        data.duration_minutes,
        data.location_type,
        data.location,
        data.special_requirements,
        data.customer_note,
        data.price,
        data.platform_fee,
        data.total_amount,
        "pending",
        "held",
    ).run()

    customer_name = current_user.get("full_name") or "Someone"
    try:
        await create_notification(
            db,
            user_id=data.rent_person_id,
            title="New booking request",
            body=f"{customer_name} requested a booking for {data.booking_date}.",
            type="booking",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    return {
        "id": booking_id,
        "status": "pending",
        "booking_status": "pending",
        "payment_status": "held",
        "message": "Booking created. Amount held from wallet.",
        "booking_date": data.booking_date,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "total_amount": data.total_amount,
        "rent_person_id": data.rent_person_id,
    }


@router.get("/bookings")
async def my_bookings(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    outgoing = await db.prepare(
        """
        SELECT b.*,
               u.full_name AS rent_person_name,
               u.image AS rent_person_image
        FROM bookings b
        LEFT JOIN users u ON u.id = b.rent_person_id
        WHERE b.customer_id = ?
        ORDER BY b.created_at DESC
        """
    ).bind(user_id).all()

    incoming = await db.prepare(
        """
        SELECT b.*,
               u.full_name AS customer_name,
               u.image AS customer_image
        FROM bookings b
        LEFT JOIN users u ON u.id = b.customer_id
        WHERE b.rent_person_id = ?
        ORDER BY b.created_at DESC
        """
    ).bind(user_id).all()

    def to_list(rows):
        items = rows.results if hasattr(rows, "results") else rows
        return [dict(r) for r in items]

    bookings = []
    for row in to_list(outgoing):
        bookings.append(_format_booking(row, user_id))
    for row in to_list(incoming):
        bookings.append(_format_booking(row, user_id))

    bookings.sort(
        key=lambda b: b.get("created_at") or b.get("booking_date") or "",
        reverse=True,
    )

    return {"bookings": bookings, "count": len(bookings)}


@router.get("/bookings/{booking_id}")
async def get_booking(
    booking_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        """
        SELECT b.*,
               c.full_name AS customer_name, c.image AS customer_image,
               r.full_name AS rent_person_name, r.image AS rent_person_image
        FROM bookings b
        LEFT JOIN users c ON c.id = b.customer_id
        LEFT JOIN users r ON r.id = b.rent_person_id
        WHERE b.id = ?
        """
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)
    if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    return _format_booking(booking, user_id)


@router.post("/bookings/{booking_id}/approve")
async def approve_booking(
    booking_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Approve only — amount already held at create. No debit."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT * FROM bookings WHERE id = ?"
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)

    if booking["rent_person_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the companion can approve this booking",
        )

    if booking.get("status") != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve booking with status: {booking.get('status')}",
        )

    otp = _generate_otp()
    await db.prepare(
        """
        UPDATE bookings
        SET status = ?, otp = ?, otp_verified = 0
        WHERE id = ?
        """
    ).bind("approved", otp, booking_id).run()

    try:
        await create_notification(
            db,
            user_id=booking["customer_id"],
            title="Booking approved",
            body="Your booking was approved. Open My Bookings to see the OTP.",
            type="booking",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    return {
        "id": booking_id,
        "booking_status": "approved",
        "payment_status": booking.get("payment_status") or "held",
        "otp": otp,
        "otp_verified": False,
        "message": "Booking approved. Payment remains held. OTP generated.",
    }


@router.post("/bookings/{booking_id}/verify-otp")
async def verify_booking_otp(
    booking_id: str,
    data: VerifyOtpRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Complete → release held amount to companion (once)."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT * FROM bookings WHERE id = ?"
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)

    if booking["rent_person_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the companion can verify the OTP",
        )

    if booking.get("status") == "completed":
        return {
            "id": booking_id,
            "booking_status": "completed",
            "payment_status": booking.get("payment_status") or "released",
            "otp_verified": True,
            "message": "Booking already completed",
        }

    if booking.get("status") != "approved":
        raise HTTPException(
            status_code=400,
            detail="Booking must be approved before OTP verification",
        )

    if not booking.get("otp") or str(data.otp).strip() != str(booking["otp"]):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    total = float(booking.get("total_amount") or 0)
    platform_fee = float(booking.get("platform_fee") or 0)
    provider_earning = max(total - platform_fee, 0)

    await db.prepare(
        """
        UPDATE bookings
        SET otp_verified = 1, status = ?, payment_status = ?
        WHERE id = ?
        """
    ).bind("completed", "released", booking_id).run()

    await release_to_companion(
        db,
        finder_id=booking["customer_id"],
        companion_id=booking["rent_person_id"],
        amount=total,
        platform_fee=platform_fee,
        booking_id=booking_id,
    )

    try:
        await create_notification(
            db,
            user_id=booking["customer_id"],
            title="Booking completed",
            body="Meetup verified. You can rate your experience.",
            type="booking",
            data={"booking_id": booking_id},
        )
        await create_notification(
            db,
            user_id=booking["rent_person_id"],
            title="Earning received",
            body=f"₹{int(provider_earning)} credited to your wallet.",
            type="wallet",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    return {
        "id": booking_id,
        "booking_status": "completed",
        "payment_status": "released",
        "otp_verified": True,
        "provider_earning": provider_earning,
        "message": "OTP verified. Booking completed. Payment released to companion.",
    }


@router.post("/bookings/{booking_id}/reject")
async def reject_booking(
    booking_id: str,
    data: BookingReject,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT * FROM bookings WHERE id = ?"
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)

    if booking["rent_person_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the companion can reject this booking",
        )

    if booking.get("status") != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject booking with status: {booking.get('status')}",
        )

    msg = (data.rejection_message or "").strip()

    await db.prepare(
        """
        UPDATE bookings
        SET status = ?, rejection_message = ?, payment_status = ?
        WHERE id = ?
        """
    ).bind("rejected", msg, "refunded", booking_id).run()

    if (booking.get("payment_status") or "") == "held":
        await refund_hold(
            db,
            user_id=booking["customer_id"],
            amount=float(booking.get("total_amount") or 0),
            booking_id=booking_id,
            reason="Booking rejected — amount refunded",
        )

    try:
        await create_notification(
            db,
            user_id=booking["customer_id"],
            title="Booking rejected",
            body=msg or "Your booking was rejected. Amount refunded to wallet.",
            type="booking",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    return {
        "id": booking_id,
        "booking_status": "rejected",
        "payment_status": "refunded",
        "rejection_message": msg,
        "message": "Booking rejected. Held amount refunded to customer.",
    }


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT * FROM bookings WHERE id = ?"
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)

    if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if booking.get("status") in ("completed", "cancelled", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot cancel this booking")

    prev_status = booking.get("status")
    pay = booking.get("payment_status") or ""

    await db.prepare(
        """
        UPDATE bookings
        SET status = ?, cancellation_message = ?, payment_status = ?
        WHERE id = ?
        """
    ).bind(
        "cancelled",
        "Cancelled by user",
        "refunded" if pay == "held" else pay,
        booking_id,
    ).run()

    refunded = False
    if prev_status in ("pending", "approved") and pay == "held":
        await refund_hold(
            db,
            user_id=booking["customer_id"],
            amount=float(booking.get("total_amount") or 0),
            booking_id=booking_id,
            reason="Booking cancelled — amount refunded",
        )
        refunded = True

    other_id = (
        booking["rent_person_id"]
        if user_id == booking["customer_id"]
        else booking["customer_id"]
    )
    try:
        await create_notification(
            db,
            user_id=other_id,
            title="Booking cancelled",
            body="A booking was cancelled.",
            type="booking",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    return {
        "id": booking_id,
        "booking_status": "cancelled",
        "payment_status": "refunded" if refunded else pay,
        "message": "Booking cancelled",
        "refunded": refunded,
    }