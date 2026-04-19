from flask import Flask, request, jsonify
from flask_cors import CORS
from db import get_connection
from datetime import datetime

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return jsonify({"message": "Hostel Menu API Running 🚀"})
@app.route('/menu', methods=['GET'])
def get_menu():
    try:
        meal_type = request.args.get('type', '').lower()
        day = datetime.now().strftime('%A').lower()

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT id, day, meal_type, item_name, start_time, end_time
        FROM menu
        WHERE LOWER(day) = %s AND LOWER(meal_type) = %s
        """

        cursor.execute(query, (day, meal_type))
        data = cursor.fetchall()

        # 🔥 FIX: convert time to string
        for row in data:
            row['start_time'] = str(row['start_time'])
            row['end_time'] = str(row['end_time'])

        conn.close()

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ➕ ADD MENU
@app.route('/add-menu', methods=['POST'])
def add_menu():
    try:
        data = request.json

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO menu (day, meal_type, item_name, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s)
        """, (
            data['day'].lower(),
            data['meal_type'].lower(),
            data['item_name'],
            data.get('start_time', '12:00 PM'),
            data.get('end_time', '02:00 PM')
        ))

        conn.commit()
        conn.close()

        return jsonify({"message": "Item added"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ❌ DELETE MENU
@app.route('/delete-menu/<int:id>', methods=['DELETE'])
def delete_menu(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM menu WHERE id=%s", (id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Deleted"})


# 📝 COMPLAINT
@app.route('/complaint', methods=['POST'])
def complaint():
    try:
        data = request.json
        text = data.get('complaint')

        if not text:
            return jsonify({"error": "Empty complaint"}), 400

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO complaints (text) VALUES (%s)", (text,))
        conn.commit()
        conn.close()

        return jsonify({"message": "Complaint saved"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 📋 GET COMPLAINTS
@app.route('/complaints')
def get_complaints():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM complaints ORDER BY created_at DESC")
    data = cursor.fetchall()

    conn.close()
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)