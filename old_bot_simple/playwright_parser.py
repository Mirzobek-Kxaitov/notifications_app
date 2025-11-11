#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E'lon sahifasidan barcha rasmlar va tavsifni olish - Playwright bilan
"""

from playwright.sync_api import sync_playwright
import re
import time

def get_ad_details(url):
    """E'lon sahifasidan barcha rasmlar va tavsifni olish"""

    print(f"\n{'='*80}")
    print(f"URL: {url}")
    print('='*80)

    with sync_playwright() as p:
        # Chromium brauzerini ishga tushirish
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        try:
            # Sahifani yuklash
            page.goto(url, timeout=30000)
            page.wait_for_load_state('networkidle')
            time.sleep(2)  # Qo'shimcha kutish

            # 1. Barcha rasmlarni olish
            print("\n📸 RASMLAR:")
            print("-" * 80)

            images = []

            # Rasmlarni topish
            img_elements = page.query_selector_all('img[src*="apollo.olxcdn.com"]')

            for idx, img in enumerate(img_elements[:10], 1):
                src = img.get_attribute('src')
                if src and 'image' in src:
                    # Katta formatga o'zgartirish
                    if 's=' in src:
                        src = src.replace('s=120x90', 's=1280x960')
                        src = src.replace('s=216x152', 's=1280x960')
                        src = src.replace('s=644x461', 's=1280x960')

                    if src not in images:
                        images.append(src)
                        print(f"{idx}. {src[:80]}...")

            print(f"\nJami topilgan rasmlar: {len(images)}")

            # 2. Tavsifni olish
            print("\n📝 TAVSIF:")
            print("-" * 80)

            description = ""
            try:
                desc_element = page.query_selector('[data-cy="ad_description"]')
                if desc_element:
                    description = desc_element.inner_text().strip()
                    print(description[:300] + "..." if len(description) > 300 else description)
                else:
                    print("Tavsif topilmadi")
            except Exception as e:
                print(f"Tavsif olishda xatolik: {e}")

            # 3. Parametrlarni olish (xonalar, qavat, telefon)
            print("\n🏠 PARAMETRLAR:")
            print("-" * 80)

            params = {}

            # HTML'dan barcha matnni olish
            page_text = page.content()

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

            # Telefon raqamlar
            phone_numbers = []

            # STRATEGIYA 1: "Показать телефон" tugmalarini sinash
            button_selectors = [
                'button:has-text("Показать")',
                'button:has-text("телефон")',
                'a[href^="tel:"]'
            ]

            for selector in button_selectors:
                try:
                    button = page.query_selector(selector)
                    if button:
                        print(f"✅ Tugma topildi: {selector}")
                        button.click()
                        time.sleep(2)

                        # Telefon raqamni olish
                        page_body = page.query_selector('body').inner_text()
                        found_phones = re.findall(r'\+?\d{1,4}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{2}', page_body)

                        for phone in found_phones:
                            clean_phone = re.sub(r'[^\d]', '', phone)
                            if len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                                phone_numbers.append(clean_phone)
                                print(f"📞 Topildi: {clean_phone}")
                        break
                except:
                    continue

            # STRATEGIYA 2: Tel: linklar
            if not phone_numbers:
                tel_links = page.query_selector_all('a[href^="tel:"]')
                for link in tel_links:
                    href = link.get_attribute('href')
                    phone = href.replace('tel:', '')
                    clean_phone = re.sub(r'[^\d]', '', phone)
                    if clean_phone and len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                        phone_numbers.append(clean_phone)
                        print(f"📞 Tel: linkdan topildi: {clean_phone}")

            # STRATEGIYA 3: Sahifa matnidan qidirish
            if not phone_numbers:
                body_text = page.query_selector('body').inner_text()
                all_phones = re.findall(r'\+?\d{1,4}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{2}', body_text)

                for phone in all_phones:
                    clean_phone = re.sub(r'[^\d]', '', phone)
                    if (clean_phone.startswith('998') or (clean_phone.startswith('9') and len(clean_phone) == 9)) \
                       and len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                        phone_numbers.append(clean_phone)
                        if len(phone_numbers) <= 2:
                            print(f"📞 Sahifa matnidan topildi: {clean_phone}")

            # STRATEGIYA 4: Tavsifdan olish
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

            browser.close()

            return {
                'images': images,
                'description': description,
                'params': params
            }

        except Exception as e:
            print(f"\n❌ Xatolik: {e}")
            browser.close()
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
