import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

# 🔥 IMPORT DB + MODELS
from db import db, Menu, Rating, Complaint, AlertLog


# =========================================
# 🏷️  COMPLAINT AUTO-TAGGER
# =========================================
TAG_RULES = {
    'quality'  : ['tasteless','bland','bad taste','awful','terrible','horrible','disgusting'],
    'cold'     : ['cold','not hot','lukewarm','cool food'],
    'hot'      : ['too hot','burning','scalding'],
    'hygiene'  : ['dirty','unhygienic','cockroach','insect','hair','plastic','stone','worm'],
    'quantity' : ['less food','small portion','not enough','hungry','quantity','half plate'],
    'timing'   : ['late','delay','delayed','early','closed','timing','time'],
    'oily'     : ['oily','too much oil','greasy','fried','unhealthy'],
    'variety'  : ['same menu','boring','no variety','repetitive','same food'],
    'service'  : ['rude','staff','behaviour','attitude','service'],
    'praise'   : ['good','great','amazing','excellent','loved','tasty','delicious','awesome','crispy','fresh','best'],
}

POSITIVE_WORDS = {'good','great','amazing','excellent','love','loved','perfect','best',
                  'tasty','crispy','delicious','awesome','wonderful','fantastic','fresh'}
NEGATIVE_WORDS = {'bad','terrible','cold','worse','tasteless','undercooked','oily',
                  'unhealthy','poor','horrible','dirty','late','slow','worst',
                  'disappointed','bland','awful','disgust','hungry','rude','insect'}

def auto_tag(text):
    lower = text.lower()
    tags  = [tag for tag, kws in TAG_RULES.items() if any(k in lower for k in kws)]
    words = set(re.findall(r'\b\w+\b', lower))
    pos   = len(words & POSITIVE_WORDS)
    neg   = len(words & NEGATIVE_WORDS)
    sentiment = 'positive' if pos > neg else ('negative' if neg > pos else 'neutral')
    return list(dict.fromkeys(tags)), sentiment


# =========================================
# 🚨  PUSH-ALERT ENGINE
# =========================================
ALERT_WINDOW_HOURS   = 2
NEGATIVE_SPIKE_LIMIT = 5
LOW_RATING_THRESHOLD = 2.5
COOLDOWN_MINUTES     = 60

def _cooldown_ok(alert_type):
    cutoff = datetime.utcnow() - timedelta(minutes=COOLDOWN_MINUTES)
    recent = AlertLog.query.filter(
        AlertLog.alert_type == alert_type,
        AlertLog.triggered_at >= cutoff
    ).first()
    return recent is None

def check_and_fire_alerts():
    fired = []

    # 1. Negative spike
    window    = datetime.utcnow() - timedelta(hours=ALERT_WINDOW_HOURS)
    neg_count = Complaint.query.filter(
        Complaint.sentiment == 'negative',
        Complaint.created_at >= window
    ).count()

    if neg_count >= NEGATIVE_SPIKE_LIMIT and _cooldown_ok('negative_spike'):
        msg = (f"🚨 {neg_count} negative complaints in the last {ALERT_WINDOW_HOURS}h. "
               f"Immediate attention required!")
        db.session.add(AlertLog(alert_type='negative_spike', message=msg))
        fired.append({"type": "negative_spike", "message": msg, "level": "critical"})

    # 2. Low-rating items
    low_items = Menu.query.filter(Menu.avg_rating > 0, Menu.avg_rating < LOW_RATING_THRESHOLD).all()
    for item in low_items:
        atype = f'low_rating_{item.id}'
        if _cooldown_ok(atype):
            msg = (f"⭐ '{item.item_name}' dropped to {item.avg_rating:.1f}★ "
                   f"({item.rating_count} votes). Please review quality.")
            db.session.add(AlertLog(alert_type=atype, message=msg))
            fired.append({"type":"low_rating","item":item.item_name,
                          "rating":item.avg_rating,"message":msg,"level":"warning"})

    if fired:
        db.session.commit()
    return fired


# =========================================
# 🏗️  APP FACTORY
# =========================================
def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)

    if test_config:
        app.config.update(test_config)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hostel.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
        app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024   # 5 MB

    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/uploads'), exist_ok=True)
    db.init_app(app)

    # ─────────────────────────────────────────
    @app.route('/')
    def home():
        return jsonify({"message": "Hostel Menu API Running 🚀"})

    # ─────────────────────────────────────────
    # 🍽️  GET MENU
    # ─────────────────────────────────────────
    @app.route('/menu')
    def get_menu():
        meal_type = request.args.get('type', '').lower()
        today     = datetime.now().strftime('%A').lower()

        data = Menu.query.filter(
            db.func.lower(Menu.day)       == today,
            db.func.lower(Menu.meal_type) == meal_type
        ).all()
        if not data:
            data = Menu.query.filter(db.func.lower(Menu.meal_type) == meal_type).all()

        result = []
        for item in data:
            result.append({
                "id"          : item.id,
                "item_name"   : item.item_name,
                "day"         : item.day,
                "meal_type"   : item.meal_type,
                "start_time"  : str(item.start_time),
                "end_time"    : str(item.end_time),
                "avg_rating"  : round(item.avg_rating, 1),
                "rating_count": item.rating_count,
                "photo_url"   : f"/static/uploads/{item.photo_url}" if item.photo_url else None,
            })
        return jsonify(result)

    # ─────────────────────────────────────────
    # ➕  ADD MENU  (multipart supports photo)
    # ─────────────────────────────────────────
    @app.route('/add-menu', methods=['POST'])
    def add_menu():
        if request.content_type and 'multipart' in request.content_type:
            form       = request.form
            photo_file = request.files.get('photo')
        else:
            form       = request.json or {}
            photo_file = None

        item_name = form.get('item_name','').strip()
        day       = form.get('day','').lower()
        meal_type = form.get('meal_type','').lower()
        start_str = form.get('start_time','07:00 AM')
        end_str   = form.get('end_time','09:00 AM')

        if not item_name:
            return jsonify({"error": "item_name is required"}), 400

        # Save photo
        photo_filename = None
        if photo_file and photo_file.filename:
            ext = os.path.splitext(photo_file.filename)[1].lower()
            if ext not in {'.jpg','.jpeg','.png','.webp','.gif'}:
                return jsonify({"error": "Invalid image format"}), 400
            safe      = re.sub(r'[^a-z0-9]','_', item_name.lower())
            photo_filename = f"{safe}_{int(datetime.utcnow().timestamp())}{ext}"
            photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        try:
            start_time = datetime.strptime(start_str, '%I:%M %p').time()
            end_time   = datetime.strptime(end_str,   '%I:%M %p').time()
        except ValueError:
            return jsonify({"error": "Time must be HH:MM AM/PM"}), 400

        new_item = Menu(
            day=day, meal_type=meal_type, item_name=item_name,
            start_time=start_time, end_time=end_time, photo_url=photo_filename
        )
        db.session.add(new_item)
        db.session.commit()

        return jsonify({
            "message"  : "Menu added successfully",
            "id"       : new_item.id,
            "photo_url": f"/static/uploads/{photo_filename}" if photo_filename else None
        })

    # ─────────────────────────────────────────
    # 📸  UPDATE PHOTO ONLY
    # ─────────────────────────────────────────
    @app.route('/menu/<int:item_id>/photo', methods=['POST'])
    def update_photo(item_id):
        item = Menu.query.get(item_id)
        if not item:
            return jsonify({"error": "Item not found"}), 404

        photo_file = request.files.get('photo')
        if not photo_file or not photo_file.filename:
            return jsonify({"error": "No photo provided"}), 400

        ext = os.path.splitext(photo_file.filename)[1].lower()
        if ext not in {'.jpg','.jpeg','.png','.webp','.gif'}:
            return jsonify({"error": "Invalid image format"}), 400

        if item.photo_url:
            old = os.path.join(app.config['UPLOAD_FOLDER'], item.photo_url)
            if os.path.exists(old):
                os.remove(old)

        safe     = re.sub(r'[^a-z0-9]','_', item.item_name.lower())
        filename = f"{safe}_{int(datetime.utcnow().timestamp())}{ext}"
        photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        item.photo_url = filename
        db.session.commit()
        return jsonify({"message":"Photo updated","photo_url":f"/static/uploads/{filename}"})

    # ─────────────────────────────────────────
    # ❌  DELETE MENU
    # ─────────────────────────────────────────
    @app.route('/delete-menu/<int:item_id>', methods=['DELETE'])
    def delete_menu(item_id):
        item = Menu.query.get(item_id)
        if not item:
            return jsonify({"error": "Item not found"}), 404

        if item.photo_url:
            path = os.path.join(app.config['UPLOAD_FOLDER'], item.photo_url)
            if os.path.exists(path):
                os.remove(path)

        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Deleted successfully"})

    # ─────────────────────────────────────────
    # ⭐  RATE A MENU ITEM
    # ─────────────────────────────────────────
    @app.route('/rate', methods=['POST'])
    def rate_item():
        data    = request.json
        menu_id = data.get('menu_id')
        stars   = data.get('stars')

        if not menu_id or stars is None:
            return jsonify({"error": "menu_id and stars required"}), 400
        if not isinstance(stars, int) or not (1 <= stars <= 5):
            return jsonify({"error": "stars must be 1-5"}), 400

        item = Menu.query.get(menu_id)
        if not item:
            return jsonify({"error": "Menu item not found"}), 404

        db.session.add(Rating(menu_id=menu_id, stars=stars))
        db.session.flush()

        all_r          = Rating.query.filter_by(menu_id=menu_id).all()
        item.avg_rating  = round(sum(r.stars for r in all_r) / len(all_r), 2)
        item.rating_count= len(all_r)
        item.rating      = item.avg_rating

        alerts = check_and_fire_alerts()
        db.session.commit()

        return jsonify({
            "message"     : "Rating saved",
            "avg_rating"  : item.avg_rating,
            "rating_count": item.rating_count,
            "alerts"      : alerts
        })

    # ─────────────────────────────────────────
    # 📝  ADD COMPLAINT  (auto-tagged)
    # ─────────────────────────────────────────
    @app.route('/complaint', methods=['POST'])
    def add_complaint():
        data    = request.json
        message = (data.get('message') or '').strip()

        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400

        tags, sentiment = auto_tag(message)

        new = Complaint(
            text      = message,
            meal_type = data.get('meal_type', 'general'),
            tags      = ','.join(tags),
            sentiment = sentiment,
        )
        db.session.add(new)
        db.session.commit()

        alerts = check_and_fire_alerts()

        return jsonify({
            "message"  : "Feedback saved successfully",
            "tags"     : tags,
            "sentiment": sentiment,
            "alerts"   : alerts
        })

    # ─────────────────────────────────────────
    # 📋  GET COMPLAINTS  (paginated + filtered)
    # ─────────────────────────────────────────
    @app.route('/complaints')
    def get_complaints():
        sentiment = request.args.get('sentiment','').lower()
        tag       = request.args.get('tag','').lower()
        page      = int(request.args.get('page', 1))
        per_page  = int(request.args.get('limit', 20))

        query = Complaint.query.order_by(Complaint.created_at.desc())
        if sentiment in ('positive','negative','neutral'):
            query = query.filter(Complaint.sentiment == sentiment)
        if tag:
            query = query.filter(Complaint.tags.contains(tag))

        total      = query.count()
        complaints = query.offset((page-1)*per_page).limit(per_page).all()

        return jsonify({
            "complaints": [{
                "id"        : c.id,
                "message"   : c.text,
                "meal_type" : c.meal_type,
                "tags"      : c.tags.split(',') if c.tags else [],
                "sentiment" : c.sentiment,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M")
            } for c in complaints],
            "total": total,
            "page" : page,
            "pages": (total + per_page - 1) // per_page
        })

    # ─────────────────────────────────────────
    # 📊  TAG SUMMARY
    # ─────────────────────────────────────────
    @app.route('/complaints/tags')
    def complaint_tag_summary():
        tag_counts = {}
        for c in Complaint.query.all():
            for t in (c.tags or '').split(','):
                t = t.strip()
                if t:
                    tag_counts[t] = tag_counts.get(t,0) + 1
        return jsonify(sorted(
            [{"tag":t,"count":n} for t,n in tag_counts.items()],
            key=lambda x: -x['count']
        ))

    # ─────────────────────────────────────────
    # 🚨  GET ALERTS
    # ─────────────────────────────────────────
    @app.route('/alerts')
    def get_alerts():
        hours = int(request.args.get('hours', 24))
        since = datetime.utcnow() - timedelta(hours=hours)
        logs  = AlertLog.query.filter(
            AlertLog.triggered_at >= since
        ).order_by(AlertLog.triggered_at.desc()).all()

        return jsonify([{
            "id"          : a.id,
            "type"        : a.alert_type,
            "message"     : a.message,
            "triggered_at": a.triggered_at.strftime("%Y-%m-%d %H:%M"),
            "resolved"    : a.resolved
        } for a in logs])

    # ─────────────────────────────────────────
    # ✅  RESOLVE ALERT
    # ─────────────────────────────────────────
    @app.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
    def resolve_alert(alert_id):
        alert = AlertLog.query.get(alert_id)
        if not alert:
            return jsonify({"error": "Alert not found"}), 404
        alert.resolved = True
        db.session.commit()
        return jsonify({"message": "Alert resolved"})

    # ─────────────────────────────────────────
    # 🌐  GLOBAL ERROR HANDLERS
    # ─────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Route not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large. Max 5 MB."}), 413

    return app


# =========================================
# ▶️  RUN SERVER
# =========================================
app = create_app()

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)