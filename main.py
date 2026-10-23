from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List, Optional

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
    c.execute('''CREATE TABLE IF NOT EXISTS shifts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  master TEXT, date TEXT, start TEXT, end TEXT, comment TEXT)''')
    conn.commit()
    conn.close()

init_db()

class Shift(BaseModel):
    master: str
    date: str
    start: str
    end: str
    comment: str

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

@app.delete("/shifts/{shift_id}")
def delete_shift(shift_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM shifts WHERE id=?", (shift_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}
