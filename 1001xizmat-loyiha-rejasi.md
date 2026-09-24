# ISH REJASI (bosqichlar; har bir bosqich to'liq tugagach keyingisiga o'tiladi)

## 1-BOSQICH: ishlaydigan prototip (mijoz + ishchi + xodimlar)  [TUGADI]
- [x] 3 soniyalik ochilish ekrani, logotiplar (sariq: mijoz, qora: ishchi), telefon/planshet/kompyuter maketi
- [x] Bosh sahifa (asl dizayn), 5 faol bo'lim, qolganlari qulflangan, Marketplace oilasi
- [x] Har bir faol bo'limda 5 oyna: Asosiy, Xizmatlar, Buyurtmalar, Xabarlar, Profil
- [x] Buyurtma, bekor qilish, ikki tomonlama baho (mijoz -> ishchi, ishchi -> mijoz), operator chati
- [x] Shoshilinch qo'shimcha to'lov taklifi; oshxona tayyorlash vaqti (5-60 daq), eslatma, kechikish, +5 daq, jarimasiz rad etish
- [x] Ishchi rejimlari (haydovchi + kuryer + usta bir vaqtda), manzillar daftari, menyu, bildirishnoma, GPS
- [x] Xodimlar paneli: operator, admin (bo'limlarni yoqish/o'chirish), boshqaruvchi, super admin (rollar, audit)
- [x] Barcha tugmalar avtomatik sinovdan o'tkazildi (o'lik tugma yo'q)

## 2-BOSQICH: server va baza  [KOD TAYYOR VA SINALGAN; joylashtirish (deploy) qoldi]
- [x] SMS-kod orqali kirish, JWT, 6 ta rol (RBAC), egalik tekshiruvi, audit jurnali
- [x] Buyurtmalar, ishchi rejimlari va yaqin buyurtmalar (GPS masofa bo'yicha), atomik qabul qilish, ikki tomonlama baho
- [x] Oshxona vaqti (5-60), uzaytirish, jarimasiz rad etish; shoshilinch to'lov; operator chati va tayinlash
- [x] Hisobotlar (kun/hafta/oy/chorak/yil), bo'limlarni yoqish/o'chirish, yaqin ishchilar, buyurtmani kuzatish
- [x] 11 ta avtomatik sinov o'tdi; Dockerfile, .env.example, README (server/ papkasi, zip ichida)
- [ ] Serverga joylashtirish, PostgreSQL, HTTPS, haqiqiy SMS provayder (sizning hisob/shartnomangiz kerak)
- [ ] Mijoz prototipini shu API'ga ulash (3-bosqichda haqiqiy mijoz ilovasi bilan)
## 3-BOSQICH: Android ilova (Play Market tayyorgarligi), xarita va jonli kuzatuv, to'lov tizimlari
## 4-BOSQICH: veb-sayt, Telegram bot, operator/admin panellarining haqiqiy versiyasi
## 5-BOSQICH: telefoniya (1001, SIP, SMS), soliq/hujjat aylanishi, bank va sug'urta integratsiyasi
## 6-BOSQICH: xavfsizlik auditi, yuklama sinovi, ishga tushirish

---
# 1001 Xizmat (MingBirXizmat): loyiha rejasi va holat

## 1. Bajarilgan (ishlaydigan prototip: 1001xizmat-app.html)
- 3 soniyalik ochilish ekrani (sariq logotip), telefon / planshet / kompyuterga moslashuvchi maket
- Bosh sahifa (asl dizayn), yon tomonga suriladigan kategoriyalar, pastga aylantirish
- Faol bo'limlar: Taksi, Yetkazib berish, Ustalar, Taomlar, Marketplace (ichida Bozorlar, Marketlar, Do'konlar, Uydan savdo, Ulgurji)
- Qolgan barcha bo'limlar qulflangan: "Yaqin kunda ishga tushadi" + "xabar bering"
- Har bir faol bo'limda 5 oyna: Asosiy, Xizmatlar, Buyurtmalar, Xabarlar, Profil
- Buyurtma berish, bekor qilish, baholash (1-5 yulduz + izoh), operator bilan yozishma
- GPS (brauzer geolokatsiyasi), "Xaritada ochish"
- Ishchi paneli (qora logotip): onlayn/oflayn, buyurtmani qabul qilish, yo'lga chiqish, bajarish
- Tillar: O'zbekcha, Русский, English (qolganlari "tez orada")
- Aloqa markazi tugmasi: +998 95 484 00 03

## 1b. Yangi (2-bosqich)
- Xodimlar paneli (Profil -> Xodimlar paneli): Operator (tayinlash, bekor qilish, mijozga javob), Admin (statistika, bo'limlarni yoqish/o'chirish: ilovaga darhol ta'sir qiladi), Boshqaruvchi (hisobot, kechikishlar), Super admin (rollar, audit jurnali, eksport)
- Ishchi paneliga o'rtacha baho qo'shildi

## 2. Panellar (bosqichma-bosqich)
| Panel | Kim uchun | Holat |
|---|---|---|
| Foydalanuvchi ilovasi | mijoz | prototip tayyor |
| Ishchi paneli | haydovchi, kuryer, usta, oshxona | prototip tayyor (oddiy) |
| Operator paneli | qo'ng'iroq va chat | prototip tayyor (demo, serversiz) |
| Admin paneli | kontent, foydalanuvchilar, buyurtmalar | prototip tayyor (demo, serversiz) |
| Boshqaruvchi paneli | hudud / filial rahbari | prototip tayyor (demo, serversiz) |
| Super admin | rollar, sozlamalar, audit, moliya | prototip tayyor (demo, serversiz) |
| Veb-sayt, Telegram bot, Android (Play Market) | tarqatish kanallari | reja |

## 3. Server va bazani talab qiladigan modullar (prototipda yo'q)
Haqiqiy foydalanuvchi hisoblari (SMS orqali kirish), umumiy buyurtmalar bazasi, real vaqtda kuzatuv (xarita, haydovchi joylashuvi), to'lov (Payme, Click, Uzcard/Humo), reyting hisobi (mijoz <-> ishchi), oshxona tayyorlash vaqti (5-60 daq) va kechikish jarimalari, kuryer/taksi rejimini almashtirish, pul taklif qilish (shoshilinch), talab ko'p hududlar xaritasi, yo'l tirbandligi.

## 4. Tashqi tizimlar (hisob, shartnoma yoki litsenziya kerak)
- Telefoniya: 1001 qisqa raqam, SIP, SMS (operator/provayder bilan shartnoma)
- Soliq hisobotlari va elektron hujjat aylanishi (soliq organi API'lari va buxgalter)
- Xarita: OpenStreetMap yoki Yandex Maps API (kalit va narxni tekshirish)
- Bank/sug'urta integratsiyasi (hamkor bilan shartnoma)
- Play Market: Google Play Console akkaunti, imzolangan Android ilova (AAB), maxfiylik siyosati

## 4b. Xavfsizlik (majburiy)
Rollar bo'yicha kirish (RBAC), ikki bosqichli tasdiqlash, ma'lumotlarni shifrlash, audit jurnali, to'lov ma'lumotlarini o'zimizda saqlamaslik (faqat to'lov tizimi orqali), shaxsiy ma'lumotlar qonuniga rioya (saqlash joyini yurist bilan tekshirish), so'rovlar cheklovi (rate limit), zaxira nusxa.

## 5. Keyingi qadamlar
1. (BAJARILDI) Prototipni ishchi/operator/admin/boshqaruvchi/super admin oynalari bilan kengaytirish
2. Backend (baza + API + SMS kirish) uchun texnologiyani tanlash
3. Android ilovasi (Flutter yoki React Native) va Play Console tayyorgarligi
4. Telegram bot va veb-sayt
5. Yurist va buxgalter bilan litsenziya/soliq masalalari

---

# BUYRUQLAR BO'YICHA TO'LIQ HOLAT JADVALI (hech biri chetda qolmasligi uchun)
Belgilar: OK = tayyor va sinalgan | PR = prototip yoki qisman | KB = keyingi bosqich | TS = tashqi shart (hisob, shartnoma yoki litsenziya kerak) | X = men qila olmayman

| # | Buyruq | Holat | Izoh |
|---|---|---|---|
| 1 | 3 soniyalik ochilish ekrani | OK | sariq logotip bilan |
| 2 | Telefon / planshet / kompyuterga moslashuv | OK | 3 kenglikda sinaldi |
| 3 | Dizayn asl suratdagidek, yuqori-past va chap-o'ng suriladi | OK | |
| 4 | Bosh oynadagi kategoriyalar: taksi, dostavka, ustalar, taomlar, marketplace, bozorlar | OK | bozorlar Marketplace ichida |
| 5 | Qolgan kategoriyalar "yaqin kunda" deb qulflangan | OK | admin yoqsa ochiladi |
| 6 | Har bir kategoriyada 5 oyna, hamma tugma ishlaydi | OK | avtomatik audit: o'lik tugma yo'q |
| 7 | Kategoriyalarni sohasiga qarab oilaga birlashtirish | OK | oilalar ilova va bazada |
| 8 | GPS | PR | brauzer GPS + serverda masofa hisobi; jonli xarita KB (3) |
| 9 | Logotip: sariq mijozga, qora ishchiga | OK | |
| 10 | Mijoz, ishchi, operator, admin, super admin, boshqaruvchi panellari | PR | rollar va API tayyor; haqiqiy panel interfeysi KB (4) |
| 11 | Veb-sayt, Telegram bot, "App Store ko'rinishidagi sayt", Android | KB | 3-4 bosqich |
| 12 | Play Console orqali Play Market | TS | Google akkaunti + imzolangan Android ilova (3-bosqich) |
| 13 | 3D 8K ikonkalar, bitta standart dizayn | X | rasm yarata olmayman; yaratib yuborsangiz joylayman |
| 14 | 1001 raqamiga qo'ng'iroq, +998 95 484 00 03 ga ulash, operatorlar | TS | ilovada "Aloqa markazi" tugmasi bor; qisqa raqam va SIP telefon operatori bilan shartnoma kerak |
| 15 | SMS | PR | kirish kodi mantig'i tayyor; haqiqiy SMS provayder TS |
| 16 | SIP telefoniya, Bluetooth | TS / ? | SIP: provayder. Bluetooth nimaga kerakligi aniq emas: tushuntirsangiz rejalayman |
| 17 | Soliq hisobotlari, elektron hujjat aylanishi | TS | hisobot API bor; soliq organi integratsiyasi buxgalter bilan |
| 18 | Kunlik / haftalik / oylik / choraklik / yillik hisobotlar | OK | /reports |
| 19 | Reyting: mijoz -> ishchi va ishchi -> mijoz, izohlar | OK | |
| 20 | Oshxona vaqti 5-60 daq, tayyor bo'lishidan oldin signal | OK | 2 daqiqa qolganda xabar |
| 21 | Tayyor bo'lmasa vaqt qo'shish, kuryer 10 daq kutib jarimasiz rad etishi | OK | |
| 22 | Kechikish, jarima, hisob-kitob, rag'batlantirish tizimi | PR | kechikish belgisi bor; jarima/bonus qoidalari biznes qarori, KB (4) |
| 23 | Shoshilinch: foydalanuvchi qo'shimcha pul taklif qilishi | OK | |
| 24 | Xaritada talab ko'p joylar (qizil "alanga") | KB | xarita kerak (3) |
| 25 | Yaqin bo'sh taksi/kuryerni ko'rsatish | PR | API tayyor (/nearby/workers); xaritada ko'rsatish KB (3) |
| 26 | Yo'ldagi taksini to'xtatib ilova orqali shu zahoti buyurtma | KB | QR/kod bilan, 4-bosqich |
| 27 | Havo buzilganda ikki variant taklif | KB | ob-havo API, 4-bosqich |
| 28 | Taksi va kuryer bir vaqtda; bo'sh taksi dostavka olishi | OK | rejimlar |
| 29 | Yo'l tirbandligi | KB | xarita API (3) |
| 30 | Taksi/kuryer kelayotganini ko'rish | PR | /orders/{id}/track API tayyor; xaritada KB (3) |
| 31 | Eng xavfsiz ilova: foydalanuvchi, ishchi, bank, kiber himoya | PR | server tomoni chorasi bajarildi (OTP, JWT, RBAC, egalik, audit, atomik qabul); HTTPS, monitoring, mustaqil audit KB (6) |
| 32 | Barcha tillar | PR | 3 til ishlaydi; qolganlari tarjima talab qiladi (4) |
| 33 | Dunyo ilovalaridan g'oyalar (Uber, DoorDash, Yandex va boshqalar) | PR | ishchi rejimlari, kechikish/eta, bahoning ikki tomonlamaligi, shoshilinch tip, talab xaritasi (KB) |
| 34 | Biznes modellar: B2C, C2C, B2B, ulgurji, dropshipping, auksion, tender, ijara, affiliate... | KB | Ulgurji, Auksion, Tender, Ijara bo'limlari qulflangan turibdi; 4-bosqichdan boshlab |
| 35 | Savdolashish, vositachilik, subpudrat, material sourcing, komissiya | PR | komissiya hisobi hisobotda (namunaviy 10%); qolganlari KB (4) |
| 36 | Loyalty, obuna, kupon/promo-kod, korporativ kabinet, Seller Academy, Developer API/SDK | KB | API (OpenAPI hujjati) asos bo'ladi |
| 37 | Bank, sug'urta, lizing integratsiyalari | TS | hamkor bilan shartnoma |
| 38 | Kodni tozalash, takrorlarni olib tashlash | PR | server toza; prototip HTML 4-bosqichda haqiqiy mijoz ilovasi bilan almashadi |
| 39 | Hamma ishni kodga saqlash | OK | shu fayl, server.zip, ilova havolasi va xotira |
