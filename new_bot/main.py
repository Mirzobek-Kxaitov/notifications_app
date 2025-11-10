#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OLX E'lonlar Bot - To'liq versiya
Telegram superguruh Topic LONG ga yuboradi
Rasmlar + Tavsif + Telefon + Parametrlar
"""

import time
import asyncio
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import re
from telegram import Bot, InputMediaPhoto
from selenium_parser import get_ad_details

# BOT sozlamalari
BOT_TOKEN = "8507503693:AAG2MM5D5IWyyJOV-8tqZhstF4Lg1289EUE"
SUPERGROUP_ID = "-1003009529649"
TOPIC_LONG = 4  # Faqat LONG topic ishlatamiz
FALLBACK_RATE = 12800

# Baza
DB_NAME = "new_bot_ads.db"

def init_database():
    """Bazani yaratish"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price TEXT,
            url TEXT UNIQUE NOT NULL,
            image_url TEXT,
            is_posted_to_telegram INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Test baza tayyor")

def parse_olx_ads():
    """OLX dan yangi e'lonlarni parsing qilish"""

    url = "https://www.olx.uz/nedvizhimost/kvartiry/arenda-dolgosrochnaya/tashkent/?currency=UZS&search%5Bfilter_enum_comission%5D%5B0%5D=no"

    print(f"\n📡 OLX dan e'lonlar yuklanmoqda...")

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('div', {'data-cy': 'l-card'})

        print(f"✅ {len(cards)} ta e'lon topildi")

        new_ads_count = 0
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        for card in cards:
            # Manzil va vaqt
            location_tag = card.find('p', {'data-testid': 'location-date'})
            if not location_tag:
                continue

            location_date = location_tag.get_text(strip=True)

            # Faqat bugungi e'lonlar
            if "Сегодня" not in location_date and "сегодня" not in location_date.lower():
                continue

            # Vaqtni ajratish
            time_match = re.search(r'(\d{1,2}):(\d{2})', location_date)
            if not time_match:
                continue

            ad_hour = int(time_match.group(1))
            ad_minute = int(time_match.group(2))

            # Oxirgi 6 soat
            time_diff_minutes = (current_hour * 60 + current_minute) - (ad_hour * 60 + ad_minute)
            if time_diff_minutes < 0 or time_diff_minutes > 360:
                continue

            # URL
            link_tag = card.find('a', href=True)
            if not link_tag or not link_tag['href']:
                continue

            link = "https://www.olx.uz" + link_tag['href']

            # Bazada mavjudligini tekshirish
            cursor.execute('SELECT id FROM ads WHERE url = ?', (link,))
            if cursor.fetchone():
                continue

            # Sarlavha
            title = "Topilmadi"
            title_tag = card.find('h6', class_='css-16v5mdi')
            if not title_tag:
                title_tag = card.find(['h6', 'h5', 'h4', 'h3'])
            if title_tag:
                title = title_tag.get_text(strip=True)

            # Narx
            price_tag = card.find('p', {'data-testid': 'ad-price'})
            price = price_tag.get_text(strip=True) if price_tag else "Topilmadi"

            # Rasm URL
            img_tag = card.find('img')
            image_url = None
            if img_tag:
                img_src = img_tag.get('src', '')
                if img_src and 's=' in img_src:
                    image_url = img_src.replace('s=216x152', 's=1280x960')
                elif img_src:
                    image_url = img_src

            # Bazaga saqlash
            cursor.execute('''
                INSERT INTO ads (title, price, url, image_url, is_posted_to_telegram)
                VALUES (?, ?, ?, ?, 0)
            ''', (title, price + " | " + location_date, link, image_url))

            new_ads_count += 1

        conn.commit()
        conn.close()

        print(f"✅ {new_ads_count} ta yangi e'lon bazaga qo'shildi!")
        return new_ads_count

    except Exception as e:
        print(f"❌ Parsing xatolik: {e}")
        return 0

async def post_to_topics():
    """Topic'larga yuborish"""

    print(f"\n📤 Topic'larga yuborish...")

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Yuborilmagan e'lonlar (yangidan eskiga)
        cursor.execute('''
            SELECT id, title, price, url, image_url
            FROM ads
            WHERE is_posted_to_telegram = 0
            ORDER BY id DESC
        ''')

        ads = cursor.fetchall()

        if not ads:
            print("Yangi e'lonlar yo'q")
            conn.close()
            return

        print(f"{len(ads)} ta yangi e'lon topildi!")

        bot = Bot(token=BOT_TOKEN)
        posted_count = 0

        for ad_id, title, price, url, image_url in ads:
            # Narx va manzilni ajratish
            if " | " in price:
                price_part, location_part = price.split(" | ", 1)
            else:
                price_part = price
                location_part = "Manzil ko'rsatilmagan"

            # Narxni dollarga o'girish
            sum_match = re.search(r'([\d\s]+)\s*сум', price_part)
            if sum_match:
                sum_value = sum_match.group(1).replace(' ', '')
                usd_value = int(sum_value) / FALLBACK_RATE
                if usd_value >= 100:
                    rounded_value = round(usd_value / 10) * 10
                else:
                    rounded_value = round(usd_value / 5) * 5
                price_formatted = f"${rounded_value:,.0f}"
            else:
                price_formatted = price_part

            # Manzil va vaqt
            if " - " in location_part:
                location_only, time_part = location_part.rsplit(" - ", 1)
                location_only = location_only.strip()
                time_part = time_part.strip()

                # UTC+5 ga o'girish
                time_match = re.search(r'(\d{1,2}):(\d{2})', time_part)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    hour = (hour + 5) % 24
                    time_part = re.sub(r'\d{1,2}:\d{2}', f'{hour:02d}:{minute:02d}', time_part)
            else:
                location_only = location_part
                time_part = ""

            print(f"\n📋 E'lon: {title[:50]}...")

            # Selenium bilan to'liq ma'lumot olish
            try:
                print("  🔍 Selenium parsing...")
                details = get_ad_details(url)

                if details and details['images']:
                    images = details['images'][:5]
                    description = details['description']
                    params = details['params']

                    # "ОПИСАНИЕ" ni olib tashlash
                    if description.startswith('ОПИСАНИЕ'):
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

                    # Album
                    media_group = []
                    for idx, img_url in enumerate(images):
                        if idx == 0:
                            caption_text = f"""<b>{title}</b>

{description[:400]}{"..." if len(description) > 400 else ""}

💰 <b>Narxi:</b> {price_formatted}
📍 <b>Manzil:</b> {location_only}
🕐 <b>Vaqt:</b> {time_part}{params_text}

<a href="{url}">🔗 OLX'da ko'rish</a>"""

                            media_group.append(InputMediaPhoto(media=img_url, caption=caption_text, parse_mode='HTML'))
                        else:
                            media_group.append(InputMediaPhoto(media=img_url))

                    # Topic LONG ga yuborish
                    sent_messages = await bot.send_media_group(
                        chat_id=SUPERGROUP_ID,
                        message_thread_id=TOPIC_LONG,
                        media=media_group
                    )

                    long_message_id = sent_messages[0].message_id
                    print(f"  ✅ E'lon yuborildi: Message #{long_message_id} ({len(images)} rasm)")

                    # Bazani yangilash
                    cursor.execute('UPDATE ads SET is_posted_to_telegram = 1 WHERE id = ?', (ad_id,))
                    conn.commit()
                    posted_count += 1

                    print(f"  💤 15 soniya pauza (Telegram flood control uchun)...")
                    # Keyingi e'lon uchun katta pauza
                    await asyncio.sleep(15)

            except Exception as e:
                print(f"  ❌ Xatolik: {e}")
                continue

        conn.close()
        print(f"\n✅ Jami {posted_count} ta e'lon yuborildi!")

    except Exception as e:
        print(f"❌ Posting xatolik: {e}")

def main():
    """Asosiy sikl"""

    print("=" * 60)
    print("🤖 TEST BOT - E'lonlar botи")
    print("🎯 Superguruh Topic LONG ga yuboradi")
    print("📸 Rasmlar + Tavsif + Telefon + Parametrlar")
    print("=" * 60)

    # Bazani yaratish
    init_database()

    while True:
        try:
            print("\n" + "=" * 60)
            print(f"⏰ Iteratsiya: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            # 1. Parsing
            new_count = parse_olx_ads()

            # 2. Topic'larga yuborish
            if new_count > 0:
                asyncio.run(post_to_topics())
            else:
                print("Yangi e'lonlar yo'q")

            # 90 soniya kutish
            print(f"\n⏳ Keyingi tekshirish 90 soniyadan keyin...")
            print("=" * 60)
            time.sleep(90)

        except KeyboardInterrupt:
            print("\n\n❌ Bot to'xtatildi (Ctrl+C)")
            break
        except Exception as e:
            print(f"\n❌ Xatolik: {e}")
            print("⏳ 30 soniyadan keyin qayta urinish...")
            time.sleep(30)

if __name__ == "__main__":
    main()
