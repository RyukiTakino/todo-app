from flask import Flask, render_template, request, redirect
import sqlite3
import os
from openai import OpenAI
app = Flask(__name__)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

connection = sqlite3.connect("todo.db")
connection.execute("""
CREATE TABLE IF NOT EXISTS todos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    completed INTEGER,
    minutes INTEGER
)
""")

connection.execute("""
CREATE TABLE IF NOT EXISTS schedules(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule TEXT)
""")
connection.close()

def get_db():
    connection = sqlite3.connect("todo.db")
    connection.row_factory = sqlite3.Row

    return connection

def add_minutes_column():
    connection = sqlite3.connect("todo.db")

    try:
        connection.execute(
            "ALTER TABLE todos ADD COLUMN minutes INTEGER"
        )
        connection.commit()
    except sqlite3.OperationalError:
        pass
    connection.close()

add_minutes_column()

@app.route("/hello")
def hello():    
    connection = get_db()
    todos = connection.execute(
        "SELECT * FROM todos"
    ).fetchall()
    connection.close()
    return render_template(
        "index.html",
          todolist=todos,
          schedule=""
    )

@app.route("/add")
def add():
    todo = request.args.get("todo")
    minutes = request.args.get("minutes")
    connection = get_db()
    connection.execute(
        "INSERT INTO todos (title, completed, minutes) VALUES (?, ?, ?)",
        (todo, 0, minutes)
    )
    connection.commit()
    connection.close()
    return redirect("/hello")

@app.route("/delete/<int:id>")
def delete(id):
    connection = get_db()
    connection.execute(
        "DELETE FROM todos WHERE id = ?",
        (id,)
    )
    connection.commit()
    connection.close()
    return redirect("/hello")

@app.route("/complete/<int:id>")
def complete(id):
    connection = get_db()
    connection.execute(
        "UPDATE todos SET completed = 1 WHERE id = ?",
        (id,)
    )
    connection.commit()
    connection.close()
    return redirect("/hello")

@app.route("/uncomplete/<int:id>")
def uncomplete(id):
    connection = get_db()
    connection.execute(
        "UPDATE todos SET completed = 0 WHERE id = ?",
        (id,)
    )
    connection.commit()
    connection.close()
    return redirect("/hello")

@app.route("/schedule")
def schedule():
    connection = get_db()

    todos = connection.execute(
        "SELECT * FROM todos"
    ).fetchall()

    todo_text = ""
    for todo in todos:
        todo_text += f"- {todo['title']}:{todo['minutes']}分\n"

    connection.close()

    prompt = f"""
    以下のTodoを1日のスケジュールにしてください。

    {todo_text}

    それぞれの必要時間を考慮して、
    無理のない順番で予定を作ってください。

    重要：
    書く予定は必ず１行ずつに分けて回答して下さい。
    一行で一つの予定を出力して下さい。
    以下のような形式で回答してください。

    9:00〜10:15 Pythonの勉強
    10:15〜10:30 休憩
    10:30〜11:00 英語の勉強

    各予定の間には必ず改行を入れてください。
    """
    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )

    connection = get_db()

    connection.execute(
        "DELETE FROM schedules"
    )

    schedule_text = response.output_text

    connection.execute(
        "INSERT INTO schedules (schedule) VALUES (?)",
        (schedule_text,)
    )

    connection.commit()
    connection.close()

    return render_template(
        "index.html",
        todolist=todos,
        schedule=response.output_text
    )

@app.route("/adjust_schedule")
def adjust_schedule():
    instruction = request.args.get("instruction")
    connection = get_db()
    schedule = connection.execute(
        "SELECT schedule FROM schedules"
    ).fetchone()
    current_schedule = schedule["schedule"]

    prompt = f"""
    {instruction}の指示に従って以下のスケジュールを修正して。
    {current_schedule}
    修正後のスケジュールだけを出力してください。
    """

    response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

    schedule_text = response.output_text
    connection.execute(
        "UPDATE schedules SET schedule = ?",
        (schedule_text,)
    )
    connection.commit()

    todos = connection.execute(
        "SELECT * FROM todos"
    ).fetchall()

    connection.close()

    return render_template(
            "index.html",
            todolist=todos,
            schedule=response.output_text
        )
    
