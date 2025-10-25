import sqlite3

def create_database():
    """E'lonlar uchun ma'lumotlar bazasi va jadvalini yaratish"""

    # Ma'lumotlar bazasiga ulanish (fayl yo'q bo'lsa avtomatik yaratiladi)
    conn = sqlite3.connect('elonlar.db')
    cursor = conn.cursor()

    # Jadval yaratish (agar mavjud bo'lsa, qayta yaratmaydi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price TEXT,
            url TEXT UNIQUE NOT NULL,
            is_posted_to_telegram INTEGER DEFAULT 0
        )
    ''')

    # O'zgarishlarni saqlash
    conn.commit()

    print("✅ Ma'lumotlar bazasi muvaffaqiyatli yaratildi!")
    print(f"📁 Fayl: elonlar.db")
    print(f"📊 Jadval: ads")
    print(f"   - id (PRIMARY KEY, AUTOINCREMENT)")
    print(f"   - title (TEXT)")
    print(f"   - price (TEXT)")
    print(f"   - url (TEXT, UNIQUE)")
    print(f"   - is_posted_to_telegram (INTEGER, DEFAULT 0)")

    # Ulanishni yopish
    conn.close()

if __name__ == "__main__":
    create_database()
