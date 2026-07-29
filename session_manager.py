import uuid
from datetime import datetime

from bot import send_text


class SessionManager:

    def __init__(self, sheets):

        self.sheets = sheets

    async def create_session(self, schedule):

        session = {
            "SessionID": str(uuid.uuid4()),
            "ScheduleID": schedule["ScheduleID"],
            "StartDateTime": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "SenderUserID": schedule["SenderUserID"],
            "ReceiverUserID": "",
            "Status": "WAITING_SENDER_ANSWER",
            "AcceptDateTime": "",
            "AcceptResult": "",
            "FinishDateTime": "",
            "CurrentQuestionOrder": 1
        }

        # Сохраняем Session
        self.sheets.save_session(session)

        # Находим пользователя
        user = self.sheets.get_user_by_id(
            schedule["SenderUserID"]
        )

        if user is None:

            print("Sender not found")

            return

        telegram_id = int(user["TelegramID"])

        # Отправляем стартовое сообщение
        sender_start = self.sheets.get_template("SenderStart")

        if sender_start:
            await send_text(
                telegram_id,
                sender_start
            )

        # Получаем вопросы сдающего
        questions = self.sheets.get_sender_questions()

        if len(questions) == 0:

            print("Sender questions not found")

            return

        first_question = questions[0]

        await send_text(
            telegram_id,
            first_question["Question"]
        )

        print()
        print("=" * 50)
        print("SESSION CREATED")
        print(session)
        print("=" * 50)
        print()

        return session
