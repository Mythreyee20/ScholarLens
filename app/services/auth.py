
import os
from datetime import datetime, timedelta, timezone

import jwt
import psycopg
from dotenv import load_dotenv
from pwdlib import PasswordHash
from psycopg.errors import UniqueViolation

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer()


def get_db_url():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is missing")
    return url


def get_secret():
    load_dotenv()
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY is missing in .env")
    return secret


def init_auth_db():
    with psycopg.connect(get_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id BIGSERIAL PRIMARY KEY,
                    client_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'client',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            cur.execute("""
                ALTER TABLE scholarship_chunks
                ADD COLUMN IF NOT EXISTS client_id BIGINT
                REFERENCES clients(id);
            """)


def register_client(client_name, email, password):
    hashed_password = password_hash.hash(password)

    try:
        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO clients
                    (client_name, email, password_hash, role)
                    VALUES (%s, %s, %s, 'client')
                    RETURNING id, client_name, email, role;
                """, (client_name, email.lower(), hashed_password))

                row = cur.fetchone()

        return {
            "id": row[0],
            "client_name": row[1],
            "email": row[2],
            "role": row[3],
        }

    except UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )


def authenticate_client(email, password):
    with psycopg.connect(get_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, client_name, email, password_hash, role
                FROM clients
                WHERE email = %s;
            """, (email.lower(),))
            user = cur.fetchone()

    if not user or not password_hash.verify(password, user[3]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "id": user[0],
        "client_name": user[1],
        "email": user[2],
        "role": user[4],
    }


def create_access_token(user_id):
    load_dotenv()
    expiry = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expiry),
    }

    return jwt.encode(payload, get_secret(), algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            get_secret(),
            algorithms=["HS256"],
        )
        user_id = int(payload["sub"])

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    with psycopg.connect(get_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, client_name, email, role
                FROM clients
                WHERE id = %s;
            """, (user_id,))
            user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": user[0],
        "client_name": user[1],
        "email": user[2],
        "role": user[3],
    }
