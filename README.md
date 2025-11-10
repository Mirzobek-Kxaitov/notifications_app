# OLX E'lonlar Telegram Botlari

OLX.uz dan kvartira e'lonlarini avtomatik Telegram'ga yuboradigan botlar.

## Loyihalar

### 📦 **new_bot** - To'liq versiya (Yangi, tavsiya etiladi)

**Xususiyatlar:**
- ✅ 5 tagacha rasm (album)
- ✅ To'liq tavsif (400 belgi)
- ✅ **Telefon raqam** (avtomatik topiladi)
- ✅ Parametrlar (xonalar, qavat)
- ✅ Narx, manzil, vaqt
- ✅ Superguruh Topic'ga yuborish

**Ishga tushirish:**
```bash
cd new_bot
python3 main.py
```

📄 [To'liq dokumentatsiya](new_bot/README.md)

---

### 📦 **old_bot_simple** - Oddiy versiya (Eski)

**Xususiyatlar:**
- ✅ 1 ta rasm
- ✅ Asosiy ma'lumot (title, price, manzil)
- ✅ Kanalga yuborish
- ❌ Telefon yo'q
- ❌ Parametrlar yo'q

**Ishga tushirish:**
```bash
cd old_bot_simple
python3 main.py
```

📄 [Dokumentatsiya](old_bot_simple/README.md)

---

## Struktura

```
notifications_app/
├── new_bot/              # Yangi to'liq bot
│   ├── main.py           # Asosiy dastur
│   ├── selenium_parser.py # Selenium parsing
│   ├── quick_test.py     # Tezkor test
│   └── new_bot_ads.db    # Baza (avtomatik yaratiladi)
│
├── old_bot_simple/       # Eski oddiy bot
│   ├── main.py           # Asosiy dastur
│   ├── parse_olx_complete.py
│   ├── poster.py
│   └── elonlar.db
│
└── requirements.txt      # Umumiy kerakli kutubxonalar
```

## O'rnatish

```bash
# Kutubxonalarni o'rnatish
pip3 install -r requirements.txt

# ChromeDriver kerak (Selenium uchun)
# macOS: brew install chromedriver
# Linux: apt-get install chromium-chromedriver
```

## Farqi

| Xususiyat | old_bot_simple | new_bot |
|-----------|----------------|---------|
| Rasmlar | 1 ta | 5 tagacha |
| Tavsif | ❌ | ✅ |
| Telefon | ❌ | ✅ (4 strategiya) |
| Parametrlar | ❌ | ✅ (xonalar, qavat) |
| Yuborish joyi | Kanal | Superguruh Topic |
| Parsing | BeautifulSoup | BeautifulSoup + Selenium |
| Baza | elonlar.db | new_bot_ads.db |

## Qaysi birini ishlatish kerak?

- **Tezlik muhim, oddiy ma'lumot yetarli** → `old_bot_simple`
- **To'liq ma'lumot kerak (telefon, rasmlar, parametrlar)** → `new_bot` ✅

## Muallif

Mirzobek

## Litsenziya

MIT
