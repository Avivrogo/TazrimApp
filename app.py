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

def render_add_expense():
    """תהליך הוספת הוצאה מלא - סכום ואז פרטים"""
    
    # שלב 1: הזנת סכום (המקלדת הנומרית)
    if st.session_state.expense_flow_step == "amount":
        st.markdown('<div class="page-title">💰 הזן סכום</div>', unsafe_allow_html=True)
        
        display_val = st.session_state.temp_amount if st.session_state.temp_amount else "0"
        st.markdown(f'<div class="amount-display">₪{display_val}</div>', unsafe_allow_html=True)
        
        # בניית המקלדת ב-3 עמודות
        keys = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['.', '0', '⌫']
        ]
        
        for row in keys:
            cols = st.columns(3)
            for i, key in enumerate(row):
                with cols[i]:
                    if st.button(key, key=f"btn_{key}_{row[0]}", use_container_width=True):
                        if key == '⌫':
                            st.session_state.temp_amount = st.session_state.temp_amount[:-1]
                        elif key == '.':
                            # הגבלה: נקודה אחת בלבד
                            if '.' not in st.session_state.temp_amount:
                                st.session_state.temp_amount += '.'
                        else:
                            # הגבלה: מקסימום 2 ספרות אחרי הנקודה
                            if '.' in st.session_state.temp_amount:
                                if len(st.session_state.temp_amount.split('.')[1]) < 2:
                                    st.session_state.temp_amount += key
                            else:
                                st.session_state.temp_amount += key
                        st.rerun()
        
        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        
        col_next, col_cancel = st.columns(2)
        with col_next:
            if st.button("המשך לפרטים ←", type="primary", use_container_width=True):
                if st.session_state.temp_amount and float(st.session_state.temp_amount) > 0:
                    st.session_state.expense_flow_step = "details"
                    st.rerun()
                else:
                    st.error("הזן סכום תקין")
        with col_cancel:
            if st.button("ביטול", use_container_width=True):
                reset_expense_flow()
                st.session_state.current_screen = "main"
                st.rerun()

    # שלב 2: הזנת פרטים (תיאור, קטגוריה, אמצעי תשלום)
    elif st.session_state.expense_flow_step == "details":
        st.markdown('<div class="page-title">📝 פרטי ההוצאה</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center; font-size:1.5rem; margin-bottom:1rem;">סכום: ₪{st.session_state.temp_amount}</div>', unsafe_allow_html=True)
        
        settings = load_settings()
        categories = settings.get("categories", ["כללי"])
        payment_methods = ["אשראי", "מזומן", "ביט", "העברה", "אחר"]
        
        description = st.text_input("תיאור ההוצאה:", placeholder="מה קנית?")
        category = st.selectbox("קטגוריה:", categories)
        payment_method = st.selectbox("אמצעי תשלום:", payment_methods)
        expense_date = st.date_input("תאריך:", datetime.now())
        
        col_save, col_back = st.columns(2)
        with col_save:
            if st.button("✅ שמירה", type="primary", use_container_width=True):
                if description:
                    new_expense = {
                        "date": expense_date.strftime("%Y-%m-%d"),
                        "amount": float(st.session_state.temp_amount),
                        "category": category,
                        "description": description,
                        "payment_method": payment_method,
                        "is_fixed": False
                    }
                    save_expense(new_expense)
                    st.success("ההוצאה נשמרה!")
                    reset_expense_flow()
                    st.session_state.current_screen = "main"
                    st.rerun()
                else:
                    st.error("חובה להזין תיאור")
                    
        with col_back:
            if st.button("חזור לסכום", use_container_width=True):
                st.session_state.expense_flow_step = "amount"
                st.rerun()

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
