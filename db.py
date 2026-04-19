import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="VTU28789@mani",
        database="hostel_menu"
    )