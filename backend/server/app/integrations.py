"""Tashqi tizimlar uchun adapterlar. Hozir faqat ishlab chiqish rejimidagi (dev) stub'lar bor.
Haqiqiy ulash uchun: provayder bilan shartnoma + kalitlar (.env) kerak."""
import os


class SmsProvider:
    def send(self, phone: str, text: str) -> None:
        raise NotImplementedError("SMS provayder ulanmagan (MX_SMS)")


class ConsoleSms(SmsProvider):
    def send(self, phone, text):
        print(f"[SMS dev] {phone}: {text}")


def get_sms() -> SmsProvider:
    if os.getenv("MX_SMS", "console") == "console":
        return ConsoleSms()
    return SmsProvider()  # bu yerga Eskiz/PlayMobile va h.k. adapteri qo'shiladi


class PaymentProvider:
    """Payme / Click / Uzcard-Humo: hisob-faktura yaratish va webhook imzosini tekshirish."""
    def create_invoice(self, order_id: int, amount: int) -> str: raise NotImplementedError
    def verify_webhook(self, headers: dict, body: bytes) -> bool: raise NotImplementedError


class TaxReporter:
    """Soliq organi API'lari va elektron hujjat aylanishi: buxgalter/yurist bilan kelishiladi."""
    def export(self, period: str) -> bytes: raise NotImplementedError


class Telephony:
    """1001 qisqa raqam, SIP va qo'ng'iroqlar: telefon operatori/SIP provayder bilan shartnoma kerak."""
    def route_call(self, caller: str) -> str: raise NotImplementedError
