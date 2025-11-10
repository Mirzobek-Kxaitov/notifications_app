#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test: Selenium bilan e'lon sahifasidan barcha rasmlar va tavsifni olish
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

def get_ad_details(url):
    """E'lon sahifasidan barcha rasmlar va tavsifni olish"""

    print(f"\n{'='*80}")
    print(f"Test URL: {url}")
    print('='*80)

    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Browser ochilmasin
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Sahifani yuklash
        driver.get(url)
        time.sleep(3)  # JavaScript yuklanishi uchun

        # 1. Barcha rasmlarni olish
        print("\n📸 RASMLAR:")
        print("-" * 80)

        images = []

        # Picture taglarni topish
        try:
            img_elements = driver.find_elements(By.CSS_SELECTOR, 'img[src*="apollo.olxcdn.com"]')

            for idx, img in enumerate(img_elements[:10], 1):  # Maksimum 10 ta
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

        except Exception as e:
            print(f"Rasmlarni olishda xatolik: {e}")

        print(f"\nJami topilgan rasmlar: {len(images)}")

        # 2. Tavsifni olish
        print("\n📝 TAVSIF:")
        print("-" * 80)

        description = ""
        try:
            desc_element = driver.find_element(By.CSS_SELECTOR, '[data-cy="ad_description"]')
            description = desc_element.text.strip()
            print(description[:300] + "..." if len(description) > 300 else description)
        except Exception as e:
            print(f"Tavsif topilmadi: {e}")

        # 3. Parametrlarni olish (xonalar, qavat, telefon)
        print("\n🏠 PARAMETRLAR:")
        print("-" * 80)

        params = {}
        try:
            # HTML'dan barcha matnni olish va regex bilan izlash
            page_text = driver.page_source

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
            button_found = False

            # STRATEGIYA 1: "Показать телефон" tugmalarini sinash (2 xil XPath)
            button_xpaths = [
                "//*[@id='mainContent']/div/div[2]/div[3]/div[2]/div[1]/div/div[5]/div/button[3]",  # Yangi variant
                "//*[@id='mainContent']/div/div[2]/div[3]/div[1]/section/div/div/div[2]/div[2]/div/button[2]"  # Eski variant
            ]

            for xpath_index, button_xpath in enumerate(button_xpaths, 1):
                try:
                    show_button = driver.find_element(By.XPATH, button_xpath)

                    # Tugma matnini tekshirish
                    button_text = show_button.text.strip()
                    print(f"✅ Tugma topildi (variant {xpath_index}): '{button_text}'")

                    # JavaScript orqali bosish (ishonchli usul)
                    driver.execute_script("arguments[0].click();", show_button)
                    time.sleep(3)  # Raqam yuklanishi uchun kutish
                    button_found = True
                    print(f"✅ Tugma bosildi, telefon yuklanmoqda...")

                    # Tugma bosilgandan keyin matnni olish (tugma o'rnida telefon ko'rinadi)
                    try:
                        time.sleep(1)
                        updated_text = show_button.text.strip()

                        # Agar tugma matni o'zgardi - demak telefon ko'rindi
                        if updated_text != button_text and updated_text:
                            print(f"📱 Tugmadan telefon olindi: {updated_text}")

                            # Har xil formatdagi raqamlarni topish
                            found_phones = re.findall(r'\+?\d{1,4}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{2}', updated_text)

                            for phone in found_phones:
                                clean_phone = re.sub(r'[^\d]', '', phone)
                                if len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                                    phone_numbers.append(clean_phone)
                                    print(f"📞 Topildi (tugma matni): {clean_phone}")
                    except Exception as e:
                        print(f"⚠️ Tugma matnini qayta o'qishda xatolik: {e}")

                    # Atrofdagi elementlardan ham qidirish
                    if not phone_numbers:
                        try:
                            # Tugma parent elementini olish
                            parent = show_button.find_element(By.XPATH, "..")
                            parent_text = parent.text.strip()

                            found_phones = re.findall(r'\+?\d{1,4}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{2}', parent_text)

                            for phone in found_phones:
                                clean_phone = re.sub(r'[^\d]', '', phone)
                                if len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                                    phone_numbers.append(clean_phone)
                                    print(f"📞 Topildi (parent element): {clean_phone}")
                        except:
                            pass

                    break  # Bitta tugma ishlab ketsa - to'xtatamiz

                except Exception as e:
                    print(f"ℹ️ Variant {xpath_index} tugmasi topilmadi")
                    continue

            # STRATEGIYA 2: Tel: linklar orqali (ochiq telefon bo'lsa)
            if not phone_numbers:
                try:
                    phone_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'tel:')]")
                    if phone_elements:
                        print("📱 Tel: linklar topildi")
                    for elem in phone_elements:
                        phone = elem.get_attribute('href').replace('tel:', '')
                        clean_phone = re.sub(r'[^\d]', '', phone)
                        if clean_phone and len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                            phone_numbers.append(clean_phone)
                            print(f"📞 Topildi (tel: link): {clean_phone}")
                except:
                    pass

            # STRATEGIYA 3: Sahifa matnidan qidirish
            if not phone_numbers:
                try:
                    body_text = driver.find_element(By.TAG_NAME, 'body').text

                    # Har xil formatdagi raqamlarni topish
                    all_phones = re.findall(r'\+?\d{1,4}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{2}', body_text)

                    for phone in all_phones:
                        clean_phone = re.sub(r'[^\d]', '', phone)
                        # Faqat O'zbekiston raqamlari
                        if (clean_phone.startswith('998') or (clean_phone.startswith('9') and len(clean_phone) == 9)) \
                           and len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                            phone_numbers.append(clean_phone)
                            if len(phone_numbers) <= 2:  # Faqat birinchi 2 tasini chop etamiz
                                print(f"📞 Topildi (sahifa matni): {clean_phone}")
                except:
                    pass

            # STRATEGIYA 4: Tavsifdan olish
            if not phone_numbers and description:
                found_phones = re.findall(r'\+?\d{1,4}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{2}[\s\-\(\)]*\d{2}', description)
                for phone in found_phones:
                    clean_phone = re.sub(r'[^\d]', '', phone)
                    if len(clean_phone) >= 9 and clean_phone not in phone_numbers:
                        phone_numbers.append(clean_phone)
                        print(f"📞 Topildi (tavsif): {clean_phone}")

            if phone_numbers:
                params['Телефон'] = ', '.join(phone_numbers[:3])  # Maksimum 3 ta
                print(f"Телефон: {params['Телефон']}")

        except Exception as e:
            print(f"Parametrlarni olishda xatolik: {e}")

        driver.quit()

        return {
            'images': images,
            'description': description,
            'params': params
        }

    except Exception as e:
        print(f"\n❌ Xatolik: {e}")
        driver.quit()
        return None

if __name__ == "__main__":
    # Test URL (bazadan bitta e'lon olish)
    import sqlite3

    conn = sqlite3.connect('elonlar.db')
    cursor = conn.cursor()
    cursor.execute('SELECT url FROM ads ORDER BY id DESC LIMIT 1')
    test_url = cursor.fetchone()[0]
    conn.close()

    # Test
    result = get_ad_details(test_url)

    if result:
        print(f"\n{'='*80}")
        print("✅ NATIJA:")
        print('='*80)
        print(f"Rasmlar soni: {len(result['images'])}")
        print(f"Tavsif uzunligi: {len(result['description'])} belgi")
        print(f"Parametrlar soni: {len(result['params'])}")
