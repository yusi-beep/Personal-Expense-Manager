from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # cascading deletion of records/categories when deleting a user
    records = db.relationship("Record", backref="user", lazy=True, cascade="all, delete-orphan")
    categories = db.relationship("Category", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, candidate: str) -> bool:
        return check_password_hash(self.password, candidate)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)          # 'YYYY-MM-DD'
    type = db.Column(db.String(10), nullable=False)          # 'income' | 'expense'
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, default="")

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_category_name'),
    )

    def __repr__(self):
        return f"<Category {self.name}>"
