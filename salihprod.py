import streamlit as st
import pandas as pd
import io
import random
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# Настройки страницы
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SmartSchedule PL — Панель Управления",
    layout="wide",
    page_icon="🗓️",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Данные по умолчанию и инициализация session_state
# ─────────────────────────────────────────────

DEFAULT_SUBJECTS = [
    {"Дисциплина": "Основы программирования", "Часы (Типовой план на 2 года)": 240, "Преподаватель": "Асанов А.А.", "Аудитория": "204"},
    {"Дисциплина": "Произв. обучение (в сетке)", "Часы (Типовой план на 2 года)": 420, "Преподаватель": "Иванов И.И.", "Аудитория": "Мастерская 1"},
    {"Дисциплина": "Кыргызский язык", "Часы (Типовой план на 2 года)": 120, "Преподаватель": "Усенова Б.С.", "Аудитория": "102"},
    {"Дисциплина": "Алгебра", "Часы (Типовой план на 2 года)": 136, "Преподаватель": "Петров П.П.", "Аудитория": "305"},
    {"Дисциплина": "Web дизайн", "Часы (Типовой план на 2 года)": 120, "Преподаватель": "Асанов А.А.", "Аудитория": "204"},
    {"Дисциплина": "Основы бизнеса", "Часы (Типовой план на 2 года)": 188, "Преподаватель": "Алиева К.Д.", "Аудитория": "105"},
]

if "subjects_db" not in st.session_state:
    st.session_state.subjects_db = pd.DataFrame(DEFAULT_SUBJECTS)
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# ─────────────────────────────────────────────
# Темы
# ─────────────────────────────────────────────

THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "sidebar_bg": "#F0F4FF",
        "text": "#1a1a2e",
        "accent": "#1E3A8A",
        "card_bg": "#F8FAFF",
        "border": "#D0D9F0",
        "tab_sel_bg": "#1E3A8A",
        "tab_sel_text": "#FFFFFF",
        "metric_color": "#1E3A8A",
        "input_bg": "#FFFFFF",
    },
    "dark": {
        "bg": "#0E1117",
        "sidebar_bg": "#161B27",
        "text": "#E8EAF0",
        "accent": "#4A7FDB",
        "card_bg": "#1A2035",
        "border": "#2E3A55",
        "tab_sel_bg": "#4A7FDB",
        "tab_sel_text": "#FFFFFF",
        "metric_color": "#7EB3FF",
        "input_bg": "#1A2035",
    }
}

T = THEMES[st.session_state.theme]

st.markdown(f"""
    <style>
    footer {{visibility: hidden;}}
    [data-testid="stHeader"] {{display: none !important;}}
    .stAppDeployButton {{display: none !important;}}
    [data-testid="stStatusWidget"] {{display: none !important;}}
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {{ display: none !important; }}
    [data-testid="stHeaderActionElements"] {{ display: none !important; }}
    .block-container {{ padding-top: 1.2rem !important; }}

    .stApp {{ background-color: {T['bg']} !important; color: {T['text']} !important; }}

    [data-testid="stSidebar"] {{
        background-color: {T['sidebar_bg']} !important;
        border-right: 1px solid {T['border']} !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: {T['card_bg']};
        border: 1px solid {T['border']};
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        color: {T['text']} !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {T['tab_sel_bg']} !important;
        color: {T['tab_sel_text']} !important;
        border-color: {T['tab_sel_bg']} !important;
    }}

    /* ── Общие Кнопки ── */
    .stButton>button {{
        background-color: {T['card_bg']} !important;
        color: {T['text']} !important;
        border: 1.5px solid {T['accent']} !important;
        font-weight: 600;
        transition: all 0.2s ease;
        width: 100%;
    }}
    .stButton>button:hover {{
        background-color: {T['accent']} !important;
        color: #FFFFFF !important;
        border-color: {T['accent']} !important;
    }}
    .stButton>button p, .stButton>button span {{
        color: {T['text']} !important;
    }}
    .stButton>button:hover p, .stButton>button:hover span {{
        color: #FFFFFF !important;
    }}

    /* ── Специфический стиль для БЕЛОЙ кнопки «⋯» ── */
    .white-button .stButton>button {{
        background-color: #FFFFFF !important;
        color: #1A1A2E !important;
        border: 1.5px solid {T['border']} !important;
    }}
    .white-button .stButton>button:hover {{
        background-color: {T['accent']} !important;
        color: #FFFFFF !important;
        border-color: {T['accent']} !important;
    }}
    .white-button .stButton>button p, .white-button .stButton>button span {{
        color: #1A1A2E !important;
    }}
    .white-button .stButton>button:hover p, .white-button .stButton>button:hover span {{
        color: #FFFFFF !important;
    }}

    /* ── Поля ввода (Полное исправление черного фона на светлой теме) ── */
    input, textarea, select,
    [data-baseweb="input"],
    [data-baseweb="input"] > div,
    [data-baseweb="base-input"],
    [data-testid="stDateInput"] div,
    [data-testid="stTextInput"] div,
    [data-testid="stNumberInput"] div,
    [data-testid="stDateInput"] input,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {{
        background-color: {T['input_bg']} !important;
        color: {T['text']} !important;
        border-color: {T['border']} !important;
    }}
    input::placeholder, textarea::placeholder {{
        color: {T['text']} !important;
        opacity: 0.4 !important;
    }}

    /* ── Слайдер ── */
    [data-testid="stSlider"] label, [data-testid="stSlider"] p {{
        color: {T['text']} !important;
    }}

    /* ── Лейблы ── */
    label, p {{
        color: {T['text']} !important;
    }}

    div[data-testid="stMetricValue"] {{
        font-size: 28px;
        color: {T['metric_color']};
        font-weight: bold;
    }}
    </style>
""", unsafe_allow_html=True)

if not st.session_state.sidebar_open:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Вспомогательные функции
# ─────────────────────────────────────────────

def safe_capitalize(s: str) -> str:
    s = s.strip()
    return s[0].upper() + s[1:] if s else s


def apply_auto_capitalize(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["Дисциплина", "Преподаватель", "Аудитория"]:
        if col in df.columns:
            df[col] = df[col].astype(str).map(safe_capitalize)
    return df


def build_working_days(start_date, end_date, holidays_set: set) -> list:
    days = []
    current = start_date
    while current <= end_date:
        if current.weekday() != 6 and current.strftime("%d.%m") not in holidays_set:
            days.append(current)
        current += timedelta(days=1)
    return days


# ─────────────────────────────────────────────
# Константы
# ─────────────────────────────────────────────

TIME_SLOTS = {
    1: "08:00–08:45", 2: "08:50–09:35", 3: "09:40–10:25", 4: "10:30–11:15",
    5: "11:35–12:20", 6: "12:40–13:25", 7: "13:30–14:15"
}

HOLIDAYS: set = {
    "07.11", "08.11",
    "01.01", "02.01", "03.01", "04.01", "05.01", "06.01",
    "07.01", "08.01", "09.01", "10.01",
    "08.03", "21.03", "07.04", "01.05", "05.05", "09.05"
}

DAY_NAMES = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]

# ─────────────────────────────────────────────
# Генератор расписания
# ─────────────────────────────────────────────

def generate_collision_free_schedule(
    db_data: pd.DataFrame,
    start_date,
    end_date,
    max_lpd: int = 3
):
    plans = {"1 Курс": {}, "2 Курс": {}}

    for _, row in db_data.iterrows():
        sub = str(row["Дисциплина"])
        teacher = str(row["Преподаватель"])
        room = str(row["Аудитория"])
        total_hours = int(row["Часы (Типовой план на 2 года)"])
        hours_c1 = (total_hours + 1) // 2
        hours_c2 = total_hours // 2
        if hours_c1 > 0:
            plans["1 Курс"][sub] = {"hours": hours_c1, "teacher": teacher, "room": room}
        if hours_c2 > 0:
            plans["2 Курс"][sub] = {"hours": hours_c2, "teacher": teacher, "room": room}

    working_days = build_working_days(start_date, end_date, HOLIDAYS)
    res_1, res_2 = [], []
    global_tracker: dict = {}

    for day in working_days:
        day_str = day.strftime("%d.%m.%Y")
        day_name = DAY_NAMES[day.weekday()]
        max_slots = 4 if day.weekday() == 5 else 7
        daily_counts: dict = {"1 Курс": {}, "2 Курс": {}}

        for slot in range(1, max_slots + 1):
            key = (day_str, slot)
            global_tracker.setdefault(key, {"teachers": set(), "rooms": set()})

            for course in ("1 Курс", "2 Курс"):
                course_plan = plans[course]
                available = [s for s, info in course_plan.items() if info["hours"] > 0]
                if not available:
                    continue
                valid = [s for s in available if daily_counts[course].get(s, 0) < max_lpd] or available

                strict_valid = []
                for s in valid:
                    tname = course_plan[s]["teacher"]
                    r = course_plan[s]["room"]
                    teacher_free = tname not in global_tracker[key]["teachers"]
                    room_free = (r == "") or (r not in global_tracker[key]["rooms"])
                    if teacher_free and room_free:
                        strict_valid.append(s)

                final_pool = strict_valid if strict_valid else valid
                if not final_pool:
                    continue

                final_pool.sort(key=lambda x: course_plan[x]["hours"], reverse=True)
                chosen = final_pool[0] if random.random() > 0.2 else random.choice(final_pool)

                tname = course_plan[chosen]["teacher"]
                rname = course_plan[chosen]["room"]

                global_tracker[key]["teachers"].add(tname)
                if rname:
                    global_tracker[key]["rooms"].add(rname)

                daily_counts[course][chosen] = daily_counts[course].get(chosen, 0) + 1
                course_plan[chosen]["hours"] -= 1

                entry = {
                    "Дата": day_str, "День": day_name,
                    "Время": TIME_SLOTS[slot], "Урок": slot,
                    "Дисциплина": chosen, "Преподаватель": tname, "Кабинет": rname
                }
                (res_1 if course == "1 Курс" else res_2).append(entry)

        if day.weekday() == 0:
            class_hr = {
                "Дата": day_str, "День": day_name, "Время": "14:20", "Урок": 8,
                "Дисциплина": "Классный час", "Преподаватель": "Куратор", "Кабинет": ""
            }
            res_1.append(class_hr)
            res_2.append(class_hr)

    return pd.DataFrame(res_1), pd.DataFrame(res_2), plans


# ─────────────────────────────────────────────
# Шапка: заголовок + аккуратная белая кнопка настроек
# ─────────────────────────────────────────────

hcol, bcol = st.columns([6, 1])
with hcol:
    st.markdown("## 🗓️ SmartSchedule PL — Панель Управления")
    st.caption("Профессиональная система автоматического планирования учебного процесса на 2 года")

with bcol:
    st.write("")
    # Кнопка «⋯» обернута в специальный CSS-класс white-button для принудительного белого фона
    st.markdown('<div class="white-button">', unsafe_allow_html=True)
    if st.button("⋯", use_container_width=True, help="Настройки оформления"):
        st.session_state.show_settings_menu = not st.session_state.get("show_settings_menu", False)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Выпадающее меню настроек (показывается под шапкой)
if st.session_state.get("show_settings_menu", False):
    with st.container():
        st.markdown(f"""
            <div style="
                background:{T['card_bg']};
                border:1px solid {T['border']};
                border-radius:12px;
                padding:16px 20px;
                margin-bottom:12px;
                display:flex;
                align-items:center;
                gap:16px;
                flex-wrap:wrap;
            ">
                <span style="font-weight:600;color:{T['text']};font-size:14px;">🎨 Оформление:</span>
            </div>
        """, unsafe_allow_html=True)

        mc1, mc2, mc3, mc4 = st.columns([2, 1, 1, 1])
        with mc1:
            st.markdown(f"<span style='color:{T['text']};font-size:13px;'>Выберите тему интерфейса</span>", unsafe_allow_html=True)
        with mc2:
            if st.button("☀️ Светлая", use_container_width=True):
                st.session_state.theme = "light"
                st.session_state.show_settings_menu = False
                st.rerun()
        with mc3:
            if st.button("🌙 Тёмная", use_container_width=True):
                st.session_state.theme = "dark"
                st.session_state.show_settings_menu = False
                st.rerun()
        with mc4:
            if st.button("✕ Закрыть", use_container_width=True):
                st.session_state.show_settings_menu = False
                st.rerun()

# ─────────────────────────────────────────────
# Боковая панель
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Настройки системы")
    max_lessons_per_day = st.slider("Макс. уроков одного предмета в день", 1, 4, 3)
    st.markdown("---")
    if st.button("📋 Загрузить демо-данные", use_container_width=True):
        st.session_state.subjects_db = pd.DataFrame(DEFAULT_SUBJECTS)
        for k in ("df_1", "df_2", "df_svodka", "excel_buffer"):
            st.session_state.pop(k, None)
        st.rerun()
    st.markdown("---")
    st.markdown("**ℹ️ SmartSchedule PL v2.1**")
    st.caption("Система планирования для профессиональных лицеев Кыргызской Республики")

# ─────────────────────────────────────────────
# Вкладки
# ─────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["🗂️ Ввод часов из плана", "🚀 Генератор", "📊 Аналитика вычитки"])

# ── Вкладка 1 ─────────────────────────────────
with tab1:
    st.subheader("Редактор учебного плана (Общие часы на 2 года)")
    st.markdown("Введите дисциплины и общие часы из типового плана. Система сама разделит их между 1 и 2 курсом.")

    edited_df = st.data_editor(
        st.session_state.subjects_db,
        num_rows="dynamic",
        use_container_width=True,
        key="subjects_editor",
    )

    sv_col, hint_col = st.columns([1, 3])
    with sv_col:
        if st.button("💾 Сохранить изменения", use_container_width=True):
            saved = apply_auto_capitalize(edited_df.copy())
            st.session_state.subjects_db = saved
            st.success("✅ Сохранено! Первые буквы приведены к заглавным.")
    with hint_col:
        st.caption("После добавления новых строк нажмите «Сохранить» — текст будет автоматически нормализован.")

    try:
        teacher_rooms = edited_df.groupby("Преподаватель")["Аудитория"].nunique()
        conflicts = teacher_rooms[teacher_rooms > 1].index.tolist()
        if conflicts:
            st.warning(f"⚠️ Преподаватели с несколькими аудиториями: {', '.join(conflicts)}")
    except Exception:
        pass

# ── Вкладка 2 ─────────────────────────────────
with tab2:
    col_input, col_action = st.columns([1, 1])

    with col_input:
        st.subheader("Период семестра")
        start_dt = st.date_input("Начало семестра", datetime(2025, 9, 1))
        end_dt = st.date_input("Окончание семестра", datetime(2026, 5, 25))

    with col_action:
        st.subheader("Запуск модели")
        st.write("Нажмите кнопку для автоматического расчёта и разделения сетки часов.")
        run_generation = st.button("🚀 Начать оптимизацию расписания", type="primary", use_container_width=True)

    if run_generation:
        if start_dt >= end_dt:
            st.error("Дата начала семестра должна быть раньше даты окончания.")
        else:
            with st.spinner("Генерация расписания..."):
                df_cleaned = st.session_state.subjects_db.copy()
                df_cleaned["Дисциплина"] = df_cleaned["Дисциплина"].astype(str).map(safe_capitalize)
                df_cleaned["Преподаватель"] = df_cleaned["Преподаватель"].astype(str).str.strip().str.title()
                df_cleaned["Аудитория"] = df_cleaned["Аудитория"].astype(str).str.strip()
                df_cleaned["Часы (Типовой план на 2 года)"] = (
                    pd.to_numeric(df_cleaned["Часы (Типовой план на 2 года)"], errors="coerce")
                    .fillna(0).astype(int)
                )
                df_cleaned = df_cleaned[df_cleaned["Часы (Типовой план на 2 года)"] > 0]

                df_1, df_2, final_plans = generate_collision_free_schedule(
                    df_cleaned, start_dt, end_dt, max_lpd=max_lessons_per_day
                )

            st.session_state.df_1 = df_1
            st.session_state.df_2 = df_2

            svodka_rows = []
            for _, row in df_cleaned.iterrows():
                sub = row["Дисциплина"]
                teacher = row["Преподаватель"]
                orig_hrs = row["Часы (Типовой план на 2 года)"]
                plan_c1 = (orig_hrs + 1) // 2
                plan_c2 = orig_hrs // 2
                left_1 = final_plans.get("1 Курс", {}).get(sub, {}).get("hours", 0)
                left_2 = final_plans.get("2 Курс", {}).get(sub, {}).get("hours", 0)
                svodka_rows.append({
                    "Дисциплина": sub,
                    "Преподаватель": teacher,
                    "Общий план (2 года)": orig_hrs,
                    "План на 1 курс": plan_c1,
                    "Вычитано на 1 курсе": plan_c1 - left_1,
                    "План на 2 курс": plan_c2,
                    "Вычитано на 2 курсе": plan_c2 - left_2,
                    "Нераспределённый остаток": left_1 + left_2,
                })
            st.session_state.df_svodka = pd.DataFrame(svodka_rows)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_1.to_excel(writer, sheet_name="1 КУРС", index=False)
                df_2.to_excel(writer, sheet_name="2 КУРС", index=False)
                st.session_state.df_svodka.to_excel(writer, sheet_name="Анализ вычитки", index=False)
            buffer.seek(0)
            st.session_state.excel_buffer = buffer.getvalue()

            st.success("✅ Расписание успешно сгенерировано!")

    if "excel_buffer" in st.session_state:
        st.download_button(
            label="📥 Скачать расписание (Excel)",
            data=st.session_state.excel_buffer,
            file_name=f"SmartSchedule_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if "df_1" in st.session_state and "df_2" in st.session_state:
        st.markdown("---")
        st.subheader("Превью расписания")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**1 Курс** — первые 20 строк")
            st.dataframe(st.session_state.df_1.head(20), use_container_width=True)
        with c2:
            st.markdown("**2 Курс** — первые 20 строк")
            st.dataframe(st.session_state.df_2.head(20), use_container_width=True)

# ── Вкладка 3 ─────────────────────────────────
with tab3:
    if "df_svodka" not in st.session_state:
        st.info("Сначала запустите генерацию расписания на вкладке «Генератор».")
    else:
        df_sv = st.session_state.df_svodka

        total_planned = int(df_sv["Общий план (2 года)"].sum())
        total_placed_1 = int(df_sv["Вычитано на 1 курсе"].sum())
        total_placed_2 = int(df_sv["Вычитано на 2 курсе"].sum())
        total_leftover = int(df_sv["Нераспределённый остаток"].sum())

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📚 Всего по плану (2 года)", total_planned)
        m2.metric("✅ Размещено (1 курс)", total_placed_1)
        m3.metric("✅ Размещено (2 курс)", total_placed_2)
        m4.metric("⚠️ Остаток", total_leftover,
                  delta=f"-{total_leftover}" if total_leftover else "0",
                  delta_color="inverse")

        st.markdown("---")
        st.subheader("Детальная таблица вычитки")
        st.dataframe(df_sv, use_container_width=True)

        problem = df_sv[df_sv["Нераспределённый остаток"] > 10]
        if not problem.empty:
            st.warning(
                f"⚠️ {len(problem)} дисциплин с остатком > 10 часов: "
                + ", ".join(problem["Дисциплина"].tolist())
            )
        else:
            st.success("🎉 Все дисциплины распределены с остатком ≤ 10 часов.")

# ─────────────────────────────────────────────
# Футер — техническая поддержка
# ─────────────────────────────────────────────

st.markdown("---")
st.markdown("""
    <div style="display:flex; justify-content:flex-end; padding:6px 0 10px 0;">
        <a href="https://wa.me/996556260309" target="_blank" style="
            display:inline-flex; align-items:center; gap:8px;
            background:#25D366; color:#ffffff; text-decoration:none;
            font-size:14px; font-weight:600; padding:10px 22px; border-radius:10px;
        ">
            <svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='white'>
                <path d='M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z'/>
                <path d='M12 0C5.373 0 0 5.373 0 12c0 2.123.554 4.117 1.527 5.845L.057 23.882a.5.5 0 0 0 .614.635l6.263-1.641A11.945 11.945 0 0 0 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.885 0-3.653-.51-5.17-1.395l-.37-.215-3.838 1.006 1.024-3.73-.235-.384A9.96 9.96 0 0 1 2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z'/>
            </svg>
            Техническая поддержка
        </a>
    </div>
""", unsafe_allow_html=True)