import secrets
from fastapi import HTTPException, status
from models.user import RegisterRequest, LoginRequest
from utils.security import hash_password, verify_password


async def register_user(data: RegisterRequest, db):
    # Check if email already exists
    existing = await db.prepare("SELECT id FROM users WHERE email = ?").bind(data.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Check if mobile already exists
    existing_mobile = await db.prepare("SELECT id FROM users WHERE mobile = ?").bind(data.mobile).first()
    if existing_mobile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mobile number already registered")

    user_id = secrets.token_hex(8)

    await db.prepare(
        """
        INSERT INTO users (id, email, mobile, password, country, city, pincode, gender, want_to)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        user_id,
        data.email,
        data.mobile,
        hash_password(data.password),
        data.country,
        data.city,
        data.pincode,
        data.gender,
        data.want_to
    ).run()

    return {
        "id": user_id,
        "email": data.email,
        "mobile": data.mobile,
        "country": data.country,
        "city": data.city,
        "gender": data.gender,
        "want_to": data.want_to,
        "message": "Registration successful"
    }


async def login_user(data: LoginRequest, db):
    user = await db.prepare("SELECT * FROM users WHERE email = ?").bind(data.email).first()

    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return {
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "mobile": user["mobile"],
            "country": user["country"],
            "city": user["city"],
            "gender": user["gender"],
            "want_to": user["want_to"],
        }
    }