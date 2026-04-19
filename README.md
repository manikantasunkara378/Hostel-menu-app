# 🍽️ Smart Hostel Menu Management System

A full-stack web application to manage and display hostel food menus dynamically with real-time availability and a complaint system.

---

## 🚀 Features

* 📅 **Day-wise Menu Display** (Breakfast, Lunch, Snacks, Dinner)
* ⏱️ **Time-based Availability** (Shows only currently available items)
* 🎯 **Dynamic API Integration** (Flask + MySQL)
* 🧑‍💼 **Admin Operations**

  * Add menu items
  * Delete menu items
* 📝 **Complaint System**

  * Students can report food quality issues
  * Stored in database for admin review
* 🎨 **Animated UI**

  * Smooth card animations
  * Responsive layout

---

## 🧱 Tech Stack

| Layer    | Technology            |
| -------- | --------------------- |
| Frontend | HTML, CSS, JavaScript |
| Backend  | Python (Flask)        |
| Database | MySQL                 |
| API      | REST API              |

---

## 📁 Project Structure

```
hostel-menu-app/
│
├── backend/
│   ├── app.py
│   ├── db.py
│   ├── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   ├── js/app.js
│
├── database.sql
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```
git clone https://github.com/your-username/hostel-menu-app.git
cd hostel-menu-app
```

---

### 2️⃣ Setup Backend

```
cd backend
pip install -r requirements.txt
```

---

### 3️⃣ Configure Database

* Open MySQL
* Run:

```
SOURCE database.sql;
```

* Update credentials in `db.py`:

```python
host="localhost"
user="root"
password="YOUR_PASSWORD"
database="hostel_menu"
```

---

### 4️⃣ Run Backend

```
python app.py
```

Server runs on:

```
http://127.0.0.1:5000
```

---

### 5️⃣ Run Frontend

* Open:

```
frontend/index.html
```

OR use Live Server (VS Code)

---

## 🔗 API Endpoints

### 📌 Get Menu

```
GET /menu?type=Lunch
```

### 📌 Add Menu

```
POST /add-menu
```

### 📌 Delete Menu

```
DELETE /delete-menu/<id>
```

### 📌 Submit Complaint

```
POST /complaint
```

### 📌 Get Complaints

```
GET /complaints
```

---

## 🧪 Example API Response

```json
[
  {
    "item_name": "Chapathi",
    "start_time": "12:00:00",
    "end_time": "14:00:00"
  }
]
```

---

## 🧠 Key Learnings

* Handling **full-stack integration**
* Solving **CORS and API issues**
* Managing **real-time data rendering**
* Fixing **JSON serialization bugs**
* Designing **scalable database schema**

---

## 🔥 Future Enhancements

* 🔐 Authentication system (Admin login)
* ⭐ Food rating system
* 📊 Analytics dashboard
* 🤖 AI-based menu recommendation
* 📱 Mobile app version

---

## 💬 Author

**Mani Kanta**
ECE (AIML) Student

---

## ⭐ If you like this project

Give it a ⭐ on GitHub and share it 🚀
