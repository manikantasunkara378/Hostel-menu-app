from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# =========================================
# 🍽️ MENU MODEL
# Upgraded: added photo_url + avg_rating
# =========================================
class Menu(db.Model):
    __tablename__ = 'menu'

    id          = db.Column(db.Integer, primary_key=True)
    day         = db.Column(db.String(20), nullable=False)
    meal_type   = db.Column(db.String(20), nullable=False)
    item_name   = db.Column(db.String(100), nullable=False)
    start_time  = db.Column(db.Time)
    end_time    = db.Column(db.Time)

    # ⭐ NEW: photo + aggregated rating
    photo_url   = db.Column(db.String(300), nullable=True)
    avg_rating  = db.Column(db.Float, default=0.0)
    rating_count= db.Column(db.Integer, default=0)

    # Legacy field kept for compatibility
    rating      = db.Column(db.Float, default=0.0)

    # Relationship to individual ratings
    ratings     = db.relationship('Rating', backref='menu_item', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Menu {self.item_name}>'


# =========================================
# ⭐ RATING MODEL  (NEW)
# One row per student-vote on a menu item
# =========================================
class Rating(db.Model):
    __tablename__ = 'rating'

    id          = db.Column(db.Integer, primary_key=True)
    menu_id     = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    stars       = db.Column(db.Integer, nullable=False)   # 1-5
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Rating {self.stars}★ for menu_id={self.menu_id}>'


# =========================================
# 📝 COMPLAINT MODEL
# Upgraded: added tags + sentiment columns
# =========================================
class Complaint(db.Model):
    __tablename__ = 'complaint'

    id          = db.Column(db.Integer, primary_key=True)
    text        = db.Column(db.Text, nullable=False)
    meal_type   = db.Column(db.String(20), default='general')

    # ⭐ NEW: auto-generated tags & sentiment
    tags        = db.Column(db.String(200), default='')   # comma-separated e.g. "quality,cold,dinner"
    sentiment   = db.Column(db.String(10),  default='neutral')  # positive/negative/neutral

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Complaint {self.id}: {self.sentiment}>'


# =========================================
# 🚨 ALERT LOG MODEL  (NEW)
# Records every push alert that was fired
# =========================================
class AlertLog(db.Model):
    __tablename__ = 'alert_log'

    id          = db.Column(db.Integer, primary_key=True)
    alert_type  = db.Column(db.String(50))   # e.g. 'negative_spike', 'low_rating'
    message     = db.Column(db.Text)
    triggered_at= db.Column(db.DateTime, default=datetime.utcnow)
    resolved    = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<AlertLog {self.alert_type} @ {self.triggered_at}>'