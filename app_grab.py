import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime, date
from pathlib import Path

# ---------- קבועים והגדרות ----------
EXPENSES_FILE = "expenses.csv"
SETTINGS_FILE = "settings.json"

# פונקציה להזרקת CSS לעיצוב RTL ומובייל
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Assistant', sans-serif; direction: RTL; text-align: right; }
    .stButton > button { width: 100%; border-radius: 10px; height: 3em; background-color: #ff4b4b; color: white; border: none; font-weight: bold; margin-bottom: 10px; }
    .main-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ---------- פונקציות נתונים ----------

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    settings = {"categories": [], "fixed_expenses": []}
    save_settings(settings)
    return settings

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def load_expenses():
    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE, encoding="utf-8")
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        return df
    return pd.DataFrame(columns=["date", "amount", "payment_method", "category", "description", "is_fixed"])

def save_expense(expense_data):
    df = load_expenses()
    new_row = pd.DataFrame([expense_data])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(EXPENSES_FILE, index=False, encoding="utf-8")

def inject_fixed_expenses():
    settings = load_settings()
    fixed_expenses = settings.get("fixed_expenses", [])
    if not fixed_expenses: return
    
    df = load_expenses()
    current_month, current_year = datetime.now().month, datetime.now().year
    
    for fixed in fixed_expenses:
        desc_id = f"[קבוע] {fixed['description']}"
        exists = not df.empty and not df[(df["description"] == desc_id) & 
                                       (df["date"].dt.month == current_month) & 
                                       (df["date"].dt.year == current_year)].empty
        if not exists:
            add_fixed_to_current_month_if_missing(fixed)

def add_fixed_to_current_month_if_missing(fixed_expense):
    desc_id = f"[קבוע] {fixed_expense['description']}"
    expense_data = {
        "date": date(datetime.now().year, datetime.now().month, 1),
        "amount": fixed_expense["amount"],
        "payment_method": fixed_expense["payment_method"],
        "category": fixed_expense["category"],
        "description": desc_id,
        "is_fixed": True,
    }
    save_expense(expense_data)

# ---------- פונקציות רינדור מסכים ----------

def render_main_screen():
    local_css()
    df = load_expenses()
    current_month = datetime.now().month
    df_month = df[df["date"].dt.month == current_month] if not df.empty else df
    
    total = df_month["amount"].sum() if not df_month.empty else 0
    st.markdown(f'<div class="main-card"><h1>₪{total:,.2f}</h1><p>סה"כ החודש</p></div>', unsafe_allow_html=True)
    
    if not df_month.empty:
        fig = px.pie(df_month, values='amount', names='category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ הוספת הוצאה"):
            st.session_state.current_screen = "add_expense"
            st.rerun()
    with col2:
        if st.button("📊 פירוט חודשי"):
            st.session_state.current_screen = "monthly_details"
            st.rerun()
    
    if st.button("⚙️ עוד"):
        st.session_state.current_screen = "more_menu"
        st.rerun()

def render_more_menu():
    st.title("הגדרות ואפשרויות")
    if st.button("🔄 הוספת הוצאה קבועה"):
        st.session_state.current_screen = "add_fixed"
        st.rerun()
    
    settings = load_settings()
    new_cat = st.text_input("הוסף קטגוריה חדשה:")
    if st.button("שמור קטגוריה"):
        if new_cat and new_cat not in settings["categories"]:
            settings["categories"].append(new_cat)
            save_settings(settings)
            st.success(f"קטגוריה '{new_cat}' נוספה!")
            
    if st.button("🏠 חזרה לבית"):
        st.session_state.current_screen = "main"
        st.rerun()

# --- פונקציות הוספה (מקוצרות לצורך היציבות) ---
def render_add_expense():
    st.title("הוספת הוצאה")
    # כאן יבוא המשך הלוגיקה של הצעדים (Steps) שתיארת
    if st.button("ביטול"):
        st.session_state.current_screen = "main"
        st.rerun()

# פונקציות ה-Session State
def init_session_state():
    if "current_screen" not in st.session_state: st.session_state.current_screen = "main"
    if "add_fixed_step" not in st.session_state: st.session_state.add_fixed_step = 1
    if "fixed_data" not in st.session_state: st.session_state.fixed_data = {}
    if "fixed_amount_input" not in st.session_state: st.session_state.fixed_amount_input = ""

def main():
    st.set_page_config(page_title="מעקב הוצאות", page_icon="💰")
    init_session_state()
    inject_fixed_expenses()
    
    s = st.session_state.current_screen
    if s == "main": render_main_screen()
    elif s == "more_menu": render_more_menu()
    elif s == "add_fixed": # כאן תשתמש בפונקציה ששלחת לי קודם
        from __main__ import render_add_fixed
        render_add_fixed()
    else: st.write(f"מסך {s} בבנייה...")

if __name__ == "__main__":
    main()