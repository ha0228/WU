import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
import re 

#make the page wide
st.set_page_config(page_title="Hussain WU Directory", layout="wide")

#title of the page
st.title('Directory at Westminster University')

#content
st.write("This is an enhanced alternative to the employee [directory](https://westminsteru.edu/campus-directory/index.html) at Westminster University." )

data = pd.read_csv('WU_directory.csv') 

#Department filter
department_list = sorted(data['Department'].dropna().unique().tolist())
department_list.insert(0, "All Departments")
department = st.selectbox('Choose one department from below:', options=department_list)

if department != 'All Departments':
    data = data[data['Department'] == department]

#Role filter
col1, col2, col3, col4 = st.columns([0.2, 0.2, 0.2, 0.4])
with col1:
    st.text("Type of Role:") 
with col2:
    role_faculty = st.checkbox('Faculty', value=1)
with col3:
    role_staff = st.checkbox('Staff', value=2)

if role_faculty and not role_staff:
    data = data[data['Role'] == 'Faculty']
elif role_staff and not role_faculty:
    data = data[data['Role'] == 'Staff']
elif not role_faculty and not role_staff:
    data = pd.DataFrame()

#Contract filter
col1, col2, col3, col4 = st.columns([0.2, 0.2, 0.2, 0.4])
with col1:
    st.text("Type of Contract:") 
with col2:
    contract_full = st.checkbox('FULL-TIME', value=1)
with col3:
    contract_part = st.checkbox('PART-TIME', value=1)

if contract_full and not contract_part:
    data = data[data['Contract'] == 'FULL-TIME']
elif contract_part and not contract_full:
    data = data[data['Contract'] == 'PART-TIME']
elif not contract_full and not contract_part:
    data = pd.DataFrame()

#Faculty filter
col1, col2, col3, col4, col5 = st.columns([0.2, 0.2, 0.2, 0.2, 0.4])
with col1:
    st.text("Rank of Faculty:") 
with col2:
    position_assistant = st.checkbox('Assistant', value=1)
with col3:
    position_associate = st.checkbox('Associate', value=1)
with col4:
    position_full = st.checkbox('Full', value=1)    

selected_ranks = []
if position_assistant:
    selected_ranks.append("Assistant")
if position_associate:
    selected_ranks.append("Associate")
if position_full:
    selected_ranks.append("Professor") 

# Apply filter if any selected
if selected_ranks:
    pattern = "|".join(selected_ranks)
    data = data[data['Position'].str.contains(pattern, case=False, na=False)]
else:
    data = pd.DataFrame()

# Name search filter with regex
col1, col2, col3 = st.columns([0.04, 0.2, 0.2])
with col1:
    inst = st.text("Name:")
with col2:
    name_search = st.text_input("Type a condition:")
with col3:
    use_regex = st.checkbox("Regular Expression", value=False)

if name_search:
    if use_regex:
        try:
            data = data[data['Name'].str.contains(name_search, case=False, regex=True, na=False)]
        except re.error:
            st.warning("Invalid regular expression.")
    else:
        data = data[data['Name'].str.contains(re.escape(name_search), case=False, regex=True, na=False)]

st.dataframe(data, hide_index=True)
