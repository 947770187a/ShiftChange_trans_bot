from state_manager import StateManager
from registration_manager import RegistrationManager

class ConversationManager:

    def __init__(self, sheets, bot):

        self.sheets = sheets
        self.bot = bot
        self.state_manager = StateManager(sheets, bot)
        self.registration_manager = RegistrationManager(
            sheets,
            bot
        )

    async def process_telegram_message(
        
        self,
        telegram_id,
        text
    ):
        print(">>> process_telegram_message") 
        user = self.find_user_by_telegram(telegram_id)

        if user is None:

            if self.registration_manager.is_pending(
                telegram_id
            ):

                await self.registration_manager.process_registration(
                    telegram_id,
                    text
                )

            else:

                await self.registration_manager.start_registration(
            telegram_id
                )

            return

        session = self.sheets.get_active_session_by_sender(
            user["UserID"]
        )

        if session is None:

            session = self.sheets.get_session_by_receiver(
                user["UserID"]
            )

        if session is None:
            return

        await self.state_manager.process_message(
            session=session,
            user=user,
            message=text
        )

    async def process_callback(
        self,
        telegram_id,
        data
    ):

        user = self.find_user_by_telegram(telegram_id)

        if user is None:
            return

        if data in ["accept", "reject"]:

            session = self.sheets.get_session_by_receiver(
                user["UserID"]
            )

        else:

            session = self.sheets.get_active_session_by_sender(
                user["UserID"]
            )

        if session is None:
            return

        await self.state_manager.process_callback(
            session=session,
            user=user,
            data=data
        )

    def find_user_by_telegram(self, telegram_id):

        return self.sheets.get_user_by_telegram(
            telegram_id
        )
