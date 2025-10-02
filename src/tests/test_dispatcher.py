# tests/test_dispatch.py
import pytest
from aiogram import Dispatcher, Bot
from aiogram.types import Update, Message, Chat, User
from src.handlers import curiosities_router, commands_router  # Import your routers


@pytest.mark.asyncio
async def test_message_routing():
    bot = Bot(token="fake_token")
    dp = Dispatcher()
    # Include the routers you want to test
    dp.include_router(curiosities_router)

    # Create a fake "Message" update
    test_update = Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=1234567890,
            chat=Chat(id=1, type="private"),
            from_user=User(id=1, is_bot=False, first_name="Test"),
            text="📚 Curiosidad"
        )
    )

    # The dispatcher will process the update and route it to your handler
    # You can check the results by mocking `message.answer`