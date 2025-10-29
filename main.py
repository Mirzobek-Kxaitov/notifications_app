#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OLX E'lonlar Bot - Asosiy fayl
Har 3 daqiqada:
1. OLX dan yangi e'lonlarni parsing qiladi
2. Telegram kanaliga yuboradi
"""

import time
import asyncio
from parse_olx_complete import parse_all_ads
from poster import post_ads_to_telegram

def main():
    """Asosiy sikl - har 5 daqiqada ishlaydi"""

    print("=" * 60)
    print("🤖 OLX E'lonlar Bot ishga tushdi!")
    print("🚀 CI/CD TEST - Version 2.0 ")
    print("✅ GitHub Actions orqali avtomatik deploy qilindi!")
    print("=" * 60)
    print()

    while True:
        try:
            print("\n" + "=" * 50)
            print(f"⏰ Yangi iteratsiya: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 50)

            # 1. Parsing - yangi e'lonlarni olish
            print("\n📡 1/2: OLX dan e'lonlar yuklanmoqda...")
            parse_all_ads()

            # 2. Telegramga yuborish
            print("\n📤 2/2: Telegram kanaliga yuborilmoqda...")
            asyncio.run(post_ads_to_telegram())

            # 3 daqiqa kutish
            print("\n✅ Iteratsiya tugadi!")
            print("⏳ Keyingi tekshirish 3 daqiqadan so'ng...")
            print("=" * 50)
            time.sleep(180)  # 3 daqiqa = 180 soniya

        except KeyboardInterrupt:
            print("\n\n❌ Bot to'xtatildi (Ctrl+C)")
            break
        except Exception as e:
            print(f"\n❌ Xatolik yuz berdi: {e}")
            print("⏳ 30 soniyadan so'ng qayta urinish...")
            time.sleep(30)

if __name__ == "__main__":
    main()
