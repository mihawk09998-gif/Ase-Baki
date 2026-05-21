import streamlit as st
import pandas as pd
import datetime
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# =====================================================================
# НАСТРОЙКИ СТРАНИЦЫ И СКРЫТИЕ ИНТЕРФЕЙСА STREAMLIT
# =====================================================================
st.set_page_config(page_title="Архитектор расписания", layout="wide", page_icon="📅")

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="collapsedControl"] {display: none;}
.stAppDeployButton {display: none;}
.custom-footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: transparent;
    color: #888;
    text-align: right;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
    z-index: 100;
}
</style>
<div class="custom-footer">сделано Lottarruu</div>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# =====================================================================
# 1. КЛАСС ЛОГИКИ И АЛГОРИТМА РАСПРЕДЕЛЕНИЯ ЧАСОВ
# =====================================================================
class ScheduleGenerator:
    def __init__(self, group_config):
        self.name = group_config['name']
        self.num_courses = group_config['num_courses']
        self.work_week = group_config['work_week']
        self.max_saturday_lessons = group_config['max_saturday_lessons']
        self.max_weekday_lessons = group_config['max_weekday_lessons']
        self.max_per_subject = group_config['max_per_subject']
        self.start_date = group_config['start_date']
        self.end_date = group_config['end_date']
        self.subjects = group_config['subjects']

    def _is_kr_holiday(self, date_obj):
        if date_obj.month == 1 and 1 <= date_obj.day <= 12: return "Новогодние каникулы"
        if date_obj.month == 5 and 1 <= date_obj.day <= 9: return "Майские каникулы"
            
        fixed_holidays = [
            (2, 23, "День защитника Отечества"), (3, 8, "Международный женский день"),
            (3, 21, "Нооруз"), (4, 7, "День народной Апрельской революции"),
            (11, 7, "День истории и памяти"), (11, 8, "День истории и памяти")
        ]
        for m, d, name in fixed_holidays:
            if date_obj.month == m and date_obj.day == d: return name
                
        floating_holidays = {
            2025: [(3, 30, "Орозо айт"), (6, 6, "Курман айт")],
            2026: [(3, 20, "Орозо айт"), (5, 27, "Курман айт")],
            2027: [(3, 10, "Орозо айт"), (5, 17, "Курман айт")],
            2028: [(2, 27, "Орозо айт"), (5, 5, "Курман айт")],
            2029: [(2, 15, "Орозо айт"), (4, 24, "Курман айт")],
            2030: [(2, 4, "Орозо айт"), (4, 14, "Курман айт")]
        }
        for m, d, name in floating_holidays.get(date_obj.year, []):
            if date_obj.month == m and date_obj.day == d: return name
        return None

    def _fill_day(self, day_info, balances, max_slots, is_spring, weekly_usage):
        daily_usage = {s['name']: 0 for s in self.subjects}
        slots_filled = 0

        while slots_filled < max_slots:
            space_left = max_slots - slots_filled
            
            # Проверяем, сколько предметов вообще осталось в балансе
            active_subjects = [s for s in self.subjects if balances[s['name']] > 0]
            if not active_subjects:
                break # Все часы всех предметов вычитаны
                
            # Если остался всего 1 предмет, отключаем дневные лимиты, чтобы вычитать его до конца!
            ignore_daily_limit = (len(active_subjects) == 1)

            def get_priority(sub):
                name = sub['name']
                rem = balances[name]
                if rem <= 0: return (-1, 0, 0)
                
                allowance = float('inf') if ignore_daily_limit else (self.max_per_subject - daily_usage[name])
                if allowance <= 0: return (-1, 0, 0)

                # Логика акцентов (Весна vs Осень)
                if is_spring:
                    base_prio = 2 if sub['accent'] else 1
                else:
                    if sub['accent']:
                        base_prio = 1 if weekly_usage.get(name, 0) < 2 else 0
                    else:
                        base_prio = 2
                
                # Ключевая логика: Можем ли мы поставить ПАРУ? 
                # (Это отправляет одиночные уроки в конец дня)
                can_pair = 1 if (rem >= 2 and allowance >= 2 and space_left >= 2) else 0
                
                return (base_prio, can_pair, rem)

            available = [s for s in self.subjects if get_priority(s)[0] >= 0]
            
            if not available:
                # Сработал лимит завуча (Вариант А). Оставляем день полупустым.
                break 

            best_sub = max(available, key=get_priority)
            s_name = best_sub['name']
            
            rem_hours = balances[s_name]
            allowance = float('inf') if ignore_daily_limit else (self.max_per_subject - daily_usage[s_name])
            max_put = min(space_left, rem_hours, allowance)
            
            # Разбиваем на пары, если это возможно
            if self.max_per_subject == 1 and not ignore_daily_limit:
                chunk = 1
            else:
                chunk = 2 if max_put >= 2 else 1

            day_info["slots"].extend([s_name] * chunk)
            balances[s_name] -= chunk
            daily_usage[s_name] += chunk
            slots_filled += chunk
            
            if best_sub['accent']:
                weekly_usage[s_name] = weekly_usage.get(s_name, 0) + chunk

    def generate_schedule(self):
        all_dates = []
        curr = self.start_date
        while curr <= self.end_date:
            all_dates.append(curr)
            curr += datetime.timedelta(days=1)
            
        ay_map = {}
        for d in all_dates:
            ay = d.year if d.month >= 8 else d.year - 1
            if ay not in ay_map: ay_map[ay] = []
            ay_map[ay].append(d)
            
        sorted_ays = sorted(list(ay_map.keys()))
        
        course_dates = {c: [] for c in range(1, self.num_courses + 1)}
        for idx, ay in enumerate(sorted_ays):
            c_idx = min(idx + 1, self.num_courses)
            course_dates[c_idx].extend(ay_map[ay])

        final_results = {}
        group_max_cols = max(self.max_weekday_lessons, self.max_saturday_lessons)

        for c in range(1, self.num_courses + 1):
            c_dates = course_dates[c]
            if not c_dates: continue
            
            c_balances = {}
            for sub in self.subjects:
                base_hours = sub['hours'] // self.num_courses
                rem_hours = sub['hours'] % self.num_courses
                c_balances[sub['name']] = base_hours + (rem_hours if c == self.num_courses else 0)

            working_pool = []
            c_calendar = {}
            for d in c_dates:
                if d.weekday() == 6: continue
                if d.weekday() == 5 and self.work_week == "5-дневная рабочая неделя": continue
                if d.month in [6, 7, 8]: continue
                working_pool.append(d)
                
            buffer_set = set(sorted(working_pool)[-3:]) if working_pool else set()

            for d in working_pool:
                hol = self._is_kr_holiday(d)
                if hol: c_calendar[d] = {"status": "Праздник", "info": hol, "slots": []}
                elif d in buffer_set: c_calendar[d] = {"status": "Буфер", "info": "Резерв", "slots": []}
                else: c_calendar[d] = {"status": "Рабочий", "slots": []}

            current_week_idx = -1
            weekly_accent_usage = {}
            
            for date_obj in sorted(c_calendar.keys()):
                if c_calendar[date_obj]["status"] != "Рабочий": continue
                
                year, week_num, weekday = date_obj.isocalendar()
                if week_num != current_week_idx:
                    current_week_idx = week_num
                    weekly_accent_usage = {s['name']: 0 for s in self.subjects}
                    
                max_s = self.max_saturday_lessons if date_obj.weekday() == 5 else self.max_weekday_lessons
                is_spring = (1 <= date_obj.month <= 5)
                
                self._fill_day(c_calendar[date_obj], c_balances, max_s, is_spring, weekly_accent_usage)

            rem_total = sum(c_balances.values())
            if rem_total > 0:
                buf_days = sorted([d for d in c_calendar if c_calendar[d]["status"] == "Буфер"], reverse=True)
                for bd in buf_days:
                    if sum(c_balances.values()) <= 0: break
                    c_calendar[bd]["status"] = "Рабочий (Из резерва)"
                    max_s = self.max_saturday_lessons if bd.weekday() == 5 else self.max_weekday_lessons
                    self._fill_day(c_calendar[bd], c_balances, max_s, True, {})

            # Передаем group_max_cols, чтобы Excel жестко отрисовал нужную сетку
            final_results[f"{self.name} ({c} курс)"] = (c_calendar, c_balances, group_max_cols)

        return final_results


# =====================================================================
# 2. СЕРВИС СБОРКИ EXCEL-ФАЙЛА
# =====================================================================
def create_excel_workbook(all_group_results):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    font_title = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=11)
    font_bold_data = Font(name="Calibri", size=11, bold=True)
    
    fill_header = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    fill_holiday = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid") 
    fill_buffer = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")  
    fill_weekend = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid") 
    fill_eaten = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid") 

    border_thin = Border(left=Side(style='thin', color='BFBFBF'), right=Side(style='thin', color='BFBFBF'),
                         top=Side(style='thin', color='BFBFBF'), bottom=Side(style='thin', color='BFBFBF'))
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws_rem = wb.create_sheet(title="Остаток часов")
    ws_rem.append(["Сводный отчет по нераспределенным часам"])
    ws_rem.merge_cells("A1:C1")
    ws_rem["A1"].font, ws_rem["A1"].fill, ws_rem["A1"].alignment = font_title, fill_header, align_center
    ws_rem.append(["Учебная группа (Курс)", "Наименование предмета", "Остаток (число часов)"])
    for col_idx in range(1, 4):
        c = ws_rem.cell(row=2, column=col_idx)
        c.font, c.fill, c.alignment = font_header, PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid"), align_center

    has_overflows = False

    for tab_name, (calendar, remainders, group_max_cols) in all_group_results.items():
        for sub_name, rem_h in remainders.items():
            if rem_h > 0:
                ws_rem.append([tab_name, sub_name, rem_h])
                has_overflows = True
                
        safe_tab_name = tab_name[:31].replace("/", "-").replace("\\", "-")
        ws = wb.create_sheet(title=safe_tab_name)
        ws.append([f"Расписание занятий: {tab_name}"])
        
        # Жесткая фиксация колонок по лимитам завуча
        max_cols = max(1, group_max_cols)
        
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2+max_cols)
        ws["A1"].font, ws["A1"].fill, ws["A1"].alignment = font_title, fill_header, align_center
        ws.row_dimensions[1].height = 35
        
        headers = ["Дата", "День недели"] + [f"Урок {i+1}" for i in range(max_cols)]
        ws.append(headers)
        for col_idx, h in enumerate(headers, 1):
            c = ws.cell(row=2, column=col_idx)
            c.font, c.fill, c.alignment, c.border = font_header, PatternFill(start_color="418AB3", end_color="418AB3", fill_type="solid"), align_center, border_thin

        days_translations = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        
        row_idx = 3
        for date_obj in sorted(calendar.keys()):
            day_info = calendar[date_obj]
            ws.cell(row=row_idx, column=1, value=date_obj.strftime("%d.%m.%Y")).alignment = align_center
            ws.cell(row=row_idx, column=2, value=days_translations[date_obj.weekday()]).alignment = align_center
            ws.cell(row=row_idx, column=1).font = ws.cell(row=row_idx, column=2).font = font_bold_data
            
            # Проверка, сколько уроков положено в этот конкретный день
            limit_for_this_day = 0
            if "Рабочий" in day_info["status"]:
                # Суббота может иметь меньше колонок-уроков, чем будни, но сетка Excel единая.
                limit_for_this_day = calendar[date_obj].get("max_s", max_cols) # Вспомогательная логика
            
            if day_info["status"] == "Праздник":
                ws.merge_cells(start_row=row_idx, start_column=3, end_row=row_idx, end_column=2+max_cols)
                c = ws.cell(row=row_idx, column=3, value=f"🎉 {day_info['info']}")
                c.alignment, c.font = align_center, font_bold_data
                for col in range(1, 3+max_cols): 
                    ws.cell(row=row_idx, column=col).fill = fill_holiday
                    ws.cell(row=row_idx, column=col).border = border_thin
            elif day_info["status"] == "Буфер":
                ws.merge_cells(start_row=row_idx, start_column=3, end_row=row_idx, end_column=2+max_cols)
                c = ws.cell(row=row_idx, column=3, value="⏳ Резерв завуча")
                c.alignment, c.font = align_center, font_bold_data
                for col in range(1, 3+max_cols): 
                    ws.cell(row=row_idx, column=col).fill = fill_buffer
                    ws.cell(row=row_idx, column=col).border = border_thin
            else:
                slots = day_info["slots"]
                # Отрисовываем уроки по жесткой сетке max_cols
                for slot_idx in range(max_cols):
                    col_num = 3 + slot_idx
                    val = slots[slot_idx] if slot_idx < len(slots) else "—"
                    c = ws.cell(row=row_idx, column=col_num, value=val)
                    c.alignment, c.font = (align_center if val=="—" else Alignment(horizontal="left", vertical="center")), font_data
                
                for col in range(1, 3+max_cols): 
                    if day_info["status"] == "Рабочий (Из резерва)":
                        ws.cell(row=row_idx, column=col).fill = fill_eaten
                    elif date_obj.weekday() == 5:
                        ws.cell(row=row_idx, column=col).fill = fill_weekend
                    ws.cell(row=row_idx, column=col).border = border_thin
                    
            row_idx += 1

        for col in ws.columns:
            ws.column_dimensions[get_column_letter(col[0].column)].width = max(max(len(str(c.value or '')) for c in col) + 3, 12)

    if not has_overflows: ws_rem.append(["Остатков нет!"])
    for col in ws_rem.columns: ws_rem.column_dimensions[get_column_letter(col[0].column)].width = 25

    virtual_workbook = io.BytesIO()
    wb.save(virtual_workbook)
    virtual_workbook.seek(0)
    return virtual_workbook

# =====================================================================
# 3. ПОЛЬЗОВАТЕЛЬСКИЙ ИНТЕРФЕЙС STREAMLIT
# =====================================================================
st.title("📅 Архитектор Расписания")

if 'global_groups' not in st.session_state: st.session_state.global_groups = []
if 'temp_subjects' not in st.session_state: st.session_state.temp_subjects = []
if 'input_name' not in st.session_state: st.session_state.input_name = ""
if 'input_hours' not in st.session_state: st.session_state.input_hours = 36
if 'input_accent' not in st.session_state: st.session_state.input_accent = False

def add_subject():
    name = st.session_state.input_name.strip()
    if name:
        st.session_state.temp_subjects.append({
            "name": name, 
            "hours": st.session_state.input_hours, 
            "accent": st.session_state.input_accent
        })
        st.session_state.input_name = ""
        st.session_state.input_accent = False
    else:
        st.toast("⚠️ Введите название дисциплины!")

def edit_subject(idx):
    sub = st.session_state.temp_subjects.pop(idx)
    st.session_state.input_name = sub['name']
    st.session_state.input_hours = sub['hours']
    st.session_state.input_accent = sub['accent']

def del_subject(idx): st.session_state.temp_subjects.pop(idx)

# ЦЕНТРАЛЬНАЯ ПАНЕЛЬ УПРАВЛЕНИЯ ГРУППАМИ
with st.expander("⚙️ УПРАВЛЕНИЕ БАЗОЙ И ГЕНЕРАЦИЯ (Нажмите чтобы открыть)", expanded=False):
    if st.session_state.global_groups:
        st.success(f"В базе сохранено групп: {len(st.session_state.global_groups)}")
        for idx, g in enumerate(st.session_state.global_groups):
            c1, c2, c3 = st.columns([4, 2, 1])
            c1.markdown(f"**{g['name']}** — {g['num_courses']} курс(а)")
            c2.markdown(f"Предметов: {len(g['subjects'])}")
            c3.button("Удалить", key=f"del_group_{idx}", on_click=lambda i=idx: st.session_state.global_groups.pop(i))
        
        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🗑️ Очистить всю базу", use_container_width=True):
                st.session_state.global_groups = []
                st.rerun()
        with col_btn2:
            if st.button("🚀 СГЕНЕРИРОВАТЬ EXCEL-ФАЙЛ", type="primary", use_container_width=True):
                with st.spinner("Сборка расписания по курсам..."):
                    all_results = {}
                    for g_cfg in st.session_state.global_groups:
                        course_results = ScheduleGenerator(g_cfg).generate_schedule()
                        all_results.update(course_results)
                    
                    excel_stream = create_excel_workbook(all_results)
                    st.download_button(
                        label="📥 СКАЧАТЬ ГОТОВОЕ РАСПИСАНИЕ (.XLSX)", data=excel_stream,
                        file_name=f"Расписание_{datetime.date.today().strftime('%d_%m_%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
    else:
        st.info("База пуста. Добавьте группы ниже.")

st.markdown("---")

# ФОРМА ВВОДА
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Параметры группы")
    g_name = st.text_input("Название группы", placeholder="Например: ЭПП-22")
    g_courses = st.number_input("Количество курсов (лет обучения)", min_value=1, max_value=4, value=1)
    
    g_week = st.selectbox("Режим обучения", ["5-дневная рабочая неделя", "6-дневная рабочая неделя"])
    
    # Динамические ползунки
    g_weekday_limit = st.slider("Кол-во уроков в будни (Пн-Пт)", 4, 8, 6)
    
    if g_week == "6-дневная рабочая неделя":
        g_sat_limit = st.slider("Кол-во уроков в субботу", 1, 8, 4)
    else:
        g_sat_limit = 0
        
    g_max_per_subject = st.slider("Макс. уроков одного предмета в день", 1, 8, 2)
    dates = st.date_input("Общий период обучения (для всех курсов)", value=(datetime.date(2025, 9, 1), datetime.date(2026, 5, 25)))

with col_right:
    st.subheader("2. Дисциплины (Общие часы)")
    
    with st.container(border=True):
        col_n, col_h = st.columns([2, 1])
        with col_n: st.text_input("Название", key="input_name", placeholder="Математика")
        with col_h: st.number_input("Часы", min_value=1, key="input_hours")
            
        st.checkbox("🔥 Акцент на конец года", key="input_accent")
        st.button("➕ Добавить", on_click=add_subject, use_container_width=True)

    if st.session_state.temp_subjects:
        st.markdown("**Список к сохранению:**")
        for i, sub in enumerate(st.session_state.temp_subjects):
            c1, c2, c3 = st.columns([6, 1, 1])
            c1.markdown(f"**{sub['name']}** — {sub['hours']} ч. {'🔥' if sub['accent'] else ''}")
            c2.button("✏️", key=f"edit_sub_{i}", on_click=edit_subject, args=(i,))
            c3.button("❌", key=f"del_sub_{i}", on_click=del_subject, args=(i,))

st.markdown("---")

if st.button("💾 СОХРАНИТЬ ГРУППУ В БАЗУ", type="secondary", use_container_width=True):
    if not g_name: st.error("Укажите название группы!")
    elif len(dates) != 2: st.error("Выберите полный диапазон дат!")
    elif not st.session_state.temp_subjects: st.error("Добавьте хотя бы один предмет!")
    else:
        st.session_state.global_groups.append({
            "name": g_name.strip(), "num_courses": g_courses, "work_week": g_week,
            "max_saturday_lessons": g_sat_limit, "max_weekday_lessons": g_weekday_limit,
            "max_per_subject": g_max_per_subject, "start_date": dates[0], "end_date": dates[1],
            "subjects": list(st.session_state.temp_subjects)
        })
        st.session_state.temp_subjects = []
        st.success(f"Группа {g_name} сохранена! Откройте верхнюю панель для генерации.")
        st.rerun()