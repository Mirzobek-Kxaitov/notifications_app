# OLX E'lonlar Bot - To'liq versiya

Telegram superguruh Topic LONG ga OLX.uz dan kvartira e'lonlarini yuboradi.

## Xususiyatlar

✅ **To'liq ma'lumot bir joyda:**
- 5 tagacha rasm (album)
- Tavsif (400 belgi)
- Narx va manzil
- Xonalar soni
- Qavat / Uy qavatlar soni
- **Telefon raqam** (avtomatik topiladi)
- OLX'da ko'rish linki

✅ **Telefon raqam topish:**
- "Показать телефон" tugmasini bosish (2 xil XPath)
- Tel: linklar orqali
- Sahifa matnidan qidirish
- Tavsifdan qidirish

## Fayllar

```
new_bot/
├── main.py              # Asosiy bot
├── selenium_parser.py   # Selenium bilan parsing
├── new_bot_ads.db       # SQLite baza (avtomatik yaratiladi)
└── README.md           # Bu fayl
```

## Ishga tushirish

### Local'da test qilish

```bash
cd new_bot
python3 main.py
```

Bot har 90 soniyada OLX'ni tekshiradi va yangi e'lonlarni yuboradi.

### To'xtatish

```bash
# Ctrl+C yoki:
pkill -f "python3 main.py"
```

## Sozlamalar

`main.py` faylidagi o'zgaruvchilar:

```python
BOT_TOKEN = "..."           # Bot token
SUPERGROUP_ID = "..."       # Superguruh ID
TOPIC_LONG = 4             # Topic ID
```

## O'rnatish

### 1. Kutubxonalarni o'rnatish

```bash
pip3 install -r requirements.txt
```

### 2. ChromeDriver o'rnatish (Selenium uchun)

**macOS:**
```bash
brew install chromedriver
```

**Linux:**
```bash
sudo apt-get install chromium-chromedriver
```

**Windows:**
[ChromeDriver yuklab olish](https://chromedriver.chromium.org/)

## Ishlash prinsipi

1. OLX.uz dan yangi e'lonlarni parsing (BeautifulSoup)
2. Har bir yangi e'lon uchun:
   - Selenium bilan to'liq ma'lumot olish
   - Telefon raqam topish (4 strategiya)
   - Telegram'ga yuborish (Topic LONG)
3. Bazada belgilash (takror yuborilmasligi uchun)
4. 90 soniya kutish va qaytadan

## Eski bot bilan farqi

**Eski bot** (`parse_olx_complete.py` + `poster.py`):
- Faqat asosiy ma'lumot (1 rasm, title, price)
- Telefon yo'q
- Kanalga yuboradi

**Yangi bot** (`new_bot/main.py`):
- To'liq ma'lumot (rasmlar, tavsif, parametrlar)
- Telefon raqam bor
- Superguruh Topic'ga yuboradi
- Alohida papkada (aralashib ketmaydi)
