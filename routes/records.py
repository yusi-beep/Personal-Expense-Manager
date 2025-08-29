import csv
import io
from sqlalchemy import desc, asc
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models.models import db, Record, Category
from decimal import Decimal, InvalidOperation
from datetime import datetime

records_bp = Blueprint("records", __name__, url_prefix="/records")

@records_bp.route("/")
@login_required
def list_records():
    # URL params
    sort = request.args.get("sort", "desc")                 # 'asc' | 'desc'
    page_str = request.args.get("page", "1")
    per_str  = request.args.get("per", "20")

    # filters
    f_category = (request.args.get("category") or "").strip()
    f_type     = (request.args.get("entry_type") or "").strip()    # 'income' | 'expense' | ''
    f_from     = (request.args.get("date_from") or "").strip()    # 'YYYY-MM-DD'
    f_to       = (request.args.get("date_to") or "").strip()      # 'YYYY-MM-DD'
    f_q        = (request.args.get("q") or "").strip()       # search in description

    # sanitize pagination
    try:
        page = max(1, int(page_str))
    except ValueError:
        page = 1
    try:
        per_page = max(5, min(100, int(per_str)))          # clamp 5..100
    except ValueError:
        per_page = 20
        per_str = "20"

    # base query
    q = Record.query.filter_by(user_id=current_user.id)

    # ------- Apply filters -------
    if f_category:
        q = q.filter(Record.category == f_category)

    if f_type in ("income", "expense"):
        q = q.filter(Record.type == f_type)

    # Record.date is 'YYYY-MM-DD' 
    if f_from:
        q = q.filter(Record.date >= f_from)
    if f_to:
        q = q.filter(Record.date <= f_to)

    if f_q:
        # simple "contains" on description (case-insensitive за SQLite)
        q = q.filter(Record.description.ilike(f"%{f_q}%"))

    # sort per date
    order_col = asc(Record.date) if sort == "asc" else desc(Record.date)
    q = q.order_by(order_col)

    # paginate (Flask-SQLAlchemy 3.x)
    pagination = db.paginate(q, page=page, per_page=per_page, error_out=False)
    records = pagination.items

    # for select „Category“ 
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()

    # calculate window for pages 
    p = pagination.page
    total = pagination.pages
    start = 1 if p - 2 <= 1 else p - 2
    end   = total if p + 2 >= total else p + 2

    return render_template(
        "records.html",
        records=records,
        categories=categories, # for select
        sort=sort,
        per=per_str,
        # pagination state
        pagination=pagination, p=p, total=total, start=start, end=end,
        # current filters (за sticky UI)
        f_category=f_category, f_type=f_type, f_from=f_from, f_to=f_to, f_q=f_q
    )

@records_bp.route("/export/csv")
@login_required
def export_csv():
    # can filter period query (?scope=&date=), there is all
    records = Record.query.filter_by(user_id=current_user.id).order_by(Record.date.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["date", "type", "category", "amount", "description"])
    for r in records:
        writer.writerow([r.date, r.type, r.category, f"{r.amount:.2f}", r.description or ""])

    output.seek(0)
    filename = f"records_{current_user.username}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

@records_bp.route("/export/pdf")
@login_required
def export_pdf():
    # selectable: filter period; there is only for user
    records = Record.query.filter_by(user_id=current_user.id).order_by(Record.date.asc()).all()
    income = sum(r.amount for r in records if r.type == "income")
    expense = sum(r.amount for r in records if r.type == "expense")
    balance = income - expense

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)

    styles = getSampleStyleSheet()
    elems = []
    elems.append(Paragraph(f"Expense Tracker — {current_user.username}", styles["Title"]))
    elems.append(Paragraph(f"Summary: Income {income:.2f} BGN  |  Expense {expense:.2f} BGN  |  Balance {balance:.2f} BGN", styles["Normal"]))
    elems.append(Spacer(1, 12))

    data = [["Date", "Type", "Category", "Amount (BGN)", "Description"]]
    for r in records:
        data.append([r.date, r.type.title(), r.category, f"{r.amount:.2f}", r.description or ""])

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
    filename = f"records_{current_user.username}.pdf"
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)

def _parse_date_any(s: str) -> str:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%-m/%-d/%Y", "%d/%m/%Y"):  # покриваме и EU
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    # fallback: rough split
    try:
        s2 = s.replace(".", "/").replace("-", "/")
        parts = s2.split("/")
        if len(parts) == 3:
            # guess M/D/Y
            m, d, y = [int(p) for p in parts]
            return datetime(y, m, d).strftime("%Y-%m-%d")
    except Exception:
        pass
    raise ValueError(f"Unrecognized date: {s}")

@records_bp.route("/import/csv", methods=["POST"])
@login_required
def import_csv():
    ALLOWED_MIME = {"text/csv", "application/vnd.ms-excel"}
    MAX_BYTES = 5 * 1024 * 1024  # 5MB

    file = request.files.get("file")
    create_missing_categories = request.form.get("create_missing_categories") == "on"

    # Is the file present
    if not file or file.filename.strip() == "":
        flash("Please choose a CSV file.", "danger")
        return redirect(url_for("records.list_records"))

    # quick extension check
    if not file.filename.lower().endswith(".csv"):
        flash("Please upload a .csv file.", "danger")
        return redirect(url_for("records.list_records"))

    # read once and check size
    raw = file.read()
    if len(raw) > MAX_BYTES:
        flash("CSV is too large (max 5MB).", "danger")
        return redirect(url_for("records.list_records"))

    # try for decoding
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("cp1251", errors="ignore")

    reader = csv.DictReader(io.StringIO(content))

    # normalise header's
    if reader.fieldnames:
        reader.fieldnames = [ (fn or "").strip().lower() for fn in reader.fieldnames ]

    required = {"date", "type", "category", "amount", "description"}
    if not required.issubset(set(reader.fieldnames or [])):
        flash("CSV header must include: date,type,category,amount,description", "danger")
        return redirect(url_for("records.list_records"))

    # cash for existing categories for this  user (case-insensitive)
    existing_cats = {c.name.lower() for c in Category.query.filter_by(user_id=current_user.id).all()}

    added_count = 0
    errors = []  # keep row numbers (start from 2, becouse row  1 is header)

    for i, raw_row in enumerate(reader, start=2):
        # normalize keys/values (strip)
        row = { (k or "").strip().lower(): (v or "").strip() for k, v in (raw_row or {}).items() }

        try:
            # date
            date = _parse_date_any(row.get("date", ""))

            # type
            type_ = (row.get("type", "") or "").lower()
            if type_ not in ("income", "expense"):
                raise ValueError("Invalid type")

            # category
            cat = row.get("category", "")
            if not cat:
                cat = "Uncategorized"

            # amount
            amt_raw = (row.get("amount", "") or "").replace(",", ".")
            amt = float(Decimal(amt_raw))
            if amt <= 0:
                raise ValueError("Amount must be positive")

            # description
            desc = row.get("description", "")

            # if necessary, create a missing category (for this user), keep in set avoidable dublicates
            if create_missing_categories and cat.lower() not in existing_cats:
                db.session.add(Category(name=cat, user_id=current_user.id))
                existing_cats.add(cat.lower())

            # record
            db.session.add(Record(
                date=date,
                type=type_,
                category=cat,
                amount=amt,
                description=desc,
                user_id=current_user.id
            ))
            added_count += 1

        except Exception:
            errors.append(i)
            continue

    db.session.commit()

    # message to 10 number   of mising lines
    if errors:
        skip_info = ", ".join(map(str, errors[:10])) + (" ..." if len(errors) > 10 else "")
        flash(f"Imported {added_count} records. Skipped rows: {skip_info}", "warning")
    else:
        flash(f"Imported {added_count} records.", "success")

    return redirect(url_for("records.list_records"))

@records_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_record():
    categories = Category.query.filter_by(user_id=current_user.id).all()

    if request.method == "POST":
        entry_type = (request.form.get("type") or "").strip().lower()
        category = (request.form.get("category") or "").strip()
        amount_raw = (request.form.get("amount") or "").replace(",", ".").strip()
        date_val = request.form.get("date") or datetime.now().strftime("%Y-%m-%d")
        desc = (request.form.get("description") or "").strip()

        if entry_type not in ("income", "expense"):
            flash("Invalid type. Choose Income or Expense.", "danger")
            return render_template("add.html", categories=categories)

        if not category:
            flash("Please select a category.", "danger")
            return render_template("add.html", categories=categories)

        try:
            amount = Decimal(amount_raw)
            if amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            flash("Amount must be a positive number.", "danger")
            # return the entered values so you don't have to type them again (selectable)
            return render_template("add.html", categories=categories)

        rec = Record(
            date=date_val,
            type=entry_type,
            category=category,
            amount=float(amount),  # save float
            description=desc,
            user_id=current_user.id
        )
        db.session.add(rec)
        db.session.commit()
        flash("Record added successfully.", "success")
        return redirect(url_for("records.list_records"))

    return render_template("add.html", categories=categories)

@records_bp.route("/edit/<int:id>", methods=["GET","POST"])
@login_required
def edit_record(id):
    record = Record.query.get_or_404(id)
    if record.user_id != current_user.id:
        return "Unauthorized", 403

    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()

    if request.method == "POST":
        entry_type = (request.form.get("type") or "").strip().lower()
        category   = (request.form.get("category") or "").strip()
        date_val   = (request.form.get("date") or record.date).strip()
        desc       = (request.form.get("description") or "").strip()
        amt_raw    = (request.form.get("amount") or "").replace(",", ".").strip()

        # type
        if entry_type not in ("income", "expense"):
            flash("Invalid type. Choose Income or Expense.", "danger")
            return render_template("edit_record.html", record=record, categories=categories)

        # date
        try:
            datetime.strptime(date_val, "%Y-%m-%d")
        except ValueError:
            flash("Date must be YYYY-MM-DD.", "danger")
            return render_template("edit_record.html", record=record, categories=categories)

        # category (must exist for this user)
        if not any(c.name == category for c in categories):
            flash("Please pick an existing category.", "danger")
            return render_template("edit_record.html", record=record, categories=categories)

        # amount
        try:
            amount = Decimal(amt_raw)
            if amount <= 0:
                raise InvalidOperation
        except Exception:
            flash("Amount must be a positive number.", "danger")
            return render_template("edit_record.html", record=record, categories=categories)

        record.type = entry_type
        record.category = category
        record.date = date_val
        record.amount = float(amount)
        record.description = desc
        db.session.commit()
        flash("Record updated.", "success")
        return redirect(url_for("records.list_records"))

    return render_template("edit_record.html", record=record, categories=categories)

@records_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_record(id):
    record = Record.query.get_or_404(id)
    if record.user_id != current_user.id:
        return "Unauthorized", 403
    db.session.delete(record)
    db.session.commit()
    flash("Record deleted.", "success")
    return redirect(url_for("records.list_records"))

