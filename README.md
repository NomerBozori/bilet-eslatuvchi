# Bilet eslatuvchi bot

Telegram bot matnni qabul qiladi, takrorlash oralig'ini so'raydi va shu oraliqda eslatma yuboradi. Eslatmalar SQLite bazasida saqlanadi, bot qayta ishga tushganda ham yo'qolmaydi. Bot faqat shaxsiy chatlarda ishlaydi.

## Ishga tushirish

Python 3.9 yoki yangisi kerak; qo'shimcha kutubxonalar talab qilinmaydi.

1. Telegram'da @BotFather orqali bot yarating. Agar token oshkor bo'lgan bo'lsa, BotFather'da `/revoke` orqali uni yangilang.
2. Terminalda yangi tokenni muhit o'zgaruvchisi sifatida bering va botni ishga tushiring:

   ```bash
   export BOT_TOKEN='YANGI_TOKEN'
   python3 bot.py
   ```

3. Telegram'da botga `/start` yuboring, eslatma matnini yozing, keyin masalan `30 daqiqa`, `2 soat`, `1 kun` yoki `1 hafta` deb javob bering. Oraliq 1 daqiqadan 365 kungacha bo'lishi mumkin. Birinchi eslatma shu oraliq o'tgach keladi.

`/list` — eslatmalar ro'yxati; `/delete 1` — raqami 1 bo'lgan eslatmani o'chirish; `/cancel` — yangi eslatma kiritishni bekor qilish; `/help` — yordam.

Bot uzluksiz eslatishi uchun jarayon va internet doim ishlashi kerak (masalan, serverda). Bir token bilan bir vaqtda faqat bitta bot jarayonini ishga tushiring. Baza odatda `reminders.db` faylida saqlanadi; boshqa joy belgilash uchun `DATABASE_PATH` muhit o'zgaruvchisidan foydalaning. Doimiy saqlanadigan diskdan foydalaning. Bot o'chib turganda o'tib ketgan eslatmalar ishga qaytgach bir marta yuboriladi, so'ng interval qaytadan boshlanadi. Yetkazish muvaffaqiyatsiz bo'lsa, bot bir daqiqadan keyin qayta urinadi.

**Telefon qo'ng'irog'i:** Telegram Bot API oddiy telefon raqamiga yoki Telegram orqali qo'ng'iroq qilish imkonini bermaydi. Buning uchun alohida telefoniya provayderi, telefon raqami, rozilik va odatda pullik xizmat kerak. Hozirgi bot faqat Telegram xabarlarini yuboradi; telefoningizda Telegram bildirishnomalarini yoqing.

## Tekshirish

```bash
python3 -m unittest discover -s tests -v
```

## Kompyuterga yuklamasdan Railway'da ishlatish

Railway GitHub reposidan Dockerfile orqali botni ishga tushirishi mumkin. Railway hisobini ulash va xizmat narxlari Railway shartlariga bog'liq; doimiy disk uchun to'lov talab qilinishi mumkin.

1. Ushbu o'zgarishlar GitHub'ning asosiy (`main`) branchiga birlashtirilganiga ishonch hosil qiling.
2. [Railway](https://railway.com/) saytida hisob yarating, **New Project → Deploy from GitHub repo** orqali ushbu repositoriyani tanlang. Railway'ga GitHub ruxsati kerak bo'lishi mumkin.
3. Xizmat sozlamalarining **Variables** bo'limiga `BOT_TOKEN` ni qo'shing. BotFather'dan olingan yangi tokenni qiymat sifatida kiriting; tokenni GitHub'ga yoki chatga joylamang.
4. Xizmatga Railway **Volume** qo'shing va uning mount path qiymatini `/data` deb belgilang. Variables bo'limiga `DATABASE_PATH=/data/reminders.db` ni qo'shing. Volume bo'lmasa, qayta deploy paytida eslatmalar yo'qolishi mumkin.
5. Xizmatni qayta deploy qiling. Deploy logida `Bot ishga tushdi` yozuvini ko'ring va Telegram'da botga `/start` yuboring. Tokenni ishlatayotgan boshqa bot jarayonlarini to'xtating: bitta token uchun faqat bitta nusxa ishlasin.

Bot veb-sayt emas va port ochishi shart emas. Railway xizmati to'xtasa yoki uyquga ketsa, eslatmalar yuborilmaydi; tarifingiz uzluksiz ishlashini tekshiring.
