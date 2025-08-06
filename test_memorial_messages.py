import asyncio
from datetime import datetime, time
import pytz

from memorial_messages import MemorialMessageScheduler

class DummyPublisher:
    async def send_simple_message(self, message):
        print(f"[TEST] Would send: {message}")
        return True

def test_should_send_memorial_message_at_9():
    publisher = DummyPublisher()
    scheduler = MemorialMessageScheduler(publisher)
    # Підміняємо last_sent_date, щоб не було "сьогодні вже надсилали"
    scheduler.last_sent_date = None

    # Підміняємо datetime.now для тесту (9:05 Київ)
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2024, 1, 1, 9, 5, 0, tzinfo=pytz.timezone("Europe/Kiev"))

    original_datetime = scheduler.__class__.__dict__['should_send_memorial_message'].__globals__['datetime']
    scheduler.__class__.__dict__['should_send_memorial_message'].__globals__['datetime'] = FakeDatetime

    try:
        assert scheduler.should_send_memorial_message() is True
        print("[TEST PASSED] should_send_memorial_message returns True at 9:05")
    finally:
        # Повертаємо оригінальний datetime
        scheduler.__class__.__dict__['should_send_memorial_message'].__globals__['datetime'] = original_datetime

if __name__ == "__main__":
    test_should_send_memorial_message_at_9()
