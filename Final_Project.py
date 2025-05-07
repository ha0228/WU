import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import re

# --- Page Settings ---
st.set_page_config(page_title="IPF World Records", layout="wide")

st.title('IPF World Records - Open Powerlifting')
st.write("This app scrapes and displays the latest IPF Raw World Records from [OpenPowerlifting](https://www.openpowerlifting.org/records/raw/ipf).")

# --- Scrape the Data ---
def load_all_tables():
    URL = "https://www.openpowerlifting.org/records/raw/ipf"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    sections = soup.find_all('div', class_='records-col')
    tables = []

    for section in sections:
        h2 = section.find('h2')
        table = section.find('table')

        if h2 and table:
            event_name = h2.text.strip()
            head_flag = True
            rows = []
            last_class = None

            for row in table.find_all('tr'):
                cols = row.find_all(['td', 'th'])
                cols = [ele.text.strip() for ele in cols]

                if cols:
                    if head_flag:
                        headers = cols
                        head_flag = False
                    else:
                        if cols[0] == '':
                            cols[0] = last_class
                        else:
                            last_class = cols[0]
                        rows.append(cols)

            df = pd.DataFrame(rows, columns=headers)
            df['Event'] = event_name
            tables.append(df)

    combined_df = pd.concat(tables, ignore_index=True)
    return combined_df

# --- Load data
data = load_all_tables()

# --- Layout: Filters Left, Chart Right ---
colL, colR = st.columns([0.7, 0.3])  # Filters 70%, Chart 30%

with colL:
    st.markdown("### Choose Event Types:")
    c1, c2, c3 = st.columns(3)
    with c1:
        squat_all = st.checkbox('Squat (All Events)', value=True, key="squat_all")
    with c2:
        bench_all = st.checkbox('Bench (All Events)', value=True, key="bench_all")
    with c3:
        deadlift_all = st.checkbox('Deadlift (All Events)', value=True, key="deadlift_all")
        total = st.checkbox('Total', value=True, key="total")

    selected_event_types = []
    if squat_all: selected_event_types.append('Squat (All Events)')
    if bench_all: selected_event_types.append('Bench (All Events)')
    if deadlift_all: selected_event_types.append('Deadlift (All Events)')
    if total: selected_event_types.append('Total')

    # Class filter
    if 'Class' in data.columns:
        class_list = sorted(data['Class'].dropna().unique().tolist(), key=lambda x: float(x) if x.replace('.', '', 1).isdigit() else float('inf'))
        class_list.insert(0, "All Classes")
        class_selected = st.selectbox('Choose a Class:', options=class_list)

    # Federation filter
    if 'Fed' in data.columns:
        fed_list = sorted(data['Fed'].dropna().unique().tolist())
        fed_list.insert(0, "All Federations")
        fed_selected = st.selectbox('Choose a Federation:', options=fed_list)

    # Name search
    c1, c2, c3 = st.columns([0.04, 0.2, 0.2])
    with c1:
        st.text("Name:")
    with c2:
        name_search = st.text_input("Type a condition:")
    with c3:
        use_regex = st.checkbox("Regular Expression", value=False)

# --- Filter the data ---
filtered_data = data.copy()

if selected_event_types:
    filtered_data = filtered_data[filtered_data['Event'].isin(selected_event_types)]
else:
    filtered_data = pd.DataFrame()

if class_selected != "All Classes" and 'Class' in filtered_data.columns:
    filtered_data = filtered_data[filtered_data['Class'] == class_selected]

if fed_selected != "All Federations" and 'Fed' in filtered_data.columns:
    filtered_data = filtered_data[filtered_data['Fed'] == fed_selected]

if name_search and 'Lifter' in filtered_data.columns:
    if use_regex:
        try:
            filtered_data = filtered_data[filtered_data['Lifter'].str.contains(name_search, case=False, regex=True, na=False)]
        except re.error:
            st.warning("Invalid regular expression.")
    else:
        filtered_data = filtered_data[filtered_data['Lifter'].str.contains(re.escape(name_search), case=False, regex=True, na=False)]

# --- Group filtered tables by event (used in chart + display)
grouped_event_dfs = {}
if not filtered_data.empty:
    for event in selected_event_types:
        event_df = filtered_data[filtered_data['Event'] == event]
        if not event_df.empty:
            grouped_event_dfs[event] = event_df

# --- Right-side chart: dynamic title + value labels ---
with colR:
    chart_title = "🏋️ Top Lift by Class (Rank 1)"  # default

    if grouped_event_dfs:
        combined_df = pd.concat(grouped_event_dfs.values())

        # Determine lift column to display (based on selected event type)
        lift_column = None
        lift_order = ['Total', 'Deadlift', 'Squat', 'Bench']
        for col in lift_order:
            if any(col.lower() in e.lower() for e in selected_event_types):
                if col in combined_df.columns:
                    lift_column = col
                    break

        if lift_column:
            chart_title = f"🏋️ Top {lift_column} by Class (Rank 1)"
            rank1_df = combined_df[combined_df['Rank'] == '1'].copy()
            rank1_df = rank1_df[rank1_df[lift_column].notna()]
            rank1_df['Lift'] = pd.to_numeric(rank1_df[lift_column], errors='coerce')
            rank1_df = rank1_df.dropna(subset=['Lift'])
            rank1_df = rank1_df.sort_values(
                by='Class',
                key=lambda x: x.map(lambda v: float(v) if v.replace('.', '', 1).isdigit() else float('inf'))
            )

            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(3.5, 4.5), facecolor='#0e1117')
            bars = ax.barh(rank1_df['Class'], rank1_df['Lift'], color='#ff6361')

            ax.set_xlabel(f"{lift_column} (kg)", color='white')
            ax.set_ylabel("Class", color='white')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.set_facecolor('#0e1117')
            for spine in ax.spines.values():
                spine.set_color('white')
            ax.grid(color='#444444', linestyle='--', linewidth=0.5, alpha=0.3)
            ax.invert_yaxis()

            # Add value labels to bars
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 10, bar.get_y() + bar.get_height() / 2,
                        f'{width:.1f}', va='center', ha='left', color='white', fontsize=8)

            st.markdown(f"### {chart_title}")
            st.pyplot(fig)
        else:
            st.markdown(f"### {chart_title}")
            st.info("No valid lift column found to display chart.")
    else:
        st.markdown(f"### {chart_title}")
        st.info("No records to display chart.")

# --- Display each table separately by event ---
if grouped_event_dfs:
    for event, df in grouped_event_dfs.items():
        st.subheader(event)
        st.dataframe(df.drop(columns=["Event"]), hide_index=True, use_container_width=True)
else:
    st.warning("No records match your filters.")
