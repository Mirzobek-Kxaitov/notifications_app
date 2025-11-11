# -*- coding: utf-8 -*-
import sqlite3
from telegram import Bot, InputMediaPhoto
import asyncio
import requests
import os
import re
from dotenv import load_dotenv
from simple_parser import get_ad_details

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
    """Bazadagi yangi e'lonlarni Telegram kanaliga yuborish - TO'LIQ VERSIYA"""

    try:
        # Ma'lumotlar bazasiga ulanish
        conn = sqlite3.connect('elonlar.db')
        cursor = conn.cursor()

        # Yuborilmagan e'lonlarni olish (ID bo'yicha tartiblash - yangidan eskiga)
        cursor.execute('''
            SELECT id, title, price, url, image_url
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
        for ad_id, title, price, url, image_url in ads:
            print(f"\n{'='*60}")
            print(f"E'lon #{ad_id}: {title[:50]}...")
            print('='*60)
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

            # Selenium bilan to'liq ma'lumot olish
            details = None
            try:
                print("  🔍 Selenium bilan to'liq ma'lumot olinmoqda...")
                details = get_ad_details(url)
            except Exception as selenium_error:
                error_msg = str(selenium_error)
                print(f"  ⚠️ Selenium xatolik: {selenium_error}")

                # Agar 404/410 xatolik bo'lsa - e'lon o'chirilgan, o'tkazib yuboramiz
                if "404" in error_msg or "410" in error_msg or "Not Found" in error_msg:
                    print(f"  🗑️ E'lon OLX'dan o'chirilgan (404/410), o'tkazib yuboriladi...")
                    cursor.execute('UPDATE ads SET is_posted_to_telegram = 1 WHERE id = ?', (ad_id,))
                    conn.commit()
                    print(f"  ✅ E'lon #{ad_id} bazada 'yuborilgan' deb belgilandi")
                    continue

                print("  ℹ️ Oddiy usulda davom etamiz...")
                details = None

            try:
                if details and details['images']:
                    # TO'LIQ VERSIYA - 5 ta rasm, tavsif, telefon, parametrlar
                    images = details['images'][:5]
                    description = details['description']
                    params = details['params']

                    # Tavsifni tozalash - boshidagi va oxiridagi bo'sh joylarni olib tashlash
                    description = description.strip()

                    # Agar birinchi qator faqat "Описание" bo'lsa, olib tashlash
                    if description.startswith('📄 Описание:'):
                        description = description[13:].strip()
                    elif description.startswith('Описание'):
                        description = description[8:].strip()

                    # Parametrlar
                    params_text = ""
                    if params.get('Количество комнат'):
                        params_text += f"\n🏠 <b>Xonalar:</b> {params['Количество комнат']}"
                    if params.get('Этаж'):
                        params_text += f"\n🏢 <b>Qavat:</b> {params['Этаж']}"
                    if params.get('Этажность дома'):
                        params_text += f" / {params['Этажность дома']}"
                    if params.get('Телефон'):
                        params_text += f"\n📞 <b>Telefon:</b> {params['Телефон']}"

                    # Album yaratish
                    media_group = []
                    for idx, img_url in enumerate(images):
                        if idx == 0:
                            # Birinchi rasmga to'liq caption
                            caption_text = f"""<b>{title}</b>

{description[:400]}{"..." if len(description) > 400 else ""}

💰 <b>Narxi:</b> {price_formatted}
📍 <b>Manzil:</b> {location_only}
🕐 <b>Vaqt:</b> {time_part}{params_text}

<a href="{url}">🔗 OLX'da ko'rish</a>"""

                            media_group.append(InputMediaPhoto(media=img_url, caption=caption_text, parse_mode='HTML'))
                        else:
                            media_group.append(InputMediaPhoto(media=img_url))

                    # Kanalga album yuborish
                    print(f"  📤 Kanalga {len(images)} ta rasm bilan yuborilmoqda...")
                    await bot.send_media_group(
                        chat_id=CHANNEL_ID,
                        media=media_group
                    )

                    print(f"  ✅ E'lon yuborildi! ({len(images)} ta rasm)")

                    # Bazada yuborilganligini belgilash
                    cursor.execute('UPDATE ads SET is_posted_to_telegram = 1 WHERE id = ?', (ad_id,))
                    conn.commit()
                    posted_count += 1

                    # Telegram flood control uchun katta pauza
                    print(f"  💤 15 soniya pauza (Telegram flood control)...")
                    await asyncio.sleep(15)

                else:
                    # Agar Selenium ishlamasa - eski usul (1 ta rasm)
                    print("  ⚠️ Selenium ma'lumot bermadi, oddiy usul ishlatiladi...")

                    # Agar image_url ham bo'sh bo'lsa - bu e'lon noto'g'ri, o'tkazib yuboramiz
                    if not image_url or not image_url.strip():
                        print("  🗑️ E'londa rasm yo'q va parser ishlamadi, o'tkazib yuboriladi...")
                        cursor.execute('UPDATE ads SET is_posted_to_telegram = 1 WHERE id = ?', (ad_id,))
                        conn.commit()
                        print(f"  ✅ E'lon #{ad_id} bazada 'yuborilgan' deb belgilandi")
                        continue

                    message_text = f"""<b>{title}</b>

💰 <b>Narxi:</b> {price_formatted}
📍 <b>Manzil:</b> {location_only}
🕐 <b>Vaqt:</b> {time_part}

<a href="{url}">👉 Batafsil ko'rish</a>"""

                    if image_url:
                        await bot.send_photo(
                            chat_id=CHANNEL_ID,
                            photo=image_url,
                            caption=message_text,
                            parse_mode='HTML'
                        )
                    else:
                        await bot.send_message(
                            chat_id=CHANNEL_ID,
                            text=message_text,
                            parse_mode='HTML',
                            disable_web_page_preview=True
                        )

                    cursor.execute('UPDATE ads SET is_posted_to_telegram = 1 WHERE id = ?', (ad_id,))
                    conn.commit()
                    posted_count += 1

                    await asyncio.sleep(2)

            except Exception as e:
                print(f"  ❌ E'lonni yuborishda xatolik: {e}")
                # Agar flood control xatolik bo'lsa, 40 soniya kutamiz
                if "Flood control" in str(e) or "Too Many Requests" in str(e):
                    print("  ⏳ Telegram limitiga yetdi, 40 soniya kutilmoqda...")
                    await asyncio.sleep(40)
                continue

        conn.close()

        print(f"\nKanalga {posted_count} ta yangi e'lon muvaffaqiyatli yuborildi!")

    except sqlite3.Error as e:
        print(f"Ma'lumotlar bazasi xatolik: {e}")
    except Exception as e:
        print(f"Xatolik: {e}")

if __name__ == "__main__":
    asyncio.run(post_ads_to_telegram())
