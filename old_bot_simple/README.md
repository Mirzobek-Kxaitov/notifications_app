# OLX Bot - TO'LIQ VERSIYA

Telegram kanalga OLX.uz dan kvartira e'lonlarini to'liq ma'lumot bilan yuboradi.

## Xususiyatlar

### ✅ TO'LIQ MA'LUMOT:
- 📸 **5 tagacha rasm** (album formatida)
- 📝 **To'liq tavsif** (400 belgi)
- 📞 **Telefon raqam** (4 strategiya bilan avtomatik topiladi)
- 🏠 **Parametrlar**: xonalar soni, qavat, uy qavatlar soni
- 💰 Narx (dollar va so'm)
- 📍 Manzil va vaqt
- 🔗 OLX'da ko'rish linki

### ✅ TELEFON TOPISH STRATEGIYALARI:
1. "Показать телефон" tugmasini bosish (2 xil XPath)
2. Tel: linklar orqali
3. Sahifa matnidan qidirish
4. Tavsifdan qidirish

### ✅ BOSHQA:
- Markaziy Bank API'dan real dollar kursi
- Environment variables (.env)
- Telegram flood control (15s pauza)
- Fallback - agar Selenium ishlamasa, oddiy usul

## Fayllar

```
old_bot_simple/
├── main.py                    # Asosiy dastur (har 90s parsing + posting)
├── parse_olx_complete.py      # OLX.uz parsing (BeautifulSoup)
├── poster.py                  # Telegram'ga yuborish (TO'LIQ VERSIYA)
├── selenium_parser.py         # Selenium bilan to'liq ma'lumot olish
├── database_setup.py          # SQLite baza yaratish
├── elonlar.db                 # SQLite baza
└── README.md                  # Bu fayl
```

## O'rnatish

### 1. Kutubxonalarni o'rnatish

```bash
pip3 install -r ../requirements.txt
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

## Ishga tushirish

```bash
cd old_bot_simple
python3 main.py
```

Bot har 90 soniyada OLX'ni tekshiradi va yangi e'lonlarni to'liq ma'lumot bilan yuboradi.

## Yangi funksiyalar (2024)

✅ **5 ta rasm** - album formatida yuborish
✅ **Telefon raqam** - avtomatik topish
✅ **To'liq tavsif** - 400 belgi
✅ **Parametrlar** - xonalar, qavat
✅ **Selenium integratsiya** - to'liq ma'lumot olish
✅ **Fallback** - agar Selenium ishlamasa, oddiy usul

## Eski bot bilan farqi

**ESKI:**
- ❌ 1 ta rasm
- ❌ Telefon yo'q
- ❌ Tavsif yo'q
- ❌ Parametrlar yo'q

**YANGI:**
- ✅ 5 ta rasm
- ✅ Telefon bor
- ✅ To'liq tavsif
- ✅ Xonalar, qavat
