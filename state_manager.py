import uuid
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class StateManager:

    def __init__(self, sheets, bot):

        self.sheets = sheets
        self.bot = bot

    async def process_message(
        self,
        session,
        user,
        message
    ):
        print(f">>> process_message: {session['Status']}")
        status = session["Status"]

        if status == "WAITING_SENDER_ANSWER":

            await self.process_sender_answer(
                session,
                user,
                message
            )

            return

        if status == "WAITING_RECEIVER_CONFIRM":

            await self.process_receiver_confirm(
                session,
                user,
                message
            )

            return

        if status == "WAITING_RECEIVER_ANSWER":

            await self.process_receiver_answer(
                session,
                user,
                message
            )

            return

        print(f"Unknown status: {status}")
        
    async def process_callback(
        self,
        session,
        user,
        data
    ):

        print(f">>> CALLBACK: {data}")
        
        if data in ["accept", "reject"]:

            if session["Status"] != "WAITING_RECEIVER_CONFIRM":
                print("Callback ignored")
                return
                
        if data == "accept":
            print(">>> ACCEPT")            
            self.sheets.update_session(
                session["SessionID"],
                "AcceptDateTime",
                datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            )

            self.sheets.update_session(
                session["SessionID"],
                "AcceptResult",
                "ACCEPTED"
            )

            self.sheets.update_session_status(
                session["SessionID"],
                "WAITING_RECEIVER_ANSWER"
            )
            self.sheets.update_session_question_order(
                session["SessionID"],
                1
            )
            print("Loading receiver questions...")
            questions = self.sheets.get_receiver_questions()
            print(questions)

            if len(questions) > 0:

                await self.bot.send_message(
                    chat_id=int(user["TelegramID"]),
                    text=questions[0]["Question"]
                )

            return


        if data == "reject":

            self.sheets.update_session(
                session["SessionID"],
                "AcceptDateTime",
                datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            )

            self.sheets.update_session(
                session["SessionID"],
                "AcceptResult",
                "REJECTED"
            )

            self.sheets.update_session_status(
                session["SessionID"],
                "WAITING_RECEIVER_ANSWER"
            )
            self.sheets.update_session_question_order(
                session["SessionID"],
                1
            )            
            questions = self.sheets.get_receiver_questions()

            if len(questions) > 0:

                await self.bot.send_message(
                    chat_id=int(user["TelegramID"]),
                    text=questions[0]["Question"]
                )

            return
        if not data.startswith("receiver:"):
            return

        receiver_user_id = data.split(":")[1]

        self.sheets.update_session_receiver(
            session["SessionID"],
            receiver_user_id
        )

        self.sheets.update_session_question_order(
            session["SessionID"],
            1
        )

        self.sheets.update_session_status(
            session["SessionID"],
            "WAITING_RECEIVER_CONFIRM"
        )

        receiver = self.sheets.get_user_by_id(
            receiver_user_id
        )
        print("Receiver:", receiver)

        if receiver is None:
            return

        template = self.sheets.get_template(
            "ReceiverRequest"
        )

        print("Template:", template)
        print("Before send receiver")

        sender_answers = self.sheets.get_answers_by_session(
            session["SessionID"],
            "Sender"
        )
        receiver_answers = self.sheets.get_answers_by_session(
            session["SessionID"],
            "Receiver"
        )

        sender_summary = ""
        receiver_summary = ""

        print("Sender answers:", sender_answers)
        
        for answer in sender_answers:

            print(answer)

            question = self.sheets.get_question_by_id(
                answer["QuestionID"]
            )

            if question is None:
                continue

            sender_summary += (
                f"• {question['Question']}: "
                f"{answer['Answer']}\n"
            )

        for answer in receiver_answers:

            question = self.sheets.get_question_by_id(
                answer["QuestionID"]
            )

            if question is None:
                continue

            receiver_summary += (
                f"• {question['Question']}\n"
                f"{answer['Answer']}\n\n"
            )
        
        sender = self.sheets.get_user_by_id(
            session["SenderUserID"]
        )

        template = (
            "📥 <b>Вам передают смену</b>\n\n"

            f"👤 <b>Сдающий:</b>\n"
            f"{sender['FullName']}\n\n"

            "━━━━━━━━━━━━━━━━━━\n\n"

            "📋 <b>Краткая информация</b>\n\n"

            f"{sender_summary}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Принять",
                        callback_data="accept"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отклонить",
                        callback_data="reject"
                    )
                ]
            ]
        )

        await self.bot.send_message(
            chat_id=int(receiver["TelegramID"]),
            text=template,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await self.bot.send_message(
            chat_id=int(sender["TelegramID"]),
            text="✅ Запрос на передачу смены отправлен принимающему."
        )
    async def process_sender_answer(
        self,
        session,
        user,
        message
    ):
        print(">>> process_sender_answer")
        questions = self.sheets.get_sender_questions()

        current_order = int(session["CurrentQuestionOrder"])

        current_question = None

        for question in questions:

            if int(question["QuestionOrder"]) == current_order:
                current_question = question
                break

        if current_question is None:

            print("Current question not found")
            return

        answer = {
               "AnswerID": str(uuid.uuid4()),
                "SessionID": session["SessionID"],
                "UserID": user["UserID"],
                "Role": "Sender",
                "QuestionID": current_question["QuestionID"],
                "Answer": message,
                "AnswerDateTime": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            }

        self.sheets.save_answer(answer)

        next_order = current_order + 1

        next_question = None

        for question in questions:

            if int(question["QuestionOrder"]) == next_order:
                next_question = question
                break

        if next_question is not None:

            self.sheets.update_session_question_order(
                session["SessionID"],
                next_order
            )

            await self.bot.send_message(
                chat_id=int(user["TelegramID"]),
                text=next_question["Question"]
            )

            return

        self.sheets.update_session_status(
            session["SessionID"],
            "WAITING_RECEIVER_CONFIRM"
        )
        #self.sheets.write_log(
        #    session["SessionID"],
        #    "SENDER_COMPLETED",
        #    user["FullName"]
        #)
        
        receivers = self.sheets.get_available_receivers(
            session["SenderUserID"]
        )

        keyboard = []

        for receiver in receivers:

            keyboard.append([
                InlineKeyboardButton(
                    text=receiver["FullName"],
                    callback_data=f"receiver:{receiver['UserID']}"
                )
            ])

        markup = InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )

        await self.bot.send_message(
            chat_id=int(user["TelegramID"]),
            text="Выберите принимающего сотрудника:",
            reply_markup=markup
        )

    async def process_receiver_confirm(
        self,
        session,
        user,
        message
    ):

        print("Receiver confirm")

    async def process_receiver_answer(
        self,
        session,
        user,
        message
    ):
        print(">>> process_receiver_answer")

        questions = self.sheets.get_receiver_questions()

        current_order = int(session["CurrentQuestionOrder"])

        current_question = None

        for question in questions:

            if int(question["QuestionOrder"]) == current_order:
                current_question = question
                break

        if current_question is None:
            return

        answer = {
            "AnswerID": str(uuid.uuid4()),
            "SessionID": session["SessionID"],
            "UserID": user["UserID"],
            "Role": "Receiver",
            "QuestionID": current_question["QuestionID"],
            "Answer": message,
            "AnswerDateTime": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }

        self.sheets.save_answer(answer)

        next_order = current_order + 1

        next_question = None

        for question in questions:

            if int(question["QuestionOrder"]) == next_order:
                next_question = question
                break

        if next_question is not None:

            self.sheets.update_session_question_order(
                session["SessionID"],
                next_order
            )

            await self.bot.send_message(
                chat_id=int(user["TelegramID"]),
                text=next_question["Question"]
            )

            return

        self.sheets.update_session(
            session["SessionID"],
            "FinishDateTime",
            datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        )

        self.sheets.update_session_status(
            session["SessionID"],
            "COMPLETED"
        )

        await self.bot.send_message(
            chat_id=int(user["TelegramID"]),
            text="✅ Передача смены завершена."
        )

        sender = self.sheets.get_user_by_id(
            session["SenderUserID"]
        )

        receiver = self.sheets.get_user_by_id(
            session["ReceiverUserID"]
        )

        await self.bot.send_message(
            chat_id=int(sender["TelegramID"]),
            text=(
                "✅ <b>Передача смены успешно завершена.</b>\n\n"
                f"🤝 Смену принял:\n"
                f"{receiver['FullName']}"
            ),
            parse_mode="HTML"
        )
        
        group_id = self.sheets.get_setting(
            "TelegramGroupID"
        )

        print("GROUP ID:", group_id)

        print("STEP 1")
        
        if group_id != "":

            sender = self.sheets.get_user_by_id(
                session["SenderUserID"]
            )

            receiver = self.sheets.get_user_by_id(
                session["ReceiverUserID"]
            )

            sender_answers = self.sheets.get_answers_by_session(
                session["SessionID"],
                "Sender"
            )

            receiver_answers = self.sheets.get_answers_by_session(
                session["SessionID"],
                "Receiver"
            )

            sender_summary = ""

            for answer in sender_answers:

                question = self.sheets.get_question_by_id(
                    answer["QuestionID"]
                )

                if question is None:
                    continue

                sender_summary += (
                    f"• {question['Question']}\n"
                    f"{answer['Answer']}\n\n"
                )

            receiver_summary = ""

            for answer in receiver_answers:

                question = self.sheets.get_question_by_id(
                    answer["QuestionID"]
                )

                if question is None:
                    continue

                receiver_summary += (
                    f"• {question['Question']}\n"
                    f"{answer['Answer']}\n\n"
                )

            group_message = (
                "📋 <b>Передача смены завершена</b>\n\n"

                f"👤 <b>Сдающий</b>\n"
                f"{sender['FullName']}\n\n"

                f"👤 <b>Принимающий</b>\n"
                f"{receiver['FullName']}\n\n"

                "━━━━━━━━━━━━━━━━━━\n\n"

                "📤 <b>Информация от сдающего</b>\n\n"

                f"{sender_summary}"

                "━━━━━━━━━━━━━━━━━━\n\n"

                "📥 <b>Ответы принимающего</b>\n\n"

                f"{receiver_summary}"

                "━━━━━━━━━━━━━━━━━━\n\n"

                f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            print(group_message)
            print("STEP 2")

            await self.bot.send_message(
                chat_id=int(group_id),
                text=group_message,
                parse_mode="HTML"
            )

            print("Group message sent")

            self.sheets.create_next_schedule(session)
