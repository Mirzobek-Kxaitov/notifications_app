#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E'lon sahifasidan rasmlar va tavsifni olish - Requests + BeautifulSoup bilan
"""

import requests
from bs4 import BeautifulSoup
import re

def get_ad_details(url):
    """E'lon sahifasidan rasmlar va tavsifni olish"""

    print(f"\n{'='*80}")
    print(f"URL: {url}")
    print('='*80)

    try:
        # Sahifani yuklash
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. Barcha rasmlarni olish
        print("\n📸 RASMLAR:")
        print("-" * 80)

        images = []

        # JSON-LD dan rasmlarni olish
        script_tags = soup.find_all('script', {'type': 'application/ld+json'})
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                if 'image' in data:
                    img_data = data['image']
                    if isinstance(img_data, list):
                        for img in img_data[:5]:
                            if img not in images:
                                images.append(img)
                                print(f"{len(images)}. {img[:80]}...")
                    elif isinstance(img_data, str):
                        if img_data not in images:
                            images.append(img_data)
                            print(f"{len(images)}. {img_data[:80]}...")
            except:
                pass

        # Agar JSON-LD dan topilmasa, img teglardan olish
        if not images:
            img_elements = soup.find_all('img', {'src': re.compile(r'apollo\.olxcdn\.com.*image')})
            for img in img_elements[:10]:
                src = img.get('src', '')
                if src and 'image' in src:
                    # Katta formatga o'zgartirish
                    if 's=' in src:
                        src = src.replace('s=120x90', 's=1280x960')
                        src = src.replace('s=216x152', 's=1280x960')
                        src = src.replace('s=644x461', 's=1280x960')

                    if src not in images:
                        images.append(src)
                        print(f"{len(images)}. {src[:80]}...")

        print(f"\nJami topilgan rasmlar: {len(images)}")

        # 2. Tavsifni olish va formatlash
        print("\n📝 TAVSIF:")
        print("-" * 80)

        description = ""

        # data-cy="ad_description" dan olish
        desc_elem = soup.find(attrs={'data-cy': 'ad_description'})
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        else:
            # Agar topilmasa, boshqa usullar bilan
            desc_divs = soup.find_all('div', class_=re.compile(r'description|content'))
            for div in desc_divs:
                text = div.get_text(strip=True)
                if len(text) > 50:
                    description = text
                    break

        if description:
            # Tavsifni formatlash - qatorma-qator
            # "Описание" dan keyin kelgan ma'lumotlarni ajratish
            description = description.replace('Описание1', '\n📄 Описание:\n1')
            description = description.replace('Описание', '\n📄 Описание:')
            description = description.replace('Комнат:', '\n🏠 Комнат:')
            description = description.replace('Этаж:', '\n🏢 Этаж:')
            description = description.replace('Этажность:', '\n🏗️ Этажность:')
            description = description.replace('Площадь:', '\n📐 Площадь:')
            description = description.replace('Балкон:', '\n🪟 Балкон:')
            description = description.replace('Состояние:', '\n✨ Состояние:')
            description = description.replace('Цена аренды:', '\n💰 Цена аренды:')

            # Katta harflar orasiga bo'sh joy qo'shish (masalan: "JangoxQozogiston" -> "Jangox Qozogiston")
            # Agar katta harf boshqa katta harfdan keyin kelsa, bo'sh joy qo'shamiz
            description = re.sub(r'([а-яёА-ЯЁa-zA-Z])([А-ЯЁA-Z][а-яёa-z])', r'\1 \2', description)

            # "—" belgisini yangi qatorga o'tkazish
            description = description.replace('—', '\n—')

            # Ko'p bo'sh qatorlarni bitta qatorga qisqartirish
            description = re.sub(r'\n\s*\n', '\n', description)

            print(description[:400] + "..." if len(description) > 400 else description)
        else:
            print("Tavsif topilmadi")

        # 3. Parametrlarni olish
        print("\n🏠 PARAMETRLAR:")
        print("-" * 80)

        params = {}

        # HTML matnidan parametrlarni izlash
        page_text = str(soup)

        # Xonalar soni
        rooms_match = re.search(r'Количество комнат.*?(\d+)', page_text, re.IGNORECASE | re.DOTALL)
        if rooms_match:
            params['Количество комнат'] = rooms_match.group(1)
            print(f"Количество комнат: {rooms_match.group(1)}")

        # Qavat
        floor_match = re.search(r'Этаж.*?(\d+)', page_text, re.IGNORECASE | re.DOTALL)
        if floor_match:
            params['Этаж'] = floor_match.group(1)
            print(f"Этаж: {floor_match.group(1)}")

        # Uy qavatlar soni
        floors_match = re.search(r'Этажность дома.*?(\d+)', page_text, re.IGNORECASE | re.DOTALL)
        if floors_match:
            params['Этажность дома'] = floors_match.group(1)
            print(f"Этажность дома: {floors_match.group(1)}")

        # Telefon raqamlar (faqat sahifa matnidan, tugma bosilmasdan)
        phone_numbers = []

        # Tel: linklar
        tel_links = soup.find_all('a', href=re.compile(r'^tel:'))
        for link in tel_links:
            href = link.get('href', '')
            phone = href.replace('tel:', '')
            clean_phone = re.sub(r'[^\d]', '', phone)
            if clean_phone and len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                phone_numbers.append(clean_phone)
                print(f"📞 Tel: linkdan topildi: {clean_phone}")

        # Sahifa matnidan qidirish
        if not phone_numbers:
            body_text = soup.get_text()
            all_phones = re.findall(r'\+?\d{1,4}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{2}', body_text)

            for phone in all_phones:
                clean_phone = re.sub(r'[^\d]', '', phone)
                if (clean_phone.startswith('998') or (clean_phone.startswith('9') and len(clean_phone) == 9)) \
                   and len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                    phone_numbers.append(clean_phone)
                    if len(phone_numbers) <= 2:
                        print(f"�� Sahifa matnidan topildi: {clean_phone}")

        # Tavsifdan olish
        if not phone_numbers and description:
            found_phones = re.findall(r'\+?\d{1,4}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{2}', description)
            for phone in found_phones:
                clean_phone = re.sub(r'[^\d]', '', phone)
                if len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                    phone_numbers.append(clean_phone)
                    print(f"📞 Tavsifdan topildi: {clean_phone}")

        if phone_numbers:
            params['Телефон'] = ', '.join(phone_numbers[:3])
            print(f"Телефон: {params['Телефон']}")
        else:
            print("⚠️ Telefon topilmadi (tugma bosilmadi)")
            print("ℹ️ Requests+BeautifulSoup JavaScript tugmalarini bosa olmaydi")
            print("💡 Telefon ko'rish uchun e'lon linkiga kiring")

        return {
            'images': images,
            'description': description,
            'params': params
        }

    except Exception as e:
        print(f"\n❌ Xatolik: {e}")
        return None

if __name__ == "__main__":
    # Test URL
    import sqlite3

    conn = sqlite3.connect('elonlar.db')
    cursor = conn.cursor()
    cursor.execute('SELECT url FROM ads ORDER BY id DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()

    if result:
        test_url = result[0]
        details = get_ad_details(test_url)

        if details:
            print(f"\n{'='*80}")
            print("✅ NATIJA:")
            print('='*80)
            print(f"Rasmlar soni: {len(details['images'])}")
            print(f"Tavsif uzunligi: {len(details['description'])} belgi")
            print(f"Parametrlar soni: {len(details['params'])}")
