import math
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify, g, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import asc, desc

from models.models import db, User, Record, Category

api_bp = Blueprint("api", __name__, url_prefix="/api")

# ---------- utils ----------

def _s():
    # serializer for tokens
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="api-token")

def generate_token(user_id: int, expires_sec: int = 60 * 60 * 24 * 7) -> str:
    # NB: expires is controlled at verify (max_age)
    return _s().dumps({"uid": user_id, "exp": expires_sec})

def verify_token(token: str):
    try:
        data = _s().loads(token, max_age=60 * 60 * 24 * 7)  # 7 days by default
        return data.get("uid")
    except SignatureExpired:
        return None
    except BadSignature:
        return None

def token_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        parts = auth.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            uid = verify_token(parts[1])
            if uid:
                user = User.query.get(uid)
                if user:
                    g.api_user = user
                    return f(*args, **kwargs)
        return jsonify({"error": "Unauthorized"}), 401
    return wrapper

def parse_date_yyyy_mm_dd(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def record_to_dict(r: Record):
    return {
        "id": r.id,
        "date": r.date,
        "type": r.type,
        "category": r.category,
        "amount": float(r.amount),
        "description": r.description or "",
    }

# ---------- auth ----------

@api_bp.post("/login")
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        # if you don't have User.check_password, chachge with werkzeug.security.check_password_hash(user.password, password)
        return jsonify({"error": "invalid credentials"}), 401

    token = generate_token(user.id)
    return jsonify({"token": token, "user": {"id": user.id, "username": user.username}}), 200

@api_bp.get("/me")
@token_required
def api_me():
    u = g.api_user
    return jsonify({"id": u.id, "username": u.username})

# ---------- categories ----------

@api_bp.get("/categories")
@token_required
def api_list_categories():
    cats = Category.query.filter_by(user_id=g.api_user.id).order_by(Category.name.asc()).all()
    return jsonify([{"id": c.id, "name": c.name} for c in cats])

@api_bp.post("/categories")
@token_required
def api_create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    exists = (Category.query
              .filter(Category.user_id == g.api_user.id)
              .filter(db.func.lower(Category.name) == name.lower())
              .first())
    if exists:
        return jsonify({"error": "category already exists"}), 409

    c = Category(name=name, user_id=g.api_user.id)
    db.session.add(c)
    db.session.commit()
    return jsonify({"id": c.id, "name": c.name}), 201

@api_bp.delete("/categories/<int:cid>")
@token_required
def api_delete_category(cid):
    c = Category.query.get_or_404(cid)
    if c.user_id != g.api_user.id:
        return jsonify({"error": "forbidden"}), 403
    db.session.delete(c)
    db.session.commit()
    return jsonify({"status": "deleted"})

# ---------- records (filters + pagination) ----------

@api_bp.get("/records")
@token_required
def api_list_records():
    # filters
    f_category  = (request.args.get("category") or "").strip()
    f_type      = (request.args.get("entry_type") or "").strip()
    f_from      = (request.args.get("date_from") or "").strip()
    f_to        = (request.args.get("date_to") or "").strip()
    f_q         = (request.args.get("q") or "").strip()
    sort        = request.args.get("sort", "desc")
    page        = max(1, int(request.args.get("page", 1)))
    per_page    = min(100, max(1, int(request.args.get("per", 20))))

    q = Record.query.filter_by(user_id=g.api_user.id)

    if f_category:
        q = q.filter(Record.category == f_category)
    if f_type in ("income", "expense"):
        q = q.filter(Record.type == f_type)
    if f_from:
        q = q.filter(Record.date >= f_from)
    if f_to:
        q = q.filter(Record.date <= f_to)
    if f_q:
        q = q.filter(Record.description.ilike(f"%{f_q}%"))

    q = q.order_by(asc(Record.date) if sort == "asc" else desc(Record.date))

    pagination = db.paginate(q, page=page, per_page=per_page, error_out=False)
    items = [record_to_dict(r) for r in pagination.items]

    return jsonify({
        "items": items,
        "page": pagination.page,
        "per": per_page,
        "total": pagination.total,
        "pages": pagination.pages
    })

@api_bp.post("/records")
@token_required
def api_create_record():
    data = request.get_json(silent=True) or {}
    date_val = (data.get("date") or "").strip()
    entry_type = (data.get("type") or "").strip().lower()
    category = (data.get("category") or "").strip()
    desc = (data.get("description") or "").strip()
    amt_raw = str(data.get("amount") or "").replace(",", ".").strip()

    # date
    if not parse_date_yyyy_mm_dd(date_val):
        return jsonify({"error": "date must be YYYY-MM-DD"}), 400

    # type
    if entry_type not in ("income", "expense"):
        return jsonify({"error": "type must be 'income' or 'expense'"}), 400

    # category
    if not category:
        return jsonify({"error": "category is required"}), 400
    # must exist for this user (or optional create_if_missing)
    owner_cat = Category.query.filter_by(user_id=g.api_user.id, name=category).first()
    if not owner_cat:
        return jsonify({"error": "category does not exist"}), 400

    # amount
    try:
        amount = Decimal(amt_raw)
        if amount <= 0:
            raise InvalidOperation
    except Exception:
        return jsonify({"error": "amount must be a positive number"}), 400

    r = Record(
        date=date_val, type=entry_type, category=category,
        amount=float(amount), description=desc, user_id=g.api_user.id
    )
    db.session.add(r)
    db.session.commit()
    return jsonify(record_to_dict(r)), 201

@api_bp.get("/records/<int:rid>")
@token_required
def api_get_record(rid):
    r = Record.query.get_or_404(rid)
    if r.user_id != g.api_user.id:
        return jsonify({"error": "forbidden"}), 403
    return jsonify(record_to_dict(r))

@api_bp.put("/records/<int:rid>")
@api_bp.patch("/records/<int:rid>")
@token_required
def api_update_record(rid):
    r = Record.query.get_or_404(rid)
    if r.user_id != g.api_user.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}

    if "date" in data:
        d = (str(data.get("date")) or "").strip()
        if not parse_date_yyyy_mm_dd(d):
            return jsonify({"error": "date must be YYYY-MM-DD"}), 400
        r.date = d

    if "type" in data:
        t = (str(data.get("type")) or "").strip().lower()
        if t not in ("income", "expense"):
            return jsonify({"error": "type must be 'income' or 'expense'"}), 400
        r.type = t

    if "category" in data:
        c = (str(data.get("category")) or "").strip()
        if not Category.query.filter_by(user_id=g.api_user.id, name=c).first():
            return jsonify({"error": "category does not exist"}), 400
        r.category = c

    if "amount" in data:
        amt_raw = str(data.get("amount")).replace(",", ".")
        try:
            amount = Decimal(amt_raw)
            if amount <= 0:
                raise InvalidOperation
        except Exception:
            return jsonify({"error": "amount must be a positive number"}), 400
        r.amount = float(amount)

    if "description" in data:
        r.description = str(data.get("description") or "")

    db.session.commit()
    return jsonify(record_to_dict(r))

@api_bp.delete("/records/<int:rid>")
@token_required
def api_delete_record(rid):
    r = Record.query.get_or_404(rid)
    if r.user_id != g.api_user.id:
        return jsonify({"error": "forbidden"}), 403
    db.session.delete(r)
    db.session.commit()
    return jsonify({"status": "deleted"})
