import os
import json
import uuid
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

from config import (
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_SHEET_NAME,
    SHEET_USERS,
    SHEET_QUESTIONS,
    SHEET_SCHEDULE,
    SHEET_SESSIONS,
    SHEET_ANSWERS,
    SHEET_SETTINGS,
    SHEET_TEMPLATES,
    SHEET_LOG
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


class GoogleSheets:

    def __init__(self):

        if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):

            data = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

            creds = Credentials.from_service_account_info(
                data,
                scopes=SCOPES
            )

        else:

            creds = Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_FILE,
                scopes=SCOPES
            )

        self.client = gspread.authorize(creds)
        self.book = self.client.open(GOOGLE_SHEET_NAME)
        self.users = self.book.worksheet(SHEET_USERS)
        self.questions = self.book.worksheet(SHEET_QUESTIONS)
        self.schedule = self.book.worksheet(SHEET_SCHEDULE)
        self.sessions = self.book.worksheet(SHEET_SESSIONS)
        self.answers = self.book.worksheet(SHEET_ANSWERS)
        self.settings = self.book.worksheet(SHEET_SETTINGS)
        self.templates = self.book.worksheet(SHEET_TEMPLATES)
        self.answers_cache = self.answers.get_all_records()
        self.log = self.book.worksheet(SHEET_LOG)
        self.users_cache = self.users.get_all_records()
        self.questions_cache = self.questions.get_all_records()
        self.settings_cache = self.settings.get_all_records()
        self.templates_cache = self.templates.get_all_records()
        self.sessions_cache = self.sessions.get_all_records()
        self.session_headers = self.sessions.row_values(1)

    # ==========================================================
    # SERVICE
    # ==========================================================

    def test_connection(self):

        print("=" * 50)
        print("GOOGLE SHEETS CONNECTED")
        print("=" * 50)

        print(f"Users: {self.users.row_count}")
        print(f"Questions: {self.questions.row_count}")
        print(f"Schedule: {self.schedule.row_count}")

        print("=" * 50)
        
    def get_setting(self, name):

        if len(self.settings_cache) == 0:
            return ""
      
        return self.settings_cache[0].get(name, "")

    # ==========================================================
    # USERS
    # ==========================================================

    def get_users(self):
        return self.users_cache

    def get_user_by_id(self, user_id):

        for user in self.users_cache:

            if user["UserID"] == user_id:
                return user

        return None

    def get_user_by_telegram(self, telegram_id):

        telegram_id = str(telegram_id)

        for user in self.users_cache:

            if str(user["TelegramID"]) == telegram_id:
                return user

        return None
    def add_user(
        self,
        user_id,
        full_name,
        telegram_id
    ):

        row = [
            user_id,
            full_name,
            str(telegram_id),
            "FALSE",
            "TRUE"
        ]

        self.users.append_row(row)

        self.users_cache.append({
            "UserID": user_id,
            "FullName": full_name,
            "TelegramID": str(telegram_id),
            "IsAdmin": "FALSE",
            "Active": "TRUE"
        })

    # ==========================================================
    # QUESTIONS
    # ==========================================================

    def get_questions(self):
        return self.questions_cache

    def get_sender_questions(self):

        questions = []

        for question in self.questions_cache:

            if (
                question["Role"] == "Sender"
                and question["Active"] == "TRUE"
            ):
                questions.append(question)

        questions.sort(
            key=lambda q: int(q["QuestionOrder"])
        )

        return questions
    def get_receiver_questions(self):

        questions = []

        for question in self.questions_cache:

            if (
                question["Role"] == "Receiver"
                and question["Active"] == "TRUE"
            ):
                questions.append(question)

        questions.sort(
            key=lambda q: int(q["QuestionOrder"])
        )

        return questions

    # ==========================================================
    # SCHEDULE
    # ==========================================================

    def get_schedule(self):
        return self.schedule.get_all_records()

    def update_schedule_executed(self, schedule_id):

        records = self.schedule.get_all_records()

        for i, row in enumerate(records, start=2):

            if row["ScheduleID"] == schedule_id:

                self.schedule.update_cell(i, 5, "TRUE")
                return

    def create_next_schedule(self, session):

        schedule = None

        for row in self.get_schedule():

            if row["ScheduleID"] == session["ScheduleID"]:
                schedule = row
                break

        if schedule is None:
            return

        start = datetime.strptime(
            schedule["StartDateTime"],
            "%d.%m.%Y %H:%M"
        )

        if start.hour == 2:

            next_start = start.replace(
                hour=14,
                minute=30
            )

        else:

            next_start = (
                start + timedelta(days=1)
            ).replace(
                hour=2,
                minute=30
            )
        
        next_start_str = next_start.strftime("%d.%m.%Y %H:%M")

        for row in self.get_schedule():

            if (
                row["SenderUserID"] == session["ReceiverUserID"]
                and row["StartDateTime"] == next_start_str
                and str(row["Active"]).upper() == "TRUE"
                and str(row["Executed"]).upper() == "FALSE"
            ):
                print("Next schedule already exists")
                return
                
        self.schedule.append_row([
            str(uuid.uuid4()),
            next_start_str,
            session["ReceiverUserID"],
            "TRUE",
            "FALSE"
        ])
    

    # ==========================================================
    # SESSIONS
    # ==========================================================

    def save_session(self, session):

        self.sessions.append_row([
            session["SessionID"],
            session["ScheduleID"],
            session["StartDateTime"],
            session["SenderUserID"],
            session["ReceiverUserID"],
            session["Status"],
            session["AcceptDateTime"],
            session["AcceptResult"],
            session["FinishDateTime"],
            session["CurrentQuestionOrder"]
        ])
        self.sessions_cache.append(session.copy())
    # ==========================================================
    # ANSWERS
    # ==========================================================

    def save_answer(self, answer):

        self.answers.append_row([
            answer["AnswerID"],
            answer["SessionID"],
            answer["UserID"],
            answer["Role"],
            answer["QuestionID"],
            answer["Answer"],
            answer["AnswerDateTime"]
        ])
        self.answers_cache.append(answer)
    def get_answers_by_session(
        self,
        session_id,
        role=None
    ):    

        result = []

        for answer in self.answers_cache:

            if answer["SessionID"] != session_id:
                continue

            if role is not None:

                if answer["Role"] != role:
                    continue

            result.append(answer)

        return result
        
    def get_question_by_id(self, question_id):

        for question in self.questions_cache:

            if question["QuestionID"] == question_id:
                return question

        return None
    def write_log(
        self,
        session_id,
        event,
        user_name
    ):

        self.log.append_row([
            datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            session_id,
            event,
            user_name
        ])
    # ==========================================================
    # MESSAGE TEMPLATES
    # ==========================================================

    def get_template(self, template_name):

        rows = self.templates_cache

        if not rows:
            return ""

        return rows[0].get(template_name, "")

    # ==========================================================
    # SESSIONS
    # ==========================================================

    def get_sessions(self):
        return self.sessions_cache

    def get_session_by_sender(self, user_id):

        for session in self.sessions_cache:

            if (
                session["SenderUserID"] == user_id
                and session["FinishDateTime"] == ""
            ):
                return session

        return None

    def get_session_by_receiver(self, user_id):

        for session in reversed(self.sessions_cache):

            if (
                session["ReceiverUserID"] == user_id
                and session["FinishDateTime"] == ""
            ):
                return session

        return None

    def update_session(self, session_id, column, value):

        if column not in self.session_headers:
            return

        column_index = self.session_headers.index(column) + 1

        for row_index, cached in enumerate(self.sessions_cache, start=2):

            if cached["SessionID"] == session_id:

                self.sessions.update_cell(
                    row_index,
                    column_index,
                    value
                )

                cached[column] = value

                return

    def get_active_session_by_sender(self, user_id):

        for session in reversed(self.sessions_cache):

            if (
                session["SenderUserID"] == user_id
                and session["FinishDateTime"] == ""
            ):
                return session

        return None

    def update_session_question_order(
        self,
        session_id,
        question_order
    ):

        self.update_session(
            session_id,
            "CurrentQuestionOrder",
            question_order
        )

    def update_session_status(
        self,
        session_id,
        status
    ):

        self.update_session(
            session_id,
            "Status",
            status
        )
    def update_session_receiver(
        self,
        session_id,
        receiver_user_id
    ):

        self.update_session(
            session_id,
            "ReceiverUserID",
            receiver_user_id
        )
    def get_available_receivers(self, sender_user_id):

        users = []

        for user in self.get_users():

            if user["Active"] != "TRUE":
                continue

            if user["UserID"] == sender_user_id:
                continue

            users.append(user)

        users.sort(key=lambda u: u["FullName"])

        return users
