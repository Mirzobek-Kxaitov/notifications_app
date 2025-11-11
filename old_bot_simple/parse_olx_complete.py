import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import re

def parse_all_ads():
    """OLX.uz dan barcha e'lonlarni ajratib olish va bazaga saqlash"""

    # Toshkent shahridagi uzoq muddatli ijaraga beriladigan kvartiralar (so'mda)
    url = "https://www.olx.uz/nedvizhimost/kvartiry/arenda-dolgosrochnaya/tashkent/?currency=UZS&search%5Bfilter_enum_comission%5D%5B0%5D=no"

    print(f"📥 Sahifa yuklanmoqda: {url}\n")

    try:
        # Connect to db
        conn = sqlite3.connect('elonlar.db')
        cursor = conn.cursor()

        #Load to page
        response = requests.get(url)
        response.raise_for_status()

        # HTML parsing
        soup = BeautifulSoup(response.text, 'html.parser')

        # Barcha e'lon kartalarini topish
        cards = soup.find_all('div', {'data-cy': 'l-card'})

        if not cards:
            print("❌ E'lon kartalari topilmadi!")
            conn.close()
            return

        print(f"✅ Jami {len(cards)} ta e'lon topildi!")
        print(f"📊 Bazaga yangi e'lonlar tekshirilmoqda...\n")

        new_ads_count = 0

        # Hozirgi vaqt
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        # E'lonlarni vaqt bilan saqlash (vaqt bo'yicha tartiblash uchun)
        ads_with_time = []

        # Har bir karta uchun ma'lumotlarni ajratib olish
        for card in cards:
            # Manzil va Sana (avval tekshirish uchun)
            location_tag = card.find('p', {'data-testid': 'location-date'})
            if not location_tag:
                continue

            location_date = location_tag.get_text(strip=True)

            # Faqat bugungi e'lonlarni olish
            if "Сегодня" not in location_date and "сегодня" not in location_date.lower():
                continue

            # Soatni ajratib olish (masalan: "Toshkent, Yashnobod tumani - Сегодня 13:55")
            time_match = re.search(r'(\d{1,2}):(\d{2})', location_date)
            if not time_match:
                continue

            ad_hour = int(time_match.group(1))
            ad_minute = int(time_match.group(2))

            # Faqat oxirgi 2 soat ichidagi e'lonlarni olish
            time_diff_minutes = (current_hour * 60 + current_minute) - (ad_hour * 60 + ad_minute)

            if time_diff_minutes < 0 or time_diff_minutes > 120:
                continue  # 2 soatdan eski yoki kelajakdagi e'lon

            # Havola
            link_tag = card.find('a', href=True)
            if link_tag and link_tag['href']:
                link = "https://www.olx.uz" + link_tag['href']
            else:
                continue  # Havola bo'lmasa, keyingi e'longa o'tamiz

            # Bazada bu havola mavjudmi tekshirish
            cursor.execute('SELECT id FROM ads WHERE url = ?', (link,))
            existing = cursor.fetchone()

            if existing:
                # Havola mavjud, keyingisiga o'tamiz
                continue

            # Sarlavha
            title = "Topilmadi"
            title_tag = card.find('h6', class_='css-16v5mdi')
            if not title_tag:
                title_tag = card.find('h4')
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
                # Kichik rasmni kattasiga o'zgartirish (s=216x152 -> s=1280x960)
                img_src = img_tag.get('src', '')
                if img_src and 's=' in img_src:
                    image_url = img_src.replace('s=216x152', 's=1280x960')
                elif img_src:
                    image_url = img_src

            # E'lonni vaqt bilan ro'yxatga qo'shish
            ads_with_time.append({
                'title': title,
                'price': price,
                'location_date': location_date,
                'link': link,
                'image_url': image_url,
                'ad_time': ad_hour * 60 + ad_minute  # Daqiqalarda vaqt
            })

        # E'lonlarni vaqt bo'yicha tartiblash (eskidan yangiga)
        ads_with_time.sort(key=lambda x: x['ad_time'])

        # Endi bazaga tartibda qo'shish
        for ad in ads_with_time:
            cursor.execute('''
                INSERT INTO ads (title, price, url, image_url, is_posted_to_telegram)
                VALUES (?, ?, ?, ?, 0)
            ''', (ad['title'], ad['price'] + " | " + ad['location_date'], ad['link'], ad['image_url']))
            new_ads_count += 1

        # O'zgarishlarni saqlash
        conn.commit()
        conn.close()

        print(f"✅ Bazaga {new_ads_count} ta yangi e'lon qo'shildi (vaqt bo'yicha tartiblangan)!")

    except requests.exceptions.RequestException as e:
        print(f"❌ Tarmoq xatolik: {e}")
    except sqlite3.Error as e:
        print(f"❌ Ma'lumotlar bazasi xatolik: {e}")
    except Exception as e:
        print(f"❌ Xatolik: {e}")

if __name__ == "__main__":
    parse_all_ads()
