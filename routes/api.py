import csv, io
import math
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify, g, current_app, send_file
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import asc, desc

from models.models import db, User, Record, Category

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


api_bp = Blueprint("api", __name__, url_prefix="/api")

# ---------- utils -----------

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

def _apply_record_filters(base_q, args, user_id):
    f_category  = (args.get("category") or "").strip()
    f_type      = (args.get("entry_type") or "").strip()
    f_from      = (args.get("date_from") or "").strip()
    f_to        = (args.get("date_to") or "").strip()
    f_q         = (args.get("q") or "").strip()
    sort        = args.get("sort", "desc")

    q = base_q.filter_by(user_id=user_id)
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
    return q

def _parse_date_any(s: str) -> str:
    s = (s or "").strip()
    from datetime import datetime
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        s2 = s.replace(".", "/").replace("-", "/")
        parts = [int(p) for p in s2.split("/") if p]
        if len(parts) == 3:
            # предполагаме M/D/Y
            m, d, y = parts
            return datetime(y, m, d).strftime("%Y-%m-%d")
    except Exception:
        pass
    raise ValueError(f"Unrecognized date: {s}")

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

@api_bp.get("/records/export/csv")
@token_required
def api_export_csv():
    q = _apply_record_filters(Record.query, request.args, g.api_user.id)
    records = q.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "type", "category", "amount", "description"])
    for r in records:
        writer.writerow([r.date, r.type, r.category, f"{float(r.amount):.2f}", r.description or ""])
    output.seek(0)

    filename = f"records_{g.api_user.username}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )

@api_bp.get("/records/export/pdf")
@token_required
def api_export_pdf():
    q = _apply_record_filters(Record.query, request.args, g.api_user.id)
    records = q.all()

    income = sum(float(r.amount) for r in records if r.type == "income")
    expense = sum(float(r.amount) for r in records if r.type == "expense")
    balance = income - expense

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elems = []
    elems.append(Paragraph(f"Expense Tracker — {g.api_user.username}", styles["Title"]))
    elems.append(Paragraph(f"Summary: Income {income:.2f} BGN  |  Expense {expense:.2f} BGN  |  Balance {balance:.2f} BGN", styles["Normal"]))
    elems.append(Spacer(1, 12))

    data = [["Date", "Type", "Category", "Amount (BGN)", "Description"]]
    for r in records:
        data.append([r.date, r.type.title(), r.category, f"{float(r.amount):.2f}", r.description or ""])

    table = Table(data, colWidths=[90, 70, 140, 100, 360])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f3f4f6")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (3,1), (3,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fcfcfc")]),
    ]))
    elems.append(table)
    doc.build(elems)

    buf.seek(0)
    filename = f"records_{g.api_user.username}.pdf"
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)

@api_bp.post("/records/import/csv")
@token_required
def api_import_csv():
    ALLOWED_BYTES = 5 * 1024 * 1024  # 5MB

    file = request.files.get("file")
    create_missing = (request.form.get("create_missing_categories") == "on")

    if not file or not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Please upload a .csv file"}), 400

    raw = file.read()
    if len(raw) > ALLOWED_BYTES:
        return jsonify({"error": "CSV is too large (max 5MB)"}), 400

    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("cp1251", errors="ignore")

    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames:
        reader.fieldnames = [(fn or "").strip().lower() for fn in reader.fieldnames]

    required = {"date", "type", "category", "amount", "description"}
    if not required.issubset(set(reader.fieldnames or [])):
        return jsonify({"error": "CSV header must include: date,type,category,amount,description"}), 400

    existing_cats = {c.name.lower() for c in Category.query.filter_by(user_id=g.api_user.id).all()}
    added, errors = 0, []

    for i, raw_row in enumerate(reader, start=2):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in (raw_row or {}).items()}
        try:
            date = _parse_date_any(row.get("date", ""))
            type_ = (row.get("type") or "").lower()
            if type_ not in ("income", "expense"):
                raise ValueError("Invalid type")
            cat = row.get("category") or "Uncategorized"
            amt = float(Decimal((row.get("amount","").replace(",", ".") or "0")))
            if amt <= 0:
                raise ValueError("Amount must be positive")
            desc = row.get("description","")

            if create_missing and cat.lower() not in existing_cats:
                db.session.add(Category(name=cat, user_id=g.api_user.id))
                existing_cats.add(cat.lower())

            db.session.add(Record(
                date=date, type=type_, category=cat, amount=amt,
                description=desc, user_id=g.api_user.id
            ))
            added += 1
        except Exception:
            errors.append(i)
            continue

    db.session.commit()
    res = {"imported": added}
    if errors:
        res["skipped_rows"] = errors[:10]
        res["skipped_count"] = len(errors)
        return jsonify(res), 207  # Multi-Status-like
    return jsonify(res), 201
