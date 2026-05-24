import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app
from db  import db, Menu, Complaint, Rating, AlertLog
from datetime import time


@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "UPLOAD_FOLDER": "/tmp/test_uploads",
    })
    with app.app_context():
        db.create_all()
        item = Menu(day='monday', meal_type='lunch', item_name='Test Food',
                    start_time=time(12,0), end_time=time(14,0))
        db.session.add(item)
        db.session.commit()
    with app.test_client() as c:
        yield c


# ── Basic routes ──────────────────────────────
def test_home(client):
    res = client.get('/')
    assert res.status_code == 200
    assert 'message' in res.get_json()

def test_get_menu(client):
    res = client.get('/menu?type=lunch')
    data = res.get_json()
    assert res.status_code == 200
    assert isinstance(data, list)
    # New fields present
    assert 'avg_rating'   in data[0]
    assert 'rating_count' in data[0]
    assert 'photo_url'    in data[0]

# ── Add menu ──────────────────────────────────
def test_add_menu(client):
    res = client.post('/add-menu', json={
        "day":"tuesday","meal_type":"breakfast",
        "item_name":"Poha","start_time":"07:00 AM","end_time":"09:00 AM"
    })
    data = res.get_json()
    assert res.status_code == 200
    assert data['message'] == 'Menu added successfully'
    assert 'id' in data

# ── Delete menu ───────────────────────────────
def test_delete_menu(client):
    with client.application.app_context():
        item = Menu(day='wed', meal_type='dinner', item_name='Delete Me',
                    start_time=time(19,0), end_time=time(21,0))
        db.session.add(item); db.session.commit()
        iid = item.id
    res = client.delete(f'/delete-menu/{iid}')
    assert res.status_code == 200

def test_delete_not_found(client):
    assert client.delete('/delete-menu/9999').status_code == 404

# ── ⭐ Rating ─────────────────────────────────
def test_rate_item(client):
    # Get menu_id from list
    items = client.get('/menu?type=lunch').get_json()
    mid   = items[0]['id']

    res  = client.post('/rate', json={"menu_id": mid, "stars": 4})
    data = res.get_json()
    assert res.status_code == 200
    assert data['avg_rating']   == 4.0
    assert data['rating_count'] == 1

def test_rate_invalid_stars(client):
    items = client.get('/menu?type=lunch').get_json()
    mid   = items[0]['id']
    res   = client.post('/rate', json={"menu_id": mid, "stars": 6})
    assert res.status_code == 400

def test_rate_accumulates(client):
    items = client.get('/menu?type=lunch').get_json()
    mid   = items[0]['id']
    client.post('/rate', json={"menu_id": mid, "stars": 2})
    res   = client.post('/rate', json={"menu_id": mid, "stars": 4})
    data  = res.get_json()
    assert data['rating_count'] == 2
    assert data['avg_rating']   == 3.0

# ── 📝 Complaint + auto-tagging ───────────────
def test_add_complaint_with_tags(client):
    res  = client.post('/complaint', json={"message":"The food was cold and oily","meal_type":"lunch"})
    data = res.get_json()
    assert res.status_code == 200
    assert 'tags'      in data
    assert 'sentiment' in data
    assert data['sentiment'] == 'negative'
    assert 'cold' in data['tags'] or 'oily' in data['tags']

def test_add_complaint_positive(client):
    res  = client.post('/complaint', json={"message":"Great breakfast today! Amazing and fresh."})
    data = res.get_json()
    assert data['sentiment'] == 'positive'
    assert 'praise' in data['tags']

def test_add_complaint_empty(client):
    assert client.post('/complaint', json={"message":""}).status_code == 400

# ── 📋 Get complaints (paginated) ─────────────
def test_get_complaints_structure(client):
    client.post('/complaint', json={"message":"Test feedback"})
    res  = client.get('/complaints')
    data = res.get_json()
    assert 'complaints' in data
    assert 'total'      in data
    assert 'page'       in data
    assert 'pages'      in data

def test_get_complaints_sentiment_filter(client):
    client.post('/complaint', json={"message":"Terrible dinner, cold and tasteless"})
    res  = client.get('/complaints?sentiment=negative')
    data = res.get_json()
    for c in data['complaints']:
        assert c['sentiment'] == 'negative'

def test_complaints_have_tags(client):
    client.post('/complaint', json={"message":"Late lunch, dirty plates and rude staff"})
    res  = client.get('/complaints')
    c    = res.get_json()['complaints'][0]
    assert isinstance(c['tags'], list)
    assert 'message' in c

# ── 📊 Tag summary ────────────────────────────
def test_tag_summary(client):
    client.post('/complaint', json={"message":"cold oily dinner"})
    res  = client.get('/complaints/tags')
    data = res.get_json()
    assert isinstance(data, list)
    if data:
        assert 'tag'   in data[0]
        assert 'count' in data[0]

# ── 🚨 Alerts ─────────────────────────────────
def test_get_alerts_empty(client):
    res  = client.get('/alerts')
    data = res.get_json()
    assert isinstance(data, list)

def test_resolve_alert_not_found(client):
    res = client.post('/alerts/9999/resolve')
    assert res.status_code == 404

# ── 🌐 Error handlers ─────────────────────────
def test_404_handler(client):
    res = client.get('/nonexistent-route')
    assert res.status_code == 404
    assert 'error' in res.get_json()