import asyncio

from sheets import GoogleSheets
from scheduler import Scheduler
from conversation_manager import ConversationManager
from bot import (
    bot,
    run_bot,
    set_conversation_manager
)


async def main():

    print("=" * 40)
    print("Shift Change Bot")
    print("=" * 40)

    sheets = GoogleSheets()
    sheets.test_connection()

    print("RAW SCHEDULE:")
    print(sheets.schedule.get_all_values())

    conversation_manager = ConversationManager(
        sheets,
        bot
    )

    set_conversation_manager(
        conversation_manager
    )

    scheduler = Scheduler(sheets)

    asyncio.create_task(
        scheduler.start()
    )

    await run_bot()


if __name__ == "__main__":
    asyncio.run(main())
