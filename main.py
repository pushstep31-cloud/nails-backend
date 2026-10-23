from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "schedule.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Таблица для смен
    c.execute('''CREATE TABLE IF NOT EXISTS shifts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  master TEXT, date TEXT, start TEXT, end TEXT, comment TEXT)''')
    
    # Таблица для пользователей (мастеров)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT UNIQUE, password TEXT)''')
    
    # Создаем дефолтных пользователей, если их еще нет
    c.execute("SELECT count(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (name, password) VALUES ('Диана', '1111')")
        c.execute("INSERT INTO users (name, password) VALUES ('Настя', '2222')")
        
    conn.commit()
    conn.close()

init_db()

class Shift(BaseModel):
    master: str
    date: str
    start: str
    end: str
    comment: str

class UserUpdate(BaseModel):
    old_name: str
    new_name: str
    new_password: str

# --- СМЕНЫ ---
@app.get("/shifts")
def get_shifts():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, master, date, start, end, comment FROM shifts")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "master": r[1], "date": r[2], "start": r[3], "end": r[4], "comment": r[5]} for r in rows]

@app.post("/shifts")
def add_shift(shift: Shift):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT master, start, end FROM shifts WHERE date=? AND ((start < ? AND end > ?) OR (start < ? AND end > ?))", 
              (shift.date, shift.end, shift.start, shift.end, shift.start))
    overlap = c.fetchone()
    if overlap:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Пересечение! {overlap[0]} уже работает с {overlap[1]} до {overlap[2]}")

    c.execute("INSERT INTO shifts (master, date, start, end, comment) VALUES (?,?,?,?,?)",
              (shift.master, shift.date, shift.start, shift.end, shift.comment))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.put("/shifts/{shift_id}")
def update_shift(shift_id: int, shift: Shift):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT master, start, end FROM shifts WHERE date=? AND id!=? AND ((start < ? AND end > ?) OR (start < ? AND end > ?))", 
              (shift.date, shift_id, shift.end, shift.start, shift.end, shift.start))
    overlap = c.fetchone()
    if overlap:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Пересечение! {overlap[0]} уже работает с {overlap[1]} до {overlap[2]}")

    c.execute("UPDATE shifts SET date=?, start=?, end=?, comment=? WHERE id=?",
              (shift.date, shift.start, shift.end, shift.comment, shift_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/shifts/{shift_id}")
def delete_shift(shift_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM shifts WHERE id=?", (shift_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# --- ПОЛЬЗОВАТЕЛИ ---
@app.get("/users")
def get_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name FROM users")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1]} for r in rows]

@app.post("/login")
def login(user: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE name=? AND password=?", (user.get("name"), user.get("password")))
    row = c.fetchone()
    conn.close()
    if row:
        return {"status": "ok", "name": row[0]}
    raise HTTPException(status_code=401, detail="Неверный пароль")

@app.put("/users")
def update_user(data: UserUpdate):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Проверяем, существует ли пользователь
    c.execute("SELECT id FROM users WHERE name=?", (data.old_name,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Пользователь не найден")
        
    # Проверяем, не занято ли новое имя другим мастером
    c.execute("SELECT id FROM users WHERE name=? AND name!=?", (data.new_name, data.old_name))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Это имя уже занято другим мастером")

    # Обновляем имя
    c.execute("UPDATE users SET name=? WHERE name=?", (data.new_name, data.old_name))
    
    # Обновляем пароль, если он был введен
    if data.new_password.strip():
        c.execute("UPDATE users SET password=? WHERE name=?", (data.new_password, data.new_name))
        
    # Обновляем имя во всех сменах этого мастера
    c.execute("UPDATE shifts SET master=? WHERE master=?", (data.new_name, data.old_name))
    
    conn.commit()
    conn.close()
    return {"status": "ok", "new_name": data.new_name}
