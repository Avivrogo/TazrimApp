import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime, date
from pathlib import Path

# ---------- קבועים ----------
EXPENSES_FILE = "expenses.csv"
SETTINGS_FILE = "settings.json"

# ---------- פונקציות עזר לקבצים ----------

def load_settings():
    """טוען את קובץ ההגדרות או יוצר אחד חדש"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        default_settings = {
            "categories": [],
            "fixed_expenses": []
        }
        save_settings(default_settings)
        return default_settings

def save_settings(settings):
    """שומר את ההגדרות לקובץ"""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def load_expenses():
    """טוען את קובץ ההוצאות או יוצר DataFrame ריק"""
    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE, encoding="utf-8")
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        return df
    else:
        df = pd.DataFrame(columns=["date", "amount", "payment_method", "category", "description", "is_fixed"])
        df.to_csv(EXPENSES_FILE, index=False, encoding="utf-8")
        return df

def save_expense(expense_data):
    file_path = 'expenses.csv'
    
    # וידוא שהתאריך הוא מחרוזת בפורמט תקין (YYYY-MM-DD)
    if isinstance(expense_data.get('date'), datetime):
        expense_data['date'] = expense_data['date'].strftime("%Y-%m-%d")
    elif not expense_data.get('date'):
        expense_data['date'] = datetime.now().strftime("%Y-%m-%d")
        
    df_new = pd.DataFrame([expense_data])
    
    if os.path.exists(file_path):
        try:
            df_existing = pd.read_csv(file_path)
            # מנקה שורות ריקות אם יש
            df_existing = df_existing.dropna(how='all')
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
        except:
            df_final = df_new
    else:
        df_final = df_new
        
    df_final.to_csv(file_path, index=False, encoding='utf-8-sig')

def delete_expense(index_to_delete):
    """מוחק הוצאה לפי האינדקס שלה בקובץ ה-CSV"""
    if os.path.exists('expenses.csv'):
        df = pd.read_csv('expenses.csv')
        # מחיקת השורה הספציפית
        df = df.drop(index_to_delete)
        # שמירה מחדש של הקובץ
        df.to_csv('expenses.csv', index=False, encoding='utf-8-sig')
        return True
    return False

def remove_fixed_setting(index):
    settings = load_settings()
    if "fixed_expenses" in settings:
        settings["fixed_expenses"].pop(index)
        save_settings(settings)

def clean_fixed_from_current_month(description):
    if os.path.exists('expenses.csv'):
        df = pd.read_csv('expenses.csv')
        df['date'] = pd.to_datetime(df['date'])
        now = datetime.now()
        
        fixed_id = f"[קבוע] {description}"
        
        # יוצרים מסנן: כל מה שהוא לא ההוצאה הזו בחודש הזה - נשאר
        mask = ~(
            (df['description'] == fixed_id) & 
            (df['date'].dt.month == now.month) & 
            (df['date'].dt.year == now.year)
        )
        
        df_cleaned = df[mask]
        df_cleaned.to_csv('expenses.csv', index=False, encoding='utf-8-sig')

def add_fixed_to_current_month_if_missing(fixed_expense):
    df = load_expenses()
    current_month, current_year = datetime.now().month, datetime.now().year
    desc_id = f"[קבוע] {fixed_expense['description']}"
    
    exists = False
    if not df.empty:
        # וידוא שהתאריכים נקראים נכון לצורך ההשוואה
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        # בדיקה האם יש כבר הוצאה עם אותו תיאור בחודש הנוכחי
        exists = not df[
            (df["description"] == desc_id) & 
            (df["date"].dt.month == current_month) & 
            (df["date"].dt.year == current_year)
        ].empty

    if not exists:
        expense_data = {
            "date": date(current_year, current_month, 1).strftime("%Y-%m-%d"),
            "amount": fixed_expense["amount"],
            "payment_method": fixed_expense["payment_method"],
            "category": fixed_expense["category"],
            "description": desc_id,
            "is_fixed": True,
        }
        save_expense(expense_data)
        
def inject_fixed_expenses():
    settings = load_settings()
    fixed_expenses = settings.get("fixed_expenses", [])
    if not fixed_expenses: return

    df = load_expenses()
    now = datetime.now()
    
    # 1. זיהוי הוצאות קבועות שכבר קיימות החודש
    existing_descriptions = []
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        mask = (df['date'].dt.month == now.month) & (df['date'].dt.year == now.year) & (df['is_fixed'] == True)
        existing_descriptions = df[mask]['description'].tolist()

    # 2. סינון רק של אלו שבאמת חסרות
    to_add = []
    first_of_month = now.strftime("%Y-%m-%d") # מקבעים לראשון לחודש הנוכחי
    
    for fixed in fixed_expenses:
        fixed_id = f"[קבוע] {fixed['description']}"
        if fixed_id not in existing_descriptions:
            to_add.append({
                "date": first_of_month,
                "amount": fixed["amount"],
                "payment_method": fixed["payment_method"],
                "category": fixed["category"],
                "description": fixed_id,
                "is_fixed": True
            })

    # 3. שמירה מרוכזת (חוסך המון זמן ריצה)
    if to_add:
        for item in to_add:
            save_expense(item)

def inject_custom_css():
    st.markdown("""
    <style>
    /* כיוון RTL */
    .stApp {
        direction: rtl;
    }
    
    /* גופן וצבעים כלליים */
    @import url('[fonts.googleapis.com](https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700&display=swap)');
    
    html, body, [class*="css"] {
        font-family: 'Heebo', sans-serif;
    }
    
    /* כפתורים גדולים */
    .big-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        padding: 25px 20px;
        border-radius: 16px;
        border: none;
        font-size: 1.3rem;
        font-weight: 600;
        width: 100%;
        margin: 8px 0;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: transform 0.2s, box-shadow 0.2s;
        text-align: center;
        display: block;
    }
    
    .big-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    .big-button-secondary {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .big-button-warning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .big-button-info {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    /* כפתורי מקלדת מספרית */
    .numpad-btn {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 12px;
        padding: 20px;
        font-size: 1.8rem;
        font-weight: 600;
        color: #495057;
        cursor: pointer;
        transition: all 0.15s;
        width: 100%;
        min-height: 70px;
    }
    
    .numpad-btn:hover {
        background: #e9ecef;
        border-color: #667eea;
    }
    
    .numpad-btn:active {
        transform: scale(0.95);
    }
    
    /* תצוגת סכום */
    .amount-display {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 20px 0;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* כרטיס */
    .card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin: 10px 0;
    }
    
    /* כותרות */
    .page-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2d3748;
        text-align: center;
        margin: 20px 0;
    }
    
    .step-indicator {
        background: #e9ecef;
        color: #495057;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* כפתור חזרה */
    .back-btn {
        background: #f8f9fa;
        border: none;
        padding: 10px 20px;
        border-radius: 10px;
        cursor: pointer;
        font-size: 1rem;
        color: #495057;
    }
    
    /* אנימציה */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-in {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* התאמת Streamlit */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        padding: 15px 20px;
        font-size: 1.1rem;
        font-weight: 500;
        border: none;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
    }
    
    /* הסתרת אלמנטים מיותרים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* רווחים */
    .spacer {
        height: 20px;
    }
    
    /* הודעת אזהרה */
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        color: #856404;
    }
    
    /* פריט ברשימה */
    .list-item {
        background: white;
        border-radius: 12px;
        padding: 15px;
        margin: 8px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------- אתחול Session State ----------

def init_session_state():
    defaults = {
        "current_screen": "main",
        "add_expense_step": 1,
        "expense_data": {},
        "amount_input": "",
        "add_fixed_step": 1,
        "fixed_data": {},
        "fixed_amount_input": ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_expense_flow():
    st.session_state.add_expense_step = 1
    st.session_state.expense_data = {}
    st.session_state.amount_input = ""

def reset_fixed_flow():
    st.session_state.add_fixed_step = 1
    st.session_state.fixed_data = {}
    st.session_state.fixed_amount_input = ""

# ---------- מסכים ----------
def render_main_screen():
    """מסך ראשי - גרסה נקייה ללא טבלה"""
    settings = load_settings()
    categories = settings.get("categories", [])
    
    st.markdown('<div class="page-title">💰 מעקב הוצאות</div>', unsafe_allow_html=True)
    
    # טעינת נתונים רק לצורך התצוגה של העוגה והסכום
    df = load_expenses()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        current_month = datetime.now().month
        current_year = datetime.now().year
        df_month = df[(df["date"].dt.month == current_month) & (df["date"].dt.year == current_year)].copy()
        
        if not df_month.empty:
            # תצוגת סכום כולל
            total = df_month["amount"].sum()
            st.markdown(f'<div class="amount-display">₪{total:,.2f}<br><small>סה"כ החודש</small></div>', unsafe_allow_html=True)
            
            # תרשים עוגה
            by_category = df_month.groupby("category")["amount"].sum().reset_index()
            fig = px.pie(by_category, values="amount", names="category", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                              margin=dict(t=20, b=20, l=20, r=20), font=dict(family="Heebo"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("אין הוצאות החודש")
    else:
        st.info("אין הוצאות עדיין")
    
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
    
    # כפתורי ניווט בלבד
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ הוספת הוצאה חדשה", key="btn_add", use_container_width=True, type="primary"):
            reset_expense_flow()
            st.session_state.current_screen = "add_expense"
            st.rerun()
    with col2:
        if st.button("📊 פירוט חודשי", key="btn_monthly", use_container_width=True):
            st.session_state.current_screen = "monthly_details"
            st.rerun()
            
    col3, col4 = st.columns(2)
    with col3:
        if st.button("⚙️ עוד", key="btn_more", use_container_width=True):
            st.session_state.current_screen = "more_menu"
            st.rerun()

def render_add_expense():
    """מסך הוספת הוצאה - רב שלבי"""
    settings = load_settings()
    categories = settings.get("categories", [])
    step = st.session_state.add_expense_step
    
    # כפתור חזרה
    if st.button("→ חזרה", key="back_add"):
        if step > 1:
            st.session_state.add_expense_step -= 1
            st.rerun()
        else:
            st.session_state.current_screen = "main"
            reset_expense_flow()
            st.rerun()
    
    st.markdown(f'<div class="step-indicator">שלב {step} מתוך 5</div>', unsafe_allow_html=True)
    st.progress(step / 5)
    
    if step == 1:
        # שלב 1: תאריך
        st.markdown('<div class="page-title">📅 בחר תאריך</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("היום", key="date_today", use_container_width=True, type="primary"):
                st.session_state.expense_data["date"] = date.today()
                st.session_state.add_expense_step = 2
                st.rerun()
        
        with col2:
            if st.button("תאריך אחר", key="date_other", use_container_width=True):
                st.session_state.show_date_picker = True
        
        if st.session_state.get("show_date_picker", False):
            selected_date = st.date_input("בחר תאריך:", value=date.today(), key="date_picker")
            if st.button("אישור תאריך", key="confirm_date", type="primary"):
                st.session_state.expense_data["date"] = selected_date
                st.session_state.show_date_picker = False
                st.session_state.add_expense_step = 2
                st.rerun()
    
    elif step == 2:
        # שלב 2: סכום עם מקלדת מספרית
        st.markdown('<div class="page-title">💵 הזן סכום</div>', unsafe_allow_html=True)
        
        amount_str = st.session_state.amount_input
        display_amount = amount_str if amount_str else "0"
        st.markdown(f'<div class="amount-display">₪{display_amount}</div>', unsafe_allow_html=True)
        
        # מקלדת מספרית
        for row in [["7", "8", "9"], ["4", "5", "6"], ["1", "2", "3"], [".", "0", "⌫"]]:
            cols = st.columns(3)
            for i, num in enumerate(row):
                with cols[i]:
                    if st.button(num, key=f"num_{num}", use_container_width=True):
                        if num == "⌫":
                            st.session_state.amount_input = amount_str[:-1]
                        elif num == ".":
                            if "." not in amount_str:
                                st.session_state.amount_input = amount_str + "."
                        else:
                            st.session_state.amount_input = amount_str + num
                        st.rerun()
        
        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        
        if st.button("המשך ←", key="confirm_amount", use_container_width=True, type="primary"):
            if amount_str and float(amount_str) > 0:
                st.session_state.expense_data["amount"] = float(amount_str)
                st.session_state.add_expense_step = 3
                st.rerun()
            else:
                st.error("יש להזין סכום תקין")
    
    elif step == 3:
        # שלב 3: אמצעי תשלום
        st.markdown('<div class="page-title">💳 אמצעי תשלום</div>', unsafe_allow_html=True)
        
        payment_methods = [
            ("מזומן", "💵"),
            ("אשראי", "💳"),
            ("ביט", "📱"),
            ("ספליט", "👥")
        ]
        
        col1, col2 = st.columns(2)
        for i, (method, icon) in enumerate(payment_methods):
            with col1 if i % 2 == 0 else col2:
                if st.button(f"{icon} {method}", key=f"pay_{method}", use_container_width=True):
                    st.session_state.expense_data["payment_method"] = method
                    st.session_state.add_expense_step = 4
                    st.rerun()
    
    elif step == 4:
        # שלב 4: קטגוריה
        st.markdown('<div class="page-title">📁 בחר קטגוריה</div>', unsafe_allow_html=True)
        
        selected_category = st.selectbox(
            "קטגוריה:",
            options=categories,
            key="category_select"
        )
        
        if st.button("המשך ←", key="confirm_category", use_container_width=True, type="primary"):
            st.session_state.expense_data["category"] = selected_category
            st.session_state.add_expense_step = 5
            st.rerun()
    
    elif step == 5:
        # שלב 5: תיאור ושמירה
        st.markdown('<div class="page-title">📝 תיאור (אופציונלי)</div>', unsafe_allow_html=True)
        
        description = st.text_area("הוסף תיאור:", key="description_input", height=100)
        
        # סיכום
        st.markdown("---")
        st.markdown("### סיכום ההוצאה:")
        data = st.session_state.expense_data
        
        # התיקון הקריטי: לוקחים את התאריך שנבחר בשלב 1
        # אם זה אובייקט date של פייתון, נמיר אותו לטקסט לצורך תצוגה ושמירה
        raw_date = data.get('date', date.today())
        if hasattr(raw_date, 'strftime'):
            formatted_date = raw_date.strftime("%Y-%m-%d")
        else:
            formatted_date = str(raw_date)
        
        st.write(f"📅 תאריך: {formatted_date}")
        st.write(f"💵 סכום: ₪{data.get('amount', 0):,.2f}")
        st.write(f"💳 תשלום: {data.get('payment_method', '')}")
        st.write(f"📁 קטגוריה: {data.get('category', '')}")
        
        if st.button("💾 שמור הוצאה", key="save_expense", use_container_width=True, type="primary"):
            expense_data = {
                "date": formatted_date, # משתמשים בתאריך שחולץ מה-session_state
                "amount": data["amount"],
                "payment_method": data["payment_method"],
                "category": data["category"],
                "description": description if description else "",
                "is_fixed": False
            }
            save_expense(expense_data)
            st.success("ההוצאה נשמרה בהצלחה! ✅")
            reset_expense_flow()
            st.session_state.current_screen = "main"
            st.rerun()

def render_monthly_details():
    st.markdown('<div class="page-title">📊 פירוט הוצאות חודשי</div>', unsafe_allow_html=True)
    
    if st.button("⬅️ חזרה למסך ראשי", key="back_from_details"):
        st.session_state.current_screen = "main"
        st.rerun()
        
    df = load_expenses()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        now = datetime.now()
        mask = (df['date'].dt.month == now.month) & (df['date'].dt.year == now.year)
        df_month = df[mask].sort_values(by='date', ascending=True).copy()
        
        if not df_month.empty:
            # כותרות ל"טבלה" החדשה שלנו
            cols = st.columns([1.5, 2.5, 1.5, 1.5, 0.5]) # העמודה האחרונה היא לאיקס
            cols[0].write("**תאריך**")
            cols[1].write("**תיאור**")
            cols[2].write("**קטגוריה**")
            cols[3].write("**סכום**")
            cols[4].write("") # עמודת המחיקה
            
            st.markdown("---")
            
            # מעבר על כל שורה בנפרד
            for idx, row in df_month.iterrows():
                c1, c2, c3, c4, c5 = st.columns([1.5, 2.5, 1.5, 1.5, 0.5])
                
                c1.write(row['date'].strftime('%d/%m/%Y'))
                c2.write(row['description'])
                c3.write(row['category'])
                c4.write(f"₪{row['amount']:,.2f}")
                
                # בדיקה: האם זו הוצאה רגילה? (לא קבועה)
                if not row.get('is_fixed', False):
                    # יצירת כפתור מחיקה עם פופאפ אישור
                    with c5:
                        with st.popover("❌"):
                            st.write(f"למחוק את '{row['description']}'?")
                            if st.button("כן, מחק", key=f"del_{idx}", type="primary", use_container_width=True):
                                if delete_expense(idx):
                                    st.success("נמחק!")
                                    st.rerun()
                else:
                    # הוצאה קבועה - משאירים ריק או שמים אייקון מנעול קטן
                    c5.write("🔒")
        else:
            st.info("אין הוצאות לחודש הנוכחי.")
    else:
        st.info("אין נתונים עדיין.")

def render_more_menu():
    """תפריט עוד"""
    if st.button("→ חזרה", key="back_more"):
        st.session_state.current_screen = "main"
        st.rerun()
    
    st.markdown('<div class="page-title">⚙️ הגדרות נוספות</div>', unsafe_allow_html=True)
    
    settings = load_settings()
    categories = settings.get("categories", [])
    
    # הוספת קטגוריה
    st.markdown("### 📁 הוספת קטגוריה")
    new_category = st.text_input("שם הקטגוריה:", key="new_category")
    if st.button("הוסף קטגוריה", key="add_category", type="primary"):
        if new_category and new_category not in categories:
            settings["categories"].append(new_category)
            save_settings(settings)
            st.success(f"הקטגוריה '{new_category}' נוספה! ✅")
            st.rerun()
        elif new_category in categories:
            st.error("קטגוריה זו כבר קיימת")
        else:
            st.error("יש להזין שם קטגוריה")
    
    st.markdown("---")
    
    # הוספת הוצאה קבועה
    st.markdown("### 🔄 הוספת הוצאה קבועה")
    if not categories:
        st.warning("יש להוסיף קטגוריה ראשונה לפני הוספת הוצאה קבועה")
    else:
        if st.button("➕ הוסף הוצאה קבועה", key="btn_add_fixed"):
            reset_fixed_flow()
            st.session_state.current_screen = "add_fixed"
            st.rerun()
    
    st.markdown("---")
    
    # ניהול הוצאות קבועות
    st.markdown("### 📋 הוצאות קבועות קיימות")
    fixed_expenses = settings.get("fixed_expenses", [])
    
    if not fixed_expenses:
        st.info("אין הוצאות קבועות")
    else:
        # בתוך הלולאה שמציגה את ההוצאות הקבועות במסך "עוד"
        for i, fixed in enumerate(fixed_expenses):
            col1, col2 = st.columns([4, 1])
            col1.write(f"📌 {fixed['description']} (₪{fixed['amount']})")
            
            with col2:
                with st.popover("🗑️"):
                    st.warning("איך תרצה למחוק?")
                    
                    # אופציה 1: רק מהעתיד
                    if st.button("רק מהחודשים הבאים", key=f"future_{i}"):
                        remove_fixed_setting(i) # פונקציה שמוחקת רק מהגדרות
                        st.success("ההגדרה הוסרה. לא תופיע בחודש הבא.")
                        st.rerun()
                        
                    # אופציה 2: ניקוי כללי
                    if st.button("גם מהחודש הנוכחי", key=f"total_{i}", type="primary"):
                        # 1. מחיקה מההגדרות
                        desc_to_clean = fixed['description']
                        remove_fixed_setting(i)
                        
                        # 2. מחיקה מה-CSV של החודש הזה
                        clean_fixed_from_current_month(desc_to_clean)
                        
                        st.success(f"ההוצאה '{desc_to_clean}' נמחקה לגמרי!")
                        st.rerun()
    
    st.markdown("---")
    
    # צפייה בחודשים קודמים
    st.markdown("### 📆 צפייה בחודשים קודמים")
    df = load_expenses()
    
    if not df.empty:
        df["month_year"] = df["date"].dt.to_period("M")
        months = df["month_year"].unique()
        month_options = [str(m) for m in sorted(months, reverse=True)]
        
        if month_options:
            selected_month = st.selectbox("בחר חודש:", month_options, key="past_month")
            
            if selected_month:
                df_selected = df[df["month_year"].astype(str) == selected_month]
                total = df_selected["amount"].sum()
                st.write(f"**סה\"כ:** ₪{total:,.2f}")
                
                display_df = df_selected[["date", "amount", "payment_method", "category", "description"]].copy()
                display_df["date"] = display_df["date"].dt.strftime("%d/%m/%Y")
                display_df["amount"] = display_df["amount"].apply(lambda x: f"₪{x:,.2f}")
                display_df.columns = ["תאריך", "סכום", "תשלום", "קטגוריה", "תיאור"]
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("אין היסטוריה להצגה")

def render_add_fixed():
    """מסך הוספת הוצאה קבועה"""
    settings = load_settings()
    categories = settings.get("categories", [])
    step = st.session_state.add_fixed_step
    
    if st.button("→ חזרה", key="back_fixed"):
        if step > 1:
            st.session_state.add_fixed_step -= 1
            st.rerun()
        else:
            st.session_state.current_screen = "more_menu"
            reset_fixed_flow()
            st.rerun()

    st.markdown(f"### שלב {step} מתוך 4")
    st.progress(step / 4)

    if step == 1:
        # --- שלב הסכום ---
        st.markdown("#### סכום חודשי קבוע")
        amount_str = st.session_state.fixed_amount_input
        display_amt = amount_str if amount_str else "0"
        st.markdown(f"<h2 style='text-align: center;'>₪{display_amt}</h2>", unsafe_allow_html=True)

        for row in [["7", "8", "9"], ["4", "5", "6"], ["1", "2", "3"], [".", "0", "⌫"]]:
            cols = st.columns(3)
            for i, num in enumerate(row):
                with cols[i]:
                    if st.button(num, key=f"fnum_{num}"):
                        if num == "⌫":
                            st.session_state.fixed_amount_input = amount_str[:-1]
                        elif num == ".":
                            if "." not in amount_str:
                                st.session_state.fixed_amount_input += "."
                        else:
                            st.session_state.fixed_amount_input += num
                        st.rerun()

        if st.button("המשך ←", key="confirm_fixed_amount"):
            if amount_str and float(amount_str) > 0:
                st.session_state.fixed_data["amount"] = float(amount_str)
                st.session_state.add_fixed_step = 2
                st.rerun()
            else:
                st.error("יש להזין סכום תקין")

    elif step == 2:
        # --- שלב אמצעי תשלום ---
        st.markdown("#### בחר אמצעי תשלום")
        for method, icon in [("מזומן", "💵"), ("אשראי", "💳"), ("ביט", "📱"), ("ספליט", "👥")]:
            if st.button(f"{icon} {method}", key=f"fpay_{method}"):
                st.session_state.fixed_data["payment_method"] = method
                st.session_state.add_fixed_step = 3
                st.rerun()

    elif step == 3:
        # --- שלב קטגוריה ---
        st.markdown("#### בחר קטגוריה")
        selected_category = st.selectbox("קטגוריה:", options=categories)
        if st.button("המשך ←", key="confirm_fixed_category"):
            st.session_state.fixed_data["category"] = selected_category
            st.session_state.add_fixed_step = 4
            st.rerun()

    elif step == 4:
        # --- שלב תיאור ושמירה סופית ---
        st.markdown("#### תיאור ואישור")
        description = st.text_input("תיאור ההוצאה (למשל: שכר דירה):")
        data = st.session_state.fixed_data
        
        st.info(f"פרטי ההוצאה: ₪{data.get('amount')} ב{data.get('payment_method')} (קטגוריה: {data.get('category')})")

        if st.button("💾 שמור הוצאה קבועה", key="save_fixed"):
            if description:
                fixed_expense = {
                    "amount": data["amount"],
                    "payment_method": data["payment_method"],
                    "category": data["category"],
                    "description": description,
                }

                # 1. שמירה להגדרות (עבור חודשים עתידיים)
                if "fixed_expenses" not in settings:
                    settings["fixed_expenses"] = []
                settings["fixed_expenses"].append(fixed_expense)
                save_settings(settings)

                # 2. הזרקה מיידית לחודש הנוכחי (הפונקציה שהוספנו קודם)
                add_fixed_to_current_month_if_missing(fixed_expense)

                st.success("ההוצאה הקבועה נשמרה וסונכרנה לתזרים הנוכחי! ✅")
                
                # איפוס וחזרה למסך הראשי
                reset_fixed_flow()
                st.session_state.current_screen = "main"
                st.rerun()
            else:
                st.error("חובה להזין תיאור")

# ---------- Main ----------

def main():
    st.set_page_config(
        page_title="מעקב הוצאות",
        page_icon="💰",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    inject_custom_css()
    init_session_state()
    
    # הזרקת הוצאות קבועות בתחילת חודש
    inject_fixed_expenses()
    
    # ניתוב מסכים
    screen = st.session_state.current_screen
    
    if screen == "main":
        render_main_screen()
    elif screen == "add_expense":
        render_add_expense()
    elif screen == "monthly_details":
        render_monthly_details()
    elif screen == "more_menu":
        render_more_menu()
    elif screen == "add_fixed":
        render_add_fixed()

if __name__ == "__main__":
    main()
