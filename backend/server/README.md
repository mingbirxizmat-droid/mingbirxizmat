# 1001 Xizmat: server (2-bosqich)

FastAPI + SQLite. Telefon raqami + SMS kod orqali kirish (JWT), rollar (user, worker, operator, manager, admin, superadmin),
buyurtmalar, ishchi paneli API'si, xabarlar, admin/audit va hisobotlar (kun/hafta/oy/chorak/yil).

## Ishga tushirish
```bash
pip install -r requirements.txt
cp .env.example .env   # MX_SECRET va MX_SUPERADMIN_PHONE ni to'ldiring
export $(grep -v '^#' .env | sed 's/ *#.*//' | xargs)
uvicorn app.main:app --reload   # hujjat: http://localhost:8000/docs
pip install pytest httpx && pytest -q   # 11 ta sinov
```
Docker: `docker build -t mx . && docker run -p 8000:8000 --env-file .env -v mxdata:/data mx`

## Xavfsizlik (bajarilgan)
OTP kodi hash holda saqlanadi, 5 daqiqa amal qiladi, 5 urinishdan keyin bloklanadi, 10 daqiqada 3 tadan ko'p so'ralmaydi.
JWT (12 soat), har so'rovda rol bazadan tekshiriladi. Egalik tekshiruvi (boshqa odamning buyurtmasiga tegib bo'lmaydi).
Parametrlangan SQL, kirishlar validatsiyasi, xavfsizlik sarlavhalari, audit jurnali, buyurtmani qabul qilish atomik (ikki ishchi bir buyurtmani ola olmaydi).
`MX_SECRET`siz server ishlab chiqarish rejimida ishga tushmaydi.

## Ishlab chiqarishdan oldin albatta
HTTPS (nginx/Caddy), PostgreSQL ga o'tish, zaxira nusxa, haqiqiy SMS adapteri (`app/integrations.py`), so'rovlar cheklovi (gateway darajasida),
jurnal va monitoring, mustaqil xavfsizlik auditi, shaxsiy ma'lumotlar qonuni bo'yicha yurist xulosasi.

## Hali yo'q (keyingi bosqichlar)
To'lov (Payme/Click/Uzcard-Humo), soliq/elektron hujjat, telefoniya (1001, SIP), xarita/tirbandlik, push bildirishnoma, qo'shimcha tillar, Telegram bot, veb va Android mijozlar.
