import os
import sqlite3
from openai import OpenAI

connection = sqlite3.connect("todo.db")

todos = connection.execute(
    "SELECT * FROM todos"
).fetchall()

print(todos)

api_key = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=api_key)

todo_text = ""

for todo in todos:
    todo_text += f"- {todo[1]} : {todo[3]}分\n"

prompt = f"""
以下のTodoを1日のスケジュールにしてください。

{todo_text}

それぞれの必要時間を考慮して、
無理のない順番で予定を作ってください。
"""

response = client.responses.create(
    model="gpt-5.6-luna",
    input=prompt
)

print(response.output_text)