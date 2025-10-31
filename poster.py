# -*- coding: utf-8 -*-
import sqlite3
from telegram import Bot
import asyncio
import requests
import os
import re
from dotenv import load_dotenv

# .env fayldan o'qish
load_dotenv()

# Sozlamalar
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
FALLBACK_RATE = int(os.getenv("FALLBACK_RATE", 12800))  # Zaxira kurs (agar API ishlamasa)

def get_usd_rate_from_api():
    """Markaziy Bank API'sidan USD kursini oladi."""
    try:
        # Ulanish uchun vaqt chegarasini belgilash (10 soniya)
        response = requests.get("https://cbu.uz/oz/arkhiv-kursov-valyut/json/", timeout=10)
        response.raise_for_status() # Agar status kod 200 bo'lmasa xatolik beradi
        currencies = response.json()
        for currency in currencies:
            if currency['Ccy'] == 'USD':
                rate = float(currency['Rate'])
                print(f"✅ Markaziy Bankdan kurs olindi: {rate}")
                return rate
        print("API javobidan USD topilmadi. Zaxira kurs ishlatiladi.")
        return FALLBACK_RATE
    except Exception as e:
        print(f"❌ Markaziy Bank API'sidan kursni olib bo'lmadi: {e}")
        return FALLBACK_RATE

async def post_ads_to_telegram():
    """Bazadagi yangi e'lonlarni Telegram kanaliga yuborish"""

    try:
        # Ma'lumotlar bazasiga ulanish
        conn = sqlite3.connect('elonlar.db')
        cursor = conn.cursor()

        # Yuborilmagan e'lonlarni olish (ID bo'yicha tartiblash - yangidan eskiga)
        cursor.execute('''
            SELECT id, title, price, url
            FROM ads
            WHERE is_posted_to_telegram = 0
            ORDER BY id DESC
        ''')

        ads = cursor.fetchall()

        if not ads:
            print("Yangi e'lonlar topilmadi.")
            conn.close()
            return

        print(f"Jami {len(ads)} ta yangi e'lon topildi!")
        print(f"Kanalga yuborilmoqda...\n")

        # Markaziy Bankdan dollar kursini olish
        usd_rate = get_usd_rate_from_api()

        # Bot obyektini yaratish
        bot = Bot(token=BOT_TOKEN)

        posted_count = 0

        # Har bir e'lonni kanalga yuborish
        for ad_id, title, price, url in ads:
            # Narx va manzilni ajratish (price da "narx | manzil" formatida saqlangan)
            if " | " in price:
                price_part, location_part = price.split(" | ", 1)
            else:
                price_part = price
                location_part = "Manzil ko'rsatilmagan"

            # Narxni formatlash - so'mni dollarga o'girish
            price_clean = price_part.strip()

            # "сум" va raqamlarni ajratish
            sum_match = re.search(r'([\d\s]+)\s*сум', price_clean)
            if sum_match:
                sum_value = sum_match.group(1).replace(' ', '')
                try:
                    # So'mni dollarga o'girish (Markaziy Bank kursidan foydalanish)
                    usd_value = int(sum_value) / usd_rate

                    # Narxni yaxlitlash - aniq summalarni ko'rsatish
                    if usd_value >= 100:
                        # 100 dan katta bo'lsa, eng yaqin 10 ga yaxlitlash
                        # Masalan: 651 -> 650, 1203 -> 1200, 281 -> 280
                        rounded_value = round(usd_value / 10) * 10
                    else:
                        # 100 dan kichik bo'lsa, eng yaqin 5 ga yaxlitlash
                        rounded_value = round(usd_value / 5) * 5

                    price_formatted = f"${rounded_value:,.0f}"

                    # "Договорная" qo'shish
                    if "Договорная" in price_clean or "Договорная" in price_part:
                        price_formatted += " (Kelishiladi)"
                except:
                    price_formatted = price_clean
            else:
                price_formatted = price_clean

            # Manzil va vaqtni ajratish
            location_clean = location_part.strip()
            time_part = ""

            # Vaqtni topish (masalan: "Сегодня в 06:30", "01 октября 2025 г.")
            if " - " in location_clean:
                location_only, time_part = location_clean.rsplit(" - ", 1)
                location_only = location_only.strip()
                time_part = time_part.strip()

                # OLX saytidan UTC vaqti keladi, O'zbekiston vaqtiga (UTC+5) o'girish
                time_match = re.search(r'(\d{1,2}):(\d{2})', time_part)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))

                    # +5 soat qo'shish
                    hour = (hour + 5) % 24

                    # Vaqtni yangi formatda almashtirish
                    time_part = re.sub(r'\d{1,2}:\d{2}', f'{hour:02d}:{minute:02d}', time_part)
            else:
                location_only = location_clean
                time_part = ""

            # Xabar matnini tayyorlash (HTML format)
            message_text = f"""<b>{title}</b>

💰 <b>Narxi:</b> {price_formatted}
📍 <b>Manzil:</b> {location_only}"""

            if time_part:
                message_text += f"\n🕐 <b>E'lon qo'yilgan vaqt:</b> {time_part}"

            message_text += f"""

<a href="{url}">👉 Batafsil ko'rish</a>"""

            try:
                # Kanalga xabar yuborish
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=message_text,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )

                # Bazada yuborilganligini belgilash
                cursor.execute('''
                    UPDATE ads
                    SET is_posted_to_telegram = 1
                    WHERE id = ?
                ''', (ad_id,))

                conn.commit()
                posted_count += 1

                print(f"E'lon #{posted_count} yuborildi: {title[:50]}...")

                # Telegram limitidan qochish uchun pauza (2 soniya)
                await asyncio.sleep(2)

            except Exception as e:
                print(f"E'lonni yuborishda xatolik (ID: {ad_id}): {e}")
                # Agar flood control xatolik bo'lsa, 40 soniya kutamiz
                if "Flood control" in str(e):
                    print("Telegram limitiga yetdi, 40 soniya kutilmoqda...")
                    await asyncio.sleep(40)

        conn.close()

        print(f"\nKanalga {posted_count} ta yangi e'lon muvaffaqiyatli yuborildi!")

    except sqlite3.Error as e:
        print(f"Ma'lumotlar bazasi xatolik: {e}")
    except Exception as e:
        print(f"Xatolik: {e}")

if __name__ == "__main__":
    asyncio.run(post_ads_to_telegram())
