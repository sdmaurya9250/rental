# # from fastapi import APIRouter, Request, Depends, HTTPException, status
# # from routes.profile import get_current_user
# # from pydantic import BaseModel, Field
# # from typing import Optional
# # import secrets
# # import json
# # import hmac
# # import hashlib
# # import base64
# #
# # router = APIRouter()
# #
# #
# # class CreatePaymentOrderRequest(BaseModel):
# #     amount: float = Field(..., ge=100)
# #     purpose: Optional[str] = "wallet_topup"
# #     return_url: Optional[str] = None
# #
# #
# # def _cf_config(request: Request) -> dict:
# #     env = request.scope.get("env")
# #     app_id = (getattr(env, "CASHFREE_APP_ID", None) or "").strip()
# #     secret = (getattr(env, "CASHFREE_SECRET_KEY", None) or "").strip()
# #     mode = (getattr(env, "CASHFREE_ENV", None) or "sandbox").lower().strip()
# #     api_version = (getattr(env, "CASHFREE_API_VERSION", None) or "2025-01-01").strip()
# #
# #     if not app_id or not secret:
# #         raise HTTPException(
# #             status_code=500,
# #             detail="Cashfree not configured. Set CASHFREE_APP_ID and CASHFREE_SECRET_KEY",
# #         )
# #
# #     base = (
# #         "https://api.cashfree.com/pg"
# #         if mode in ("production", "prod", "live")
# #         else "https://sandbox.cashfree.com/pg"
# #     )
# #     return {
# #         "app_id": app_id,
# #         "secret": secret,
# #         "base": base,
# #         "api_version": api_version,
# #         "mode": mode,
# #     }
# #
# # async def _http_json(
# #     method: str,
# #     url: str,
# #     headers: dict,
# #     body: dict | None = None,
# # ) -> tuple[int, dict]:
# #     """
# #     Cloudflare Workers: use js.fetch (urllib often fails with
# #     'Remote end closed connection without response').
# #     """
# #     payload = json.dumps(body) if body is not None else None
# #
# #     # --- Workers native fetch ---
# #     try:
# #         from js import fetch, Object
# #         from pyodide.ffi import to_js
# #
# #         opts = {
# #             "method": method,
# #             "headers": headers,
# #         }
# #         if payload is not None:
# #             opts["body"] = payload
# #
# #         resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
# #         text = await resp.text()
# #         code = int(resp.status)
# #         try:
# #             data = json.loads(text) if text else {}
# #         except Exception:
# #             data = {"message": text}
# #         return code, data
# #     except ImportError:
# #         pass
# #     except Exception as e:
# #         # fall through to urllib for local debug
# #         last_err = e
# #     else:
# #         last_err = None
# #
# #     # --- Local / non-Workers fallback ---
# #     import urllib.request
# #     import urllib.error
# #
# #     data_bytes = payload.encode("utf-8") if payload is not None else None
# #     req = urllib.request.Request(
# #         url,
# #         data=data_bytes,
# #         headers=headers,
# #         method=method,
# #     )
# #     try:
# #         with urllib.request.urlopen(req, timeout=30) as resp:
# #             text = resp.read().decode("utf-8")
# #             return resp.status, (json.loads(text) if text else {})
# #     except urllib.error.HTTPError as e:
# #         text = e.read().decode("utf-8")
# #         try:
# #             data = json.loads(text) if text else {}
# #         except Exception:
# #             data = {"message": text}
# #         return int(e.code), data
# #     except Exception as e:
# #         msg = str(last_err or e)
# #         raise HTTPException(
# #             status_code=502,
# #             detail=f"Cashfree request failed: {msg}",
# #         )
# #
# # async def _cf_request(
# #     request: Request,
# #     method: str,
# #     path: str,
# #     body: dict | None = None,
# # ) -> dict:
# #     cfg = _cf_config(request)
# #     url = f"{cfg['base']}{path}"
# #     # headers = {
# #     #     "Content-Type": "application/json",
# #     #     "Accept": "application/json",
# #     #     "x-client-id": cfg["app_id"],
# #     #     "x-client-secret": cfg["secret"],
# #     #     "x-api-version": cfg["api_version"],
# #     # }
# #
# #     headers = {
# #         "Content-Type": "application/json",
# #         "Accept": "application/json",
# #         "x-client-id": cfg["app_id"],
# #         "x-client-secret": cfg["secret"],
# #         "x-api-version": cfg["api_version"],  # e.g. "2023-08-01" or "2025-01-01"
# #     }
# #
# #     code, data = await _http_json(method, url, headers, body)
# #     if code >= 400:
# #         msg = data.get("message") if isinstance(data, dict) else str(data)
# #         raise HTTPException(status_code=502, detail=msg or f"Cashfree error {code}")
# #     return data if isinstance(data, dict) else {}
# #
# #
# # async def _credit_wallet_once(db, user_id: str, amount: float, order_id: str) -> bool:
# #     """Credit available balance once per order_id (idempotent)."""
# #     amount = float(amount or 0)
# #     if amount <= 0:
# #         return False
# #
# #     existing = await db.prepare(
# #         """
# #         SELECT id FROM wallet_transactions
# #         WHERE booking_id = ? AND user_id = ? AND category = 'Added'
# #           AND type = 'Wallet Top Up'
# #         LIMIT 1
# #         """
# #     ).bind(order_id, user_id).first()
# #     if existing:
# #         return False
# #
# #     await db.prepare(
# #         """
# #         UPDATE users
# #         SET wallet_balance = COALESCE(wallet_balance, 0) + ?,
# #             total_added = COALESCE(total_added, 0) + ?
# #         WHERE id = ?
# #         """
# #     ).bind(amount, amount, user_id).run()
# #
# #     tx_id = secrets.token_hex(8)
# #     await db.prepare(
# #         """
# #         INSERT INTO wallet_transactions
# #             (id, user_id, type, subtitle, amount, category, booking_id)
# #         VALUES (?, ?, ?, ?, ?, ?, ?)
# #         """
# #     ).bind(
# #         tx_id,
# #         user_id,
# #         "Wallet Top Up",
# #         f"Cashfree {order_id}",
# #         abs(amount),
# #         "Added",
# #         order_id,
# #     ).run()
# #     return True
# #
# #
# # @router.post("/payments/create-order", status_code=status.HTTP_201_CREATED)
# # async def create_payment_order(
# #     data: CreatePaymentOrderRequest,
# #     request: Request,
# #     current_user: dict = Depends(get_current_user),
# # ):
# #     """
# #     Create Cashfree order for WALLET TOP-UP only.
# #     Booking still uses wallet hold — never charge at book time.
# #     """
# #     db = request.scope["env"].DB
# #     user_id = current_user["id"]
# #     amount = round(float(data.amount), 2)
# #
# #     if amount < 100:
# #         raise HTTPException(status_code=400, detail="Minimum top-up is ₹100")
# #
# #     order_id = f"wt_{secrets.token_hex(8)}"
# #     phone = str(current_user.get("mobile") or "9999999999").strip()
# #     digits = "".join(c for c in phone if c.isdigit())
# #     phone = digits[-10:] if len(digits) >= 10 else "9999999999"
# #     email = (current_user.get("email") or "user@example.com").strip()
# #     name = (current_user.get("full_name") or "User").strip()[:100]
# #
# #     return_url = (data.return_url or "").strip()
# #     if not return_url:
# #         return_url = (
# #             "https://rental-backend.kudoo-live.workers.dev/api/payments/return"
# #             "?order_id={order_id}"
# #         )
# #     elif "{order_id}" not in return_url:
# #         sep = "&" if "?" in return_url else "?"
# #         return_url = f"{return_url}{sep}order_id={{order_id}}"
# #
# #     notify_url = "https://rental-backend.kudoo-live.workers.dev/api/payments/webhook"
# #
# #     payload = {
# #         "order_id": order_id,
# #         "order_amount": amount,
# #         "order_currency": "INR",
# #         "customer_details": {
# #             "customer_id": str(user_id)[:50],
# #             "customer_phone": phone,
# #             "customer_email": email,
# #             "customer_name": name,
# #         },
# #         "order_meta": {
# #             "return_url": return_url,
# #             "notify_url": notify_url,
# #         },
# #         "order_note": data.purpose or "wallet_topup",
# #         "order_tags": {
# #             "user_id": user_id,
# #             "purpose": data.purpose or "wallet_topup",
# #         },
# #     }
# #
# #     cf = await _cf_request(request, "POST", "/orders", payload)
# #     payment_session_id = cf.get("payment_session_id")
# #     cf_order_id = str(cf.get("cf_order_id") or "")
# #
# #     if not payment_session_id:
# #         raise HTTPException(
# #             status_code=502,
# #             detail=cf.get("message") or "Failed to create Cashfree order",
# #         )
# #
# #     row_id = secrets.token_hex(8)
# #     await db.prepare(
# #         """
# #         INSERT INTO payment_orders (
# #             id, user_id, order_id, cf_order_id, amount, currency,
# #             purpose, status, payment_session_id, raw_response
# #         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# #         """
# #     ).bind(
# #         row_id,
# #         user_id,
# #         order_id,
# #         cf_order_id,
# #         amount,
# #         "INR",
# #         data.purpose or "wallet_topup",
# #         "CREATED",
# #         payment_session_id,
# #         json.dumps(cf),
# #     ).run()
# #
# #     cfg = _cf_config(request)
# #     return {
# #         "order_id": order_id,
# #         "cf_order_id": cf_order_id,
# #         "payment_session_id": payment_session_id,
# #         "amount": amount,
# #         "currency": "INR",
# #         "environment": cfg["mode"],
# #         "purpose": data.purpose or "wallet_topup",
# #         "message": "Order created. Open Cashfree checkout with payment_session_id.",
# #     }
# #
# #
# # @router.get("/payments/verify/{order_id}")
# # async def verify_payment(
# #     order_id: str,
# #     request: Request,
# #     current_user: dict = Depends(get_current_user),
# # ):
# #     """After checkout: confirm PAID and credit available wallet balance."""
# #     db = request.scope["env"].DB
# #     user_id = current_user["id"]
# #
# #     row = await db.prepare(
# #         "SELECT * FROM payment_orders WHERE order_id = ?"
# #     ).bind(order_id).first()
# #     if not row:
# #         raise HTTPException(status_code=404, detail="Order not found")
# #
# #     order = dict(row)
# #     if order["user_id"] != user_id:
# #         raise HTTPException(status_code=403, detail="Not allowed")
# #
# #     async def _balance():
# #         bal = await db.prepare(
# #             "SELECT wallet_balance, wallet_held FROM users WHERE id = ?"
# #         ).bind(user_id).first()
# #         b = dict(bal) if bal else {}
# #         return float(b.get("wallet_balance") or 0), float(b.get("wallet_held") or 0)
# #
# #     if (order.get("status") or "").upper() == "PAID":
# #         available, held = await _balance()
# #         return {
# #             "order_id": order_id,
# #             "status": "PAID",
# #             "credited": True,
# #             "amount": float(order.get("amount") or 0),
# #             "wallet_balance": available,
# #             "available_balance": available,
# #             "wallet_held": held,
# #             "message": "Payment already processed",
# #         }
# #
# #     cf = await _cf_request(request, "GET", f"/orders/{order_id}")
# #     order_status = (cf.get("order_status") or "").upper()
# #
# #     if order_status == "PAID":
# #         amount = float(order.get("amount") or cf.get("order_amount") or 0)
# #         await db.prepare(
# #             """
# #             UPDATE payment_orders
# #             SET status = 'PAID', updated_at = CURRENT_TIMESTAMP, raw_response = ?
# #             WHERE order_id = ?
# #             """
# #         ).bind(json.dumps(cf), order_id).run()
# #
# #         credited = await _credit_wallet_once(db, user_id, amount, order_id)
# #         available, held = await _balance()
# #
# #         return {
# #             "order_id": order_id,
# #             "status": "PAID",
# #             "credited": credited,
# #             "amount": amount,
# #             "wallet_balance": available,
# #             "available_balance": available,
# #             "wallet_held": held,
# #             "message": (
# #                 "Payment successful. Wallet credited."
# #                 if credited
# #                 else "Already credited"
# #             ),
# #         }
# #
# #     local = (
# #         "FAILED"
# #         if order_status in ("EXPIRED", "TERMINATED")
# #         else (order_status or "CREATED")
# #     )
# #     await db.prepare(
# #         """
# #         UPDATE payment_orders
# #         SET status = ?, updated_at = CURRENT_TIMESTAMP, raw_response = ?
# #         WHERE order_id = ?
# #         """
# #     ).bind(local, json.dumps(cf), order_id).run()
# #
# #     available, held = await _balance()
# #     return {
# #         "order_id": order_id,
# #         "status": local,
# #         "credited": False,
# #         "cf_order_status": order_status,
# #         "wallet_balance": available,
# #         "available_balance": available,
# #         "wallet_held": held,
# #         "message": "Payment not completed yet",
# #     }
# #
# #
# # @router.post("/payments/webhook")
# # async def cashfree_webhook(request: Request):
# #     """Cashfree notify_url — credit wallet on success (idempotent)."""
# #     db = request.scope["env"].DB
# #     raw_body = await request.body()
# #     raw_text = (
# #         raw_body.decode("utf-8")
# #         if isinstance(raw_body, (bytes, bytearray))
# #         else str(raw_body)
# #     )
# #
# #     cfg = _cf_config(request)
# #     ts = request.headers.get("x-webhook-timestamp") or ""
# #     sig = request.headers.get("x-webhook-signature") or ""
# #
# #     if ts and sig:
# #         signed = f"{ts}{raw_text}".encode("utf-8")
# #         expected = base64.b64encode(
# #             hmac.new(cfg["secret"].encode("utf-8"), signed, hashlib.sha256).digest()
# #         ).decode("utf-8")
# #         if not hmac.compare_digest(expected, sig):
# #             raise HTTPException(status_code=401, detail="Invalid webhook signature")
# #
# #     try:
# #         payload = json.loads(raw_text)
# #     except Exception:
# #         raise HTTPException(status_code=400, detail="Invalid JSON")
# #
# #     event_type = (payload.get("type") or "").upper()
# #     data = payload.get("data") or {}
# #     order = data.get("order") or {}
# #     payment = data.get("payment") or {}
# #
# #     order_id = order.get("order_id") or payload.get("order_id")
# #     if not order_id:
# #         return {"ok": True, "message": "ignored"}
# #
# #     row = await db.prepare(
# #         "SELECT * FROM payment_orders WHERE order_id = ?"
# #     ).bind(order_id).first()
# #     if not row:
# #         return {"ok": True, "message": "order not found"}
# #
# #     po = dict(row)
# #     if (po.get("status") or "").upper() == "PAID":
# #         return {"ok": True, "message": "already paid"}
# #
# #     pay_status = (payment.get("payment_status") or order.get("order_status") or "").upper()
# #     is_success = (
# #         "SUCCESS" in event_type
# #         or pay_status in ("SUCCESS", "PAID")
# #         or event_type == "PAYMENT_SUCCESS_WEBHOOK"
# #     )
# #
# #     if is_success:
# #         amount = float(po.get("amount") or 0)
# #         await db.prepare(
# #             """
# #             UPDATE payment_orders
# #             SET status = 'PAID', updated_at = CURRENT_TIMESTAMP, raw_response = ?
# #             WHERE order_id = ?
# #             """
# #         ).bind(raw_text, order_id).run()
# #         await _credit_wallet_once(db, po["user_id"], amount, order_id)
# #
# #     return {"ok": True}
# #
# #
# # @router.get("/payments/return")
# # async def payment_return(order_id: Optional[str] = None):
# #     """Browser return — app should call verify with order_id."""
# #     return {
# #         "order_id": order_id,
# #         "message": "Return to app and call GET /api/payments/verify/{order_id}",
# #     }
# #
# #
# # @router.get("/payments/orders")
# # async def my_payment_orders(
# #     request: Request,
# #     current_user: dict = Depends(get_current_user),
# # ):
# #     """List my top-up orders."""
# #     db = request.scope["env"].DB
# #     user_id = current_user["id"]
# #
# #     rows = await db.prepare(
# #         """
# #         SELECT order_id, amount, status, purpose, created_at, updated_at
# #         FROM payment_orders
# #         WHERE user_id = ?
# #         ORDER BY created_at DESC
# #         LIMIT 50
# #         """
# #     ).bind(user_id).all()
# #
# #     items = rows.results if hasattr(rows, "results") else rows
# #     orders = [dict(r) for r in items]
# #     return {"count": len(orders), "orders": orders}
#
#
# from fastapi import APIRouter, Request, Depends, HTTPException, status
# from routes.profile import get_current_user
# from pydantic import BaseModel, Field
# from typing import Optional
# import secrets
# import json
# import hmac
# import hashlib
# import base64
#
# router = APIRouter()
#
#
# class CreatePaymentOrderRequest(BaseModel):
#     amount: float = Field(..., ge=100)
#     purpose: Optional[str] = "wallet_topup"
#     return_url: Optional[str] = None
#
#
# def _cf_config(request: Request) -> dict:
#     env = request.scope.get("env")
#     app_id = (getattr(env, "CASHFREE_APP_ID", None) or "").strip()
#     secret = (getattr(env, "CASHFREE_SECRET_KEY", None) or "").strip()
#     mode = (getattr(env, "CASHFREE_ENV", None) or "sandbox").lower().strip()
#     api_version = (getattr(env, "CASHFREE_API_VERSION", None) or "2025-01-01").strip()
#
#     if not app_id or not secret:
#         raise HTTPException(
#             status_code=500,
#             detail="Cashfree not configured. Set CASHFREE_APP_ID and CASHFREE_SECRET_KEY",
#         )
#
#     base = (
#         "https://api.cashfree.com/pg"
#         if mode in ("production", "prod", "live")
#         else "https://sandbox.cashfree.com/pg"
#     )
#     return {
#         "app_id": app_id,
#         "secret": secret,
#         "base": base,
#         "api_version": api_version,
#         "mode": mode,
#     }
#
#
# async def _http_json(
#     method: str,
#     url: str,
#     headers: dict,
#     body: dict | None = None,
# ) -> tuple[int, dict]:
#     """Cloudflare Workers: js.fetch first; urllib fallback."""
#     payload = json.dumps(body) if body is not None else None
#     last_err = None
#
#     try:
#         from js import fetch, Object
#         from pyodide.ffi import to_js
#
#         opts = {"method": method, "headers": headers}
#         if payload is not None:
#             opts["body"] = payload
#
#         resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
#         text = await resp.text()
#         code = int(resp.status)
#         try:
#             data = json.loads(text) if text else {}
#         except Exception:
#             data = {"message": text}
#         return code, data
#     except ImportError:
#         pass
#     except Exception as e:
#         last_err = e
#
#     import urllib.request
#     import urllib.error
#
#     data_bytes = payload.encode("utf-8") if payload is not None else None
#     req = urllib.request.Request(
#         url, data=data_bytes, headers=headers, method=method
#     )
#     try:
#         with urllib.request.urlopen(req, timeout=30) as resp:
#             text = resp.read().decode("utf-8")
#             return resp.status, (json.loads(text) if text else {})
#     except urllib.error.HTTPError as e:
#         text = e.read().decode("utf-8")
#         try:
#             data = json.loads(text) if text else {}
#         except Exception:
#             data = {"message": text}
#         return int(e.code), data
#     except Exception as e:
#         raise HTTPException(
#             status_code=502,
#             detail=f"Cashfree request failed: {last_err or e}",
#         )
#
#
# async def _cf_request(
#     request: Request,
#     method: str,
#     path: str,
#     body: dict | None = None,
# ) -> dict:
#     cfg = _cf_config(request)
#     url = f"{cfg['base']}{path}"
#     headers = {
#         "Content-Type": "application/json",
#         "Accept": "application/json",
#         "x-client-id": cfg["app_id"],
#         "x-client-secret": cfg["secret"],
#         "x-api-version": cfg["api_version"],
#     }
#     code, data = await _http_json(method, url, headers, body)
#     if code >= 400:
#         msg = data.get("message") if isinstance(data, dict) else str(data)
#         raise HTTPException(status_code=502, detail=msg or f"Cashfree error {code}")
#     return data if isinstance(data, dict) else {}
#
#
# def _d1_changes(result) -> int:
#     """Rows affected by UPDATE/INSERT (Workers D1)."""
#     if result is None:
#         return 0
#     if hasattr(result, "meta") and result.meta is not None:
#         return int(getattr(result.meta, "changes", 0) or 0)
#     if isinstance(result, dict):
#         meta = result.get("meta") or {}
#         return int(meta.get("changes") or result.get("changes") or 0)
#     return 0
#
#
# async def _credit_wallet_once(db, user_id: str, amount: float, order_id: str) -> bool:
#     """
#     Credit once per order_id.
#     UNIQUE on (booking_id, category, type) → second insert is treated as already done.
#     """
#     amount = float(amount or 0)
#     if amount <= 0:
#         return False
#
#     existing = await db.prepare(
#         """
#         SELECT id FROM wallet_transactions
#         WHERE booking_id = ?
#           AND category = 'Added'
#           AND type = 'Wallet Top Up'
#         LIMIT 1
#         """
#     ).bind(order_id).first()
#     if existing:
#         return False
#
#     tx_id = secrets.token_hex(8)
#     try:
#         await db.prepare(
#             """
#             INSERT INTO wallet_transactions
#                 (id, user_id, type, subtitle, amount, category, booking_id)
#             VALUES (?, ?, ?, ?, ?, ?, ?)
#             """
#         ).bind(
#             tx_id,
#             user_id,
#             "Wallet Top Up",
#             f"Cashfree {order_id}",
#             abs(amount),
#             "Added",
#             order_id,
#         ).run()
#     except Exception as e:
#         msg = str(e).upper()
#         # D1 / SQLite unique race — another request already inserted
#         if "UNIQUE" in msg or "CONSTRAINT" in msg:
#             return False
#         raise
#
#     await db.prepare(
#         """
#         UPDATE users
#         SET wallet_balance = COALESCE(wallet_balance, 0) + ?,
#             total_added = COALESCE(total_added, 0) + ?
#         WHERE id = ?
#         """
#     ).bind(amount, amount, user_id).run()
#     return True
#
#
# async def _mark_paid_and_credit(
#     db,
#     *,
#     order_id: str,
#     user_id: str,
#     amount: float,
#     raw_response: str | None = None,
# ) -> dict:
#     """
#     Idempotent credit for webhook + verify.
#     Only the first caller that flips status → PAID performs the wallet credit.
#     """
#     amount = float(amount or 0)
#
#     row = await db.prepare(
#         "SELECT status, amount, user_id FROM payment_orders WHERE order_id = ?"
#     ).bind(order_id).first()
#     if not row:
#         return {
#             "claimed": False,
#             "credited": False,
#             "already_paid": False,
#             "missing": True,
#         }
#
#     po = dict(row)
#     uid = po.get("user_id") or user_id
#     amt = float(po.get("amount") or amount)
#
#     if (po.get("status") or "").upper() == "PAID":
#         # Status already PAID — only repair missing ledger row, never double balance
#         credited = await _credit_wallet_once(db, uid, amt, order_id)
#         return {
#             "claimed": False,
#             "credited": credited,
#             "already_paid": True,
#         }
#
#     # Atomic claim: only one writer sets PAID
#     if raw_response is not None:
#         result = await db.prepare(
#             """
#             UPDATE payment_orders
#             SET status = 'PAID',
#                 updated_at = CURRENT_TIMESTAMP,
#                 raw_response = ?
#             WHERE order_id = ?
#               AND UPPER(COALESCE(status, '')) != 'PAID'
#             """
#         ).bind(raw_response, order_id).run()
#     else:
#         result = await db.prepare(
#             """
#             UPDATE payment_orders
#             SET status = 'PAID',
#                 updated_at = CURRENT_TIMESTAMP
#             WHERE order_id = ?
#               AND UPPER(COALESCE(status, '')) != 'PAID'
#             """
#         ).bind(order_id).run()
#
#     if _d1_changes(result) == 0:
#         # Lost race — peer already claimed
#         await _credit_wallet_once(db, uid, amt, order_id)
#         return {
#             "claimed": False,
#             "credited": False,
#             "already_paid": True,
#         }
#
#     credited = await _credit_wallet_once(db, uid, amt, order_id)
#     return {
#         "claimed": True,
#         "credited": credited,
#         "already_paid": False,
#     }
#
#
# @router.post("/payments/create-order", status_code=status.HTTP_201_CREATED)
# async def create_payment_order(
#     data: CreatePaymentOrderRequest,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """Cashfree order for wallet top-up only. Booking stays on wallet hold."""
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#     amount = round(float(data.amount), 2)
#
#     if amount < 100:
#         raise HTTPException(status_code=400, detail="Minimum top-up is ₹100")
#
#     order_id = f"wt_{secrets.token_hex(8)}"
#     phone = str(current_user.get("mobile") or "9999999999").strip()
#     digits = "".join(c for c in phone if c.isdigit())
#     phone = digits[-10:] if len(digits) >= 10 else "9999999999"
#     email = (current_user.get("email") or "user@example.com").strip()
#     name = (current_user.get("full_name") or "User").strip()[:100]
#
#     return_url = (data.return_url or "").strip()
#     if not return_url:
#         return_url = (
#             "https://rental-backend.kudoo-live.workers.dev/api/payments/return"
#             "?order_id={order_id}"
#         )
#     elif "{order_id}" not in return_url:
#         sep = "&" if "?" in return_url else "?"
#         return_url = f"{return_url}{sep}order_id={{order_id}}"
#
#     notify_url = "https://rental-backend.kudoo-live.workers.dev/api/payments/webhook"
#
#     payload = {
#         "order_id": order_id,
#         "order_amount": amount,
#         "order_currency": "INR",
#         "customer_details": {
#             "customer_id": str(user_id)[:50],
#             "customer_phone": phone,
#             "customer_email": email,
#             "customer_name": name,
#         },
#         "order_meta": {
#             "return_url": return_url,
#             "notify_url": notify_url,
#         },
#         "order_note": data.purpose or "wallet_topup",
#         "order_tags": {
#             "user_id": user_id,
#             "purpose": data.purpose or "wallet_topup",
#         },
#     }
#
#     cf = await _cf_request(request, "POST", "/orders", payload)
#     payment_session_id = cf.get("payment_session_id")
#     cf_order_id = str(cf.get("cf_order_id") or "")
#
#     if not payment_session_id:
#         raise HTTPException(
#             status_code=502,
#             detail=cf.get("message") or "Failed to create Cashfree order",
#         )
#
#     row_id = secrets.token_hex(8)
#     await db.prepare(
#         """
#         INSERT INTO payment_orders (
#             id, user_id, order_id, cf_order_id, amount, currency,
#             purpose, status, payment_session_id, raw_response
#         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         row_id,
#         user_id,
#         order_id,
#         cf_order_id,
#         amount,
#         "INR",
#         data.purpose or "wallet_topup",
#         "CREATED",
#         payment_session_id,
#         json.dumps(cf),
#     ).run()
#
#     cfg = _cf_config(request)
#     return {
#         "order_id": order_id,
#         "cf_order_id": cf_order_id,
#         "payment_session_id": payment_session_id,
#         "amount": amount,
#         "currency": "INR",
#         "environment": cfg["mode"],
#         "purpose": data.purpose or "wallet_topup",
#         "message": "Order created. Open Cashfree checkout with payment_session_id.",
#     }
#
#
# @router.get("/payments/verify/{order_id}")
# async def verify_payment(
#     order_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """After checkout: confirm PAID and credit wallet at most once."""
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     row = await db.prepare(
#         "SELECT * FROM payment_orders WHERE order_id = ?"
#     ).bind(order_id).first()
#     if not row:
#         raise HTTPException(status_code=404, detail="Order not found")
#
#     order = dict(row)
#     if order["user_id"] != user_id:
#         raise HTTPException(status_code=403, detail="Not allowed")
#
#     async def _balance():
#         bal = await db.prepare(
#             "SELECT wallet_balance, wallet_held FROM users WHERE id = ?"
#         ).bind(user_id).first()
#         b = dict(bal) if bal else {}
#         return float(b.get("wallet_balance") or 0), float(b.get("wallet_held") or 0)
#
#     if (order.get("status") or "").upper() == "PAID":
#         available, held = await _balance()
#         return {
#             "order_id": order_id,
#             "status": "PAID",
#             "credited": True,
#             "amount": float(order.get("amount") or 0),
#             "wallet_balance": available,
#             "available_balance": available,
#             "wallet_held": held,
#             "message": "Payment already processed",
#         }
#
#     cf = await _cf_request(request, "GET", f"/orders/{order_id}")
#     order_status = (cf.get("order_status") or "").upper()
#
#     if order_status == "PAID":
#         amount = float(order.get("amount") or cf.get("order_amount") or 0)
#         result = await _mark_paid_and_credit(
#             db,
#             order_id=order_id,
#             user_id=user_id,
#             amount=amount,
#             raw_response=json.dumps(cf),
#         )
#         available, held = await _balance()
#         return {
#             "order_id": order_id,
#             "status": "PAID",
#             "credited": bool(result.get("credited") or result.get("already_paid")),
#             "amount": amount,
#             "wallet_balance": available,
#             "available_balance": available,
#             "wallet_held": held,
#             "message": (
#                 "Payment successful. Wallet credited."
#                 if result.get("credited")
#                 else "Payment already processed"
#             ),
#         }
#
#     local = (
#         "FAILED"
#         if order_status in ("EXPIRED", "TERMINATED")
#         else (order_status or "CREATED")
#     )
#     await db.prepare(
#         """
#         UPDATE payment_orders
#         SET status = ?, updated_at = CURRENT_TIMESTAMP, raw_response = ?
#         WHERE order_id = ?
#         """
#     ).bind(local, json.dumps(cf), order_id).run()
#
#     available, held = await _balance()
#     return {
#         "order_id": order_id,
#         "status": local,
#         "credited": False,
#         "cf_order_status": order_status,
#         "wallet_balance": available,
#         "available_balance": available,
#         "wallet_held": held,
#         "message": "Payment not completed yet",
#     }
#
#
# @router.post("/payments/webhook")
# async def cashfree_webhook(request: Request):
#     """Cashfree notify_url — same idempotent credit path as verify."""
#     db = request.scope["env"].DB
#     raw_body = await request.body()
#     raw_text = (
#         raw_body.decode("utf-8")
#         if isinstance(raw_body, (bytes, bytearray))
#         else str(raw_body)
#     )
#
#     cfg = _cf_config(request)
#     ts = request.headers.get("x-webhook-timestamp") or ""
#     sig = request.headers.get("x-webhook-signature") or ""
#
#     if ts and sig:
#         signed = f"{ts}{raw_text}".encode("utf-8")
#         expected = base64.b64encode(
#             hmac.new(cfg["secret"].encode("utf-8"), signed, hashlib.sha256).digest()
#         ).decode("utf-8")
#         if not hmac.compare_digest(expected, sig):
#             raise HTTPException(status_code=401, detail="Invalid webhook signature")
#
#     try:
#         payload = json.loads(raw_text)
#     except Exception:
#         raise HTTPException(status_code=400, detail="Invalid JSON")
#
#     event_type = (payload.get("type") or "").upper()
#     data = payload.get("data") or {}
#     order = data.get("order") or {}
#     payment = data.get("payment") or {}
#
#     order_id = order.get("order_id") or payload.get("order_id")
#     if not order_id:
#         return {"ok": True, "message": "ignored"}
#
#     row = await db.prepare(
#         "SELECT * FROM payment_orders WHERE order_id = ?"
#     ).bind(order_id).first()
#     if not row:
#         return {"ok": True, "message": "order not found"}
#
#     po = dict(row)
#     if (po.get("status") or "").upper() == "PAID":
#         return {"ok": True, "message": "already paid"}
#
#     pay_status = (
#         payment.get("payment_status") or order.get("order_status") or ""
#     ).upper()
#     is_success = (
#         "SUCCESS" in event_type
#         or pay_status in ("SUCCESS", "PAID")
#         or event_type == "PAYMENT_SUCCESS_WEBHOOK"
#     )
#
#     if is_success:
#         amount = float(po.get("amount") or 0)
#         await _mark_paid_and_credit(
#             db,
#             order_id=order_id,
#             user_id=po["user_id"],
#             amount=amount,
#             raw_response=raw_text,
#         )
#
#     return {"ok": True}
#
#
# @router.get("/payments/return")
# async def payment_return(order_id: Optional[str] = None):
#     return {
#         "order_id": order_id,
#         "message": "Return to app and call GET /api/payments/verify/{order_id}",
#     }
#
#
# @router.get("/payments/orders")
# async def my_payment_orders(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     rows = await db.prepare(
#         """
#         SELECT order_id, amount, status, purpose, created_at, updated_at
#         FROM payment_orders
#         WHERE user_id = ?
#         ORDER BY created_at DESC
#         LIMIT 50
#         """
#     ).bind(user_id).all()
#
#     items = rows.results if hasattr(rows, "results") else rows
#     orders = [dict(r) for r in items]
#     return {"count": len(orders), "orders": orders}



from fastapi import APIRouter, Request, Depends, HTTPException, status
from routes.profile import get_current_user
from pydantic import BaseModel, Field
from typing import Optional
import secrets
import json
import hmac
import hashlib
import base64

router = APIRouter()

# Minimum Cashfree / wallet top-up (₹). Use 1 so booking can add only the shortfall.
MIN_TOPUP = 1.0


class CreatePaymentOrderRequest(BaseModel):
    amount: float = Field(..., ge=1)  # was ge=100
    purpose: Optional[str] = "wallet_topup"
    return_url: Optional[str] = None


def _cf_config(request: Request) -> dict:
    env = request.scope.get("env")
    app_id = (getattr(env, "CASHFREE_APP_ID", None) or "").strip()
    secret = (getattr(env, "CASHFREE_SECRET_KEY", None) or "").strip()
    mode = (getattr(env, "CASHFREE_ENV", None) or "sandbox").lower().strip()
    api_version = (getattr(env, "CASHFREE_API_VERSION", None) or "2025-01-01").strip()

    if not app_id or not secret:
        raise HTTPException(
            status_code=500,
            detail="Cashfree not configured. Set CASHFREE_APP_ID and CASHFREE_SECRET_KEY",
        )

    base = (
        "https://api.cashfree.com/pg"
        if mode in ("production", "prod", "live")
        else "https://sandbox.cashfree.com/pg"
    )
    return {
        "app_id": app_id,
        "secret": secret,
        "base": base,
        "api_version": api_version,
        "mode": mode,
    }


async def _http_json(
    method: str,
    url: str,
    headers: dict,
    body: dict | None = None,
) -> tuple[int, dict]:
    """Cloudflare Workers: js.fetch first; urllib fallback."""
    payload = json.dumps(body) if body is not None else None
    last_err = None

    try:
        from js import fetch, Object
        from pyodide.ffi import to_js

        opts = {"method": method, "headers": headers}
        if payload is not None:
            opts["body"] = payload

        resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
        text = await resp.text()
        code = int(resp.status)
        try:
            data = json.loads(text) if text else {}
        except Exception:
            data = {"message": text}
        return code, data
    except ImportError:
        pass
    except Exception as e:
        last_err = e

    import urllib.request
    import urllib.error

    data_bytes = payload.encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url, data=data_bytes, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, (json.loads(text) if text else {})
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8")
        try:
            data = json.loads(text) if text else {}
        except Exception:
            data = {"message": text}
        return int(e.code), data
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Cashfree request failed: {last_err or e}",
        )


async def _cf_request(
    request: Request,
    method: str,
    path: str,
    body: dict | None = None,
) -> dict:
    cfg = _cf_config(request)
    url = f"{cfg['base']}{path}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-client-id": cfg["app_id"],
        "x-client-secret": cfg["secret"],
        "x-api-version": cfg["api_version"],
    }
    code, data = await _http_json(method, url, headers, body)
    if code >= 400:
        msg = data.get("message") if isinstance(data, dict) else str(data)
        raise HTTPException(status_code=502, detail=msg or f"Cashfree error {code}")
    return data if isinstance(data, dict) else {}


def _d1_changes(result) -> int:
    if result is None:
        return 0
    if hasattr(result, "meta") and result.meta is not None:
        return int(getattr(result.meta, "changes", 0) or 0)
    if isinstance(result, dict):
        meta = result.get("meta") or {}
        return int(meta.get("changes") or result.get("changes") or 0)
    return 0


async def _credit_wallet_once(db, user_id: str, amount: float, order_id: str) -> bool:
    amount = float(amount or 0)
    if amount <= 0:
        return False

    existing = await db.prepare(
        """
        SELECT id FROM wallet_transactions
        WHERE booking_id = ?
          AND category = 'Added'
          AND type = 'Wallet Top Up'
        LIMIT 1
        """
    ).bind(order_id).first()
    if existing:
        return False

    tx_id = secrets.token_hex(8)
    try:
        await db.prepare(
            """
            INSERT INTO wallet_transactions
                (id, user_id, type, subtitle, amount, category, booking_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        ).bind(
            tx_id,
            user_id,
            "Wallet Top Up",
            f"Cashfree {order_id}",
            abs(amount),
            "Added",
            order_id,
        ).run()
    except Exception as e:
        msg = str(e).upper()
        if "UNIQUE" in msg or "CONSTRAINT" in msg:
            return False
        raise

    await db.prepare(
        """
        UPDATE users
        SET wallet_balance = COALESCE(wallet_balance, 0) + ?,
            total_added = COALESCE(total_added, 0) + ?
        WHERE id = ?
        """
    ).bind(amount, amount, user_id).run()
    return True


async def _mark_paid_and_credit(
    db,
    *,
    order_id: str,
    user_id: str,
    amount: float,
    raw_response: str | None = None,
) -> dict:
    amount = float(amount or 0)

    row = await db.prepare(
        "SELECT status, amount, user_id FROM payment_orders WHERE order_id = ?"
    ).bind(order_id).first()
    if not row:
        return {
            "claimed": False,
            "credited": False,
            "already_paid": False,
            "missing": True,
        }

    po = dict(row)
    uid = po.get("user_id") or user_id
    amt = float(po.get("amount") or amount)

    if (po.get("status") or "").upper() == "PAID":
        credited = await _credit_wallet_once(db, uid, amt, order_id)
        return {
            "claimed": False,
            "credited": credited,
            "already_paid": True,
        }

    if raw_response is not None:
        result = await db.prepare(
            """
            UPDATE payment_orders
            SET status = 'PAID',
                updated_at = CURRENT_TIMESTAMP,
                raw_response = ?
            WHERE order_id = ?
              AND UPPER(COALESCE(status, '')) != 'PAID'
            """
        ).bind(raw_response, order_id).run()
    else:
        result = await db.prepare(
            """
            UPDATE payment_orders
            SET status = 'PAID',
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
              AND UPPER(COALESCE(status, '')) != 'PAID'
            """
        ).bind(order_id).run()

    if _d1_changes(result) == 0:
        await _credit_wallet_once(db, uid, amt, order_id)
        return {
            "claimed": False,
            "credited": False,
            "already_paid": True,
        }

    credited = await _credit_wallet_once(db, uid, amt, order_id)
    return {
        "claimed": True,
        "credited": credited,
        "already_paid": False,
    }


@router.post("/payments/create-order", status_code=status.HTTP_201_CREATED)
async def create_payment_order(
    data: CreatePaymentOrderRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Wallet top-up only.
    Amount = whatever the app sends (e.g. booking shortfall ₹50).
    Min = MIN_TOPUP (₹1), not fixed ₹100.
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]
    amount = round(float(data.amount), 2)

    if amount < MIN_TOPUP:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum top-up is ₹{int(MIN_TOPUP) if MIN_TOPUP == int(MIN_TOPUP) else MIN_TOPUP}",
        )

    order_id = f"wt_{secrets.token_hex(8)}"
    phone = str(current_user.get("mobile") or "9999999999").strip()
    digits = "".join(c for c in phone if c.isdigit())
    phone = digits[-10:] if len(digits) >= 10 else "9999999999"
    email = (current_user.get("email") or "user@example.com").strip()
    name = (current_user.get("full_name") or "User").strip()[:100]

    return_url = (data.return_url or "").strip()
    if not return_url:
        return_url = (
            "https://rental-backend.kudoo-live.workers.dev/api/payments/return"
            "?order_id={order_id}"
        )
    elif "{order_id}" not in return_url:
        sep = "&" if "?" in return_url else "?"
        return_url = f"{return_url}{sep}order_id={{order_id}}"

    notify_url = "https://rental-backend.kudoo-live.workers.dev/api/payments/webhook"

    payload = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(user_id)[:50],
            "customer_phone": phone,
            "customer_email": email,
            "customer_name": name,
        },
        "order_meta": {
            "return_url": return_url,
            "notify_url": notify_url,
        },
        "order_note": data.purpose or "wallet_topup",
        "order_tags": {
            "user_id": user_id,
            "purpose": data.purpose or "wallet_topup",
        },
    }

    cf = await _cf_request(request, "POST", "/orders", payload)
    payment_session_id = cf.get("payment_session_id")
    cf_order_id = str(cf.get("cf_order_id") or "")

    if not payment_session_id:
        raise HTTPException(
            status_code=502,
            detail=cf.get("message") or "Failed to create Cashfree order",
        )

    row_id = secrets.token_hex(8)
    await db.prepare(
        """
        INSERT INTO payment_orders (
            id, user_id, order_id, cf_order_id, amount, currency,
            purpose, status, payment_session_id, raw_response
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        row_id,
        user_id,
        order_id,
        cf_order_id,
        amount,
        "INR",
        data.purpose or "wallet_topup",
        "CREATED",
        payment_session_id,
        json.dumps(cf),
    ).run()

    cfg = _cf_config(request)
    return {
        "order_id": order_id,
        "cf_order_id": cf_order_id,
        "payment_session_id": payment_session_id,
        "amount": amount,
        "currency": "INR",
        "environment": cfg["mode"],
        "purpose": data.purpose or "wallet_topup",
        "min_topup": MIN_TOPUP,
        "message": "Order created. Open Cashfree checkout with payment_session_id.",
    }


@router.get("/payments/verify/{order_id}")
async def verify_payment(
    order_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT * FROM payment_orders WHERE order_id = ?"
    ).bind(order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")

    order = dict(row)
    if order["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    async def _balance():
        bal = await db.prepare(
            "SELECT wallet_balance, wallet_held FROM users WHERE id = ?"
        ).bind(user_id).first()
        b = dict(bal) if bal else {}
        return float(b.get("wallet_balance") or 0), float(b.get("wallet_held") or 0)

    if (order.get("status") or "").upper() == "PAID":
        available, held = await _balance()
        return {
            "order_id": order_id,
            "status": "PAID",
            "credited": True,
            "amount": float(order.get("amount") or 0),
            "wallet_balance": available,
            "available_balance": available,
            "wallet_held": held,
            "message": "Payment already processed",
        }

    cf = await _cf_request(request, "GET", f"/orders/{order_id}")
    order_status = (cf.get("order_status") or "").upper()

    if order_status == "PAID":
        amount = float(order.get("amount") or cf.get("order_amount") or 0)
        result = await _mark_paid_and_credit(
            db,
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            raw_response=json.dumps(cf),
        )
        available, held = await _balance()
        return {
            "order_id": order_id,
            "status": "PAID",
            "credited": bool(result.get("credited") or result.get("already_paid")),
            "amount": amount,
            "wallet_balance": available,
            "available_balance": available,
            "wallet_held": held,
            "message": (
                "Payment successful. Wallet credited."
                if result.get("credited")
                else "Payment already processed"
            ),
        }

    local = (
        "FAILED"
        if order_status in ("EXPIRED", "TERMINATED")
        else (order_status or "CREATED")
    )
    await db.prepare(
        """
        UPDATE payment_orders
        SET status = ?, updated_at = CURRENT_TIMESTAMP, raw_response = ?
        WHERE order_id = ?
        """
    ).bind(local, json.dumps(cf), order_id).run()

    available, held = await _balance()
    return {
        "order_id": order_id,
        "status": local,
        "credited": False,
        "cf_order_status": order_status,
        "wallet_balance": available,
        "available_balance": available,
        "wallet_held": held,
        "message": "Payment not completed yet",
    }


@router.post("/payments/webhook")
async def cashfree_webhook(request: Request):
    db = request.scope["env"].DB
    raw_body = await request.body()
    raw_text = (
        raw_body.decode("utf-8")
        if isinstance(raw_body, (bytes, bytearray))
        else str(raw_body)
    )

    cfg = _cf_config(request)
    ts = request.headers.get("x-webhook-timestamp") or ""
    sig = request.headers.get("x-webhook-signature") or ""

    if ts and sig:
        signed = f"{ts}{raw_text}".encode("utf-8")
        expected = base64.b64encode(
            hmac.new(cfg["secret"].encode("utf-8"), signed, hashlib.sha256).digest()
        ).decode("utf-8")
        if not hmac.compare_digest(expected, sig):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_text)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = (payload.get("type") or "").upper()
    data = payload.get("data") or {}
    order = data.get("order") or {}
    payment = data.get("payment") or {}

    order_id = order.get("order_id") or payload.get("order_id")
    if not order_id:
        return {"ok": True, "message": "ignored"}

    row = await db.prepare(
        "SELECT * FROM payment_orders WHERE order_id = ?"
    ).bind(order_id).first()
    if not row:
        return {"ok": True, "message": "order not found"}

    po = dict(row)
    if (po.get("status") or "").upper() == "PAID":
        return {"ok": True, "message": "already paid"}

    pay_status = (
        payment.get("payment_status") or order.get("order_status") or ""
    ).upper()
    is_success = (
        "SUCCESS" in event_type
        or pay_status in ("SUCCESS", "PAID")
        or event_type == "PAYMENT_SUCCESS_WEBHOOK"
    )

    if is_success:
        amount = float(po.get("amount") or 0)
        await _mark_paid_and_credit(
            db,
            order_id=order_id,
            user_id=po["user_id"],
            amount=amount,
            raw_response=raw_text,
        )

    return {"ok": True}


@router.get("/payments/return")
async def payment_return(order_id: Optional[str] = None):
    return {
        "order_id": order_id,
        "message": "Return to app and call GET /api/payments/verify/{order_id}",
    }


@router.get("/payments/orders")
async def my_payment_orders(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    rows = await db.prepare(
        """
        SELECT order_id, amount, status, purpose, created_at, updated_at
        FROM payment_orders
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
        """
    ).bind(user_id).all()

    items = rows.results if hasattr(rows, "results") else rows
    orders = [dict(r) for r in items]
    return {"count": len(orders), "orders": orders}