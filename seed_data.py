from app import create_app
from db import db, Menu
from datetime import time

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    def add(day, meal, items, start, end):
        for item in items:
            db.session.add(Menu(
                day=day.lower(),
                meal_type=meal.lower(),
                item_name=item,
                start_time=start,
                end_time=end
            ))

    # ================= BREAKFAST =================
    add("monday","breakfast",[
        "Bread & Omelet","Veg Upma","Coconut Chutney","Milk & Coffee","Tomato Ketchup"
    ], time(7,0), time(9,0))

    add("tuesday","breakfast",[
        "Idly","Ven Pongal","Medhu Vada","Coconut Chutney","Pumpkin Sambar","Milk & Coffee"
    ], time(7,0), time(9,0))

    add("wednesday","breakfast",[
        "Masala Dosa","Semiya Khichadi","Onion Sambar","Peanut Chutney","Bread & Jam","Milk & Coffee"
    ], time(7,0), time(9,0))

    add("thursday","breakfast",[
        "Maggi","Mysore Bonda","Red Chutney","Cornflakes","Milk","Coffee"
    ], time(7,0), time(9,0))

    add("friday","breakfast",[
        "Pesarattu","Allam Pachadi","Rava Upma","Sambar","Coconut Chutney","Bread & Jam"
    ], time(7,0), time(9,0))

    add("saturday","breakfast",[
        "Karam Dosa","Chutney","Sambar","White Sauce Pasta","Cornflakes","Milk & Coffee"
    ], time(7,0), time(9,0))

    add("sunday","breakfast",[
        "Poori","Channa Masala","Bread & Jam","Coffee","Milk"
    ], time(7,0), time(9,0))

    # ================= SNACKS =================
    snacks = [
        ("monday","Bun"),
        ("tuesday","Curry Puff"),
        ("wednesday","Mixture"),
        ("thursday","Ghee Biscuits"),
        ("friday","Cake"),
        ("saturday","Boiled Groundnut"),
        ("sunday","Sweetcorn"),
    ]

    for d, item in snacks:
        add(d,"snacks",[item], time(17,0), time(18,0))

    # ================= LUNCH =================
    add("monday","lunch",[
        "Chapathi","Palak Paneer","White Rice","Sambar","Potato Fry",
        "Tomato Dal","Payasam","Rasam","Chutney","Buttermilk","Fryums"
    ], time(12,0), time(14,0))

    add("tuesday","lunch",[
        "Chapathi","Green Peas Masala","White Rice","Veg Sambar",
        "Spinach Dal","Banana Fry","Egg Omelet","Rasam","Gongura",
        "Curd","Appalam"
    ], time(12,0), time(14,0))

    add("wednesday","lunch",[
        "Roti","Veg Salna","White Rice","Dal","Sambar","Beans Fry",
        "Egg Masala","Rasam","Thoviyal","Buttermilk","Onion Rings"
    ], time(12,0), time(14,0))

    add("thursday","lunch",[
        "Chapathi","Veg Gravy","White Rice","Dal","Brinjal Curry",
        "Fry","Egg Podimas","Rasam","Coconut","Buttermilk","Fryums"
    ], time(12,0), time(14,0))

    add("friday","lunch",[
        "Chapathi","Rajma","White Rice","Dal","Sambar","Brinjal Fry",
        "Egg Omelette","Rasam","Chutney","Buttermilk","Appalam"
    ], time(12,0), time(14,0))

    add("saturday","lunch",[
        "Chapathi","Veg Kadai","Bisi Bele Bath","Curd Rice","White Rice",
        "Rasam","Yam Fry","Vada","Pickle","Sweet","Curd Chilli"
    ], time(12,0), time(14,0))

    add("sunday","lunch",[
        "Chapathi","Gobi Kurma","White Rice","Dal","Sambar",
        "Beetroot Fry","Egg Curry","Rasam","Mint Chutney",
        "Cool Drink","Fryums"
    ], time(12,0), time(14,0))

    # ================= DINNER =================
    add("monday","dinner",[
        "Dosa","Egg Kurma","Paneer Curry","Pulav","Rice",
        "Curd","Banana","Raitha","Milk"
    ], time(19,0), time(20,30))

    add("tuesday","dinner",[
        "Chicken Curry","Chicken Kulambu","Fry","Roti",
        "Ghee Rice","Rice","Sambar","Curd","Sweet","Milk"
    ], time(19,0), time(20,30))

    add("wednesday","dinner",[
        "Chicken Biryani","Salna","Veg Biryani","Chapathi",
        "Pepper Masala","Raitha","Rice","Rasam","Curd","Sweet","Milk"
    ], time(19,0), time(20,30))

    add("thursday","dinner",[
        "Chicken Masala","Kurma","Corn Fry","Roti",
        "Pulav","Rice","Sambar","Curd","Sweet","Milk"
    ], time(19,0), time(20,30))

    add("friday","dinner",[
        "Fried Rice","Chicken Gravy","Mushroom Rice","Chapathi",
        "Rajma","Sauce","Rice","Rasam","Curd","Sweet","Milk"
    ], time(19,0), time(20,30))

    add("saturday","dinner",[
        "Pulihora","Veg Curry","Vada","Roti","Dal",
        "Rice","Cabbage Fry","Rasam","Curd","Sweet","Milk"
    ], time(19,0), time(20,30))

    add("sunday","dinner",[
        "Chicken Curry","Dosa","Chutney","Rice","Sambar",
        "Curd","Fruits","Milk"
    ], time(19,0), time(20,30))

    db.session.commit()
    print("🔥 FULL MENU INSERTED SUCCESSFULLY")