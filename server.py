import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import struct
import time
import uuid
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "keys.json")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Server-side Environment Configurations
SERVER_HOST = os.getenv("HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("PORT", "8799"))
AUTH_USER = os.getenv("AUTH_USER", "")
AUTH_PASS = os.getenv("AUTH_PASS", "")

security = HTTPBasic(auto_error=False)


def verify_credentials(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    # Jika tidak diset username & password di server, akses terbuka (publik/internal)
    if not AUTH_USER and not AUTH_PASS:
        return True
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Akses Ditolak: Masukkan username & password server",
            headers={"WWW-Authenticate": "Basic"},
        )
    user_ok = secrets.compare_digest(credentials.username, AUTH_USER)
    pass_ok = secrets.compare_digest(credentials.password, AUTH_PASS)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau Password salah",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


app = FastAPI(title="2FA Authenticator Hub (Server Edition)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def clean_secret(secret: str) -> str:
    if not secret:
        return ""
    # Remove spaces, dashes, and invalid chars
    cleaned = re.sub(r"[^A-Za-z2-7]", "", secret.strip()).upper()
    return cleaned


def generate_totp(secret: str) -> str:
    cleaned = clean_secret(secret)
    if not cleaned or len(cleaned) < 8:
        return "------"
    try:
        missing_padding = len(cleaned) % 8
        if missing_padding != 0:
            cleaned += "=" * (8 - missing_padding)
        key = base64.b32decode(cleaned, casefold=True)
        counter = int(time.time()) // 30
        msg = struct.pack(">Q", counter)
        digest = hmac.new(key, msg, hashlib.sha1).digest()
        offset = digest[19] & 0x0F
        code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1000000
        return f"{code:06d}"
    except Exception:
        return "ERROR"


def get_remaining_seconds() -> int:
    return 30 - (int(time.time()) % 30)


def load_keys() -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_keys(keys: List[Dict[str, Any]]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)


class AccountCreateReq(BaseModel):
    name: str
    secret: str


class AccountUpdateReq(BaseModel):
    name: str
    secret: str


class BatchImportReq(BaseModel):
    raw_text: str


@app.get("/", response_class=HTMLResponse)
async def index(_: bool = Depends(verify_credentials)):
    html_path = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(html_path):
        return "<h1>Template index.html belum ditemukan</h1>"
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/accounts")
async def get_accounts(_: bool = Depends(verify_credentials)):
    keys = load_keys()
    rem = get_remaining_seconds()
    result = []
    for k in keys:
        secret = k.get("secret", "")
        code = generate_totp(secret)
        result.append(
            {
                "id": k.get("id"),
                "name": k.get("name", "Unnamed"),
                "secret": secret,
                "code": code,
                "created_at": k.get("created_at", ""),
            }
        )
    return {"accounts": result, "remaining": rem}


@app.post("/api/accounts")
async def create_account(req: AccountCreateReq, _: bool = Depends(verify_credentials)):
    name = req.name.strip()
    secret = clean_secret(req.secret)
    if not name:
        raise HTTPException(status_code=400, detail="Nama akun wajib diisi")
    if not secret:
        raise HTTPException(status_code=400, detail="Secret key 2FA tidak valid (format Base32)")

    # Validate secret by generating code
    test_code = generate_totp(secret)
    if test_code in ("------", "ERROR"):
        raise HTTPException(status_code=400, detail="Secret key tidak dapat diproses atau format salah")

    keys = load_keys()
    acc_id = str(uuid.uuid4())[:8]
    item = {
        "id": acc_id,
        "name": name,
        "secret": secret,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    keys.append(item)
    save_keys(keys)
    return {"ok": True, "account": item}


@app.put("/api/accounts/{account_id}")
async def update_account(account_id: str, req: AccountUpdateReq, _: bool = Depends(verify_credentials)):
    keys = load_keys()
    target = next((k for k in keys if k["id"] == account_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan")

    name = req.name.strip()
    secret = clean_secret(req.secret)
    if not name:
        raise HTTPException(status_code=400, detail="Nama akun wajib diisi")
    if not secret:
        raise HTTPException(status_code=400, detail="Secret key 2FA tidak valid")

    test_code = generate_totp(secret)
    if test_code in ("------", "ERROR"):
        raise HTTPException(status_code=400, detail="Secret key tidak valid")

    target["name"] = name
    target["secret"] = secret
    save_keys(keys)
    return {"ok": True}


@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: str, _: bool = Depends(verify_credentials)):
    keys = load_keys()
    new_keys = [k for k in keys if k["id"] != account_id]
    if len(new_keys) == len(keys):
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan")
    save_keys(new_keys)
    return {"ok": True}


@app.post("/api/accounts/import")
async def import_batch(req: BatchImportReq, _: bool = Depends(verify_credentials)):
    lines = [l.strip() for l in req.raw_text.splitlines() if l.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="Data impor kosong")

    keys = load_keys()
    added = 0
    for line in lines:
        # Try delimiter: ----, |, /, tab, comma, space
        parts = []
        if "----" in line:
            parts = [p.strip() for p in line.split("----") if p.strip()]
        elif "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
        elif "\t" in line:
            parts = [p.strip() for p in line.split("\t") if p.strip()]
        elif "," in line:
            parts = [p.strip() for p in line.split(",") if p.strip()]
        else:
            parts = [p.strip() for p in line.split() if p.strip()]

        if not parts:
            continue

        if len(parts) >= 2:
            name = parts[0]
            # find which part looks like secret key
            secret = ""
            for p in parts[1:]:
                c = clean_secret(p)
                if len(c) >= 16:
                    secret = c
                    break
            if not secret:
                secret = clean_secret(parts[1])
        else:
            secret = clean_secret(parts[0])
            name = f"2FA_{len(keys) + added + 1}"

        if secret and len(secret) >= 8:
            acc_id = str(uuid.uuid4())[:8]
            keys.append({
                "id": acc_id,
                "name": name,
                "secret": secret,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            added += 1

    save_keys(keys)
    return {"ok": True, "added": added, "total": len(keys)}


@app.get("/api/calc")
async def calc_totp(secret: str, _: bool = Depends(verify_credentials)):
    c = clean_secret(secret)
    return {"secret": c, "code": generate_totp(c), "remaining": get_remaining_seconds()}


if __name__ == "__main__":
    host = SERVER_HOST
    port = SERVER_PORT
    auth_status = "Aktif (Basic Auth)" if AUTH_USER else "Nonaktif (Akses Publik)"
    print("=" * 60)
    print("  🚀 2FA Authenticator Hub - Web Server Edition")
    print("=" * 60)
    print(f"  • Host: {host}")
    print(f"  • Port: {port}")
    print(f"  • URL Akses: http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}")
    print(f"  • Proteksi Login: {auth_status}")
    print("=" * 60)
    uvicorn.run(app, host=host, port=port, log_level="info")
