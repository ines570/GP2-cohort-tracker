import streamlit as st
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import plotly.io as pio
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from PIL import Image
import datetime
import plotly.express as px
import sqlite3

st.set_page_config(
    layout = 'wide'
)

df=pd.read_csv('Data Curation - OCT 2021 - CLEANED_DATA.csv')
df['Current_Total'].fillna(df.Current_Total, inplace=True)
df_count_country = df.groupby('Territory')['Short_Name'].count()
df['Timestamp'] = pd.to_datetime(df['Timestamp'],format='%m/%d/%Y', errors='ignore')
countries = df['Territory'].unique()


####################### HEAD ##############################################

head_1, head_2, title, head_3, head_4 = st.columns([1.2,1.2,4,1,1])
mjff = Image.open('mgff_logo.png')
head_1.image(mjff, width = 100)
gp2 = Image.open('gp2_logo.png')
head_2.image(gp2, width = 100)

with title:
    st.markdown("""
    <style>
    .big-font {
        font-size:46px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<p class="big-font">Cohort Tracker Dashboard</p>', unsafe_allow_html=True)

with head_3:
    st.markdown("**TOTAL SAMPLES**")
    total_n = df['Current_Total'].sum()   
    st.markdown(total_n)
with head_4:
    st.markdown("**LAST UPDATED**")
    most_recent_date = df['Timestamp'].max()   
    st.markdown(most_recent_date)

    
    
    

#DB Management
conn = sqlite3.connect('data.db')
c = conn.cursor()

def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS usertable(username TEXT, password TEXT)')
    
def add_userdata(username, password):
    c.execute('INSERT INTO usertable(username, password) VALUES (?,?)', (username, password))
    conn.commit()
    
def login_user(username, password):
    c.execute('SELECT * FROM usertable WHERE username =? AND password = ?', (username, password))
    data = c.fetchall()
    return data
    
def view_all_users():
    c.execute('SELECT * FROM usertable')
    data = c.fetchall()
    return data




def main():
    """"Login App"""
        
    menu = ["Home", "Login", "SignUp"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Home":
        st.subheader("Please Login First Before Use the App")
        
    elif choice == "Login":
        st.sidebar.subheader("Login Section")
        
        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.checkbox("Login"):
            #if password == '12345':
            create_usertable()
            result = login_user(username, password)
            if result: 
                st.sidebar.success("Logged in as {}".format(username))
                

                ########################  SIDE BAR #########################################

                st.sidebar.header("**Find your cohort**")
                countries_selected = st.sidebar.multiselect('Main Site Selection', countries)

                if len(countries_selected) > 0:

                    df_cf = df.loc[df['Main_Site'].isin(countries_selected)]
                else:
                    df_cf = df


                slider_1, slider_2 = st.sidebar.slider('Cohort size', int(df_cf['Current_Total'].min()), int(df_cf['Current_Total'].max()+1), [int(df_cf['Current_Total'].min()),
                                                       int(df_cf['Current_Total'].max()+1)],10)


                df_csf = df_cf[df_cf['Current_Total'].between(slider_1, slider_2)].reset_index(drop=True).sort_values('Short_Name', ascending=True)


                cohort_selection = st.sidebar.selectbox('Cohort selection',df_csf['Short_Name'].unique())
                df_selected = df_csf.loc[df_csf['Short_Name'] == cohort_selection]
                df_selected = df_selected.reset_index()
                
                
                ########################  1st row   #########################################
                world, europe, asia, na, sa, blank = st.columns([1,1,1.2,1.2,1.2,3])

                df_map = df
                WORLD = world.button('WORLD')
                if WORLD:
                    with world:
                       df_map = df

                EUR = europe.button('EUROPE')
                if EUR:
                    with europe:
                       df_map = df.loc[df['Continent'] == 'Europe']

                ASIA = asia.button('ASIA/OCEANIA')
                if ASIA:
                    with asia:
                       df_map = df.loc[df['Continent'] == 'Asia/Oceania']

                NAM = na.button('NORTH AMERICA')
                if NAM:
                    with na:
                       df_map = df.loc[df['Continent'] == 'North America']

                SAM = sa.button('SOUTH AMERICA')
                if SAM:
                    with sa:
                       df_map = df.loc[df['Continent'] == 'South America']
                    
                ########################  2nd row   #########################################
                left_column, right_column = st.columns([2.5,1])
                with right_column:
                    df_selected_update = df_selected[['Short_Name','Proposed_Samples_by2022', 'Processed_Samples']]
                    df_selected_update['Processed_Samples'] = df_selected_update['Processed_Samples'].astype(str).apply(lambda x: x.replace('.0',''))
                    selected_cohort = f"Cohort Name:      **{df_selected['Short_Name'][0]}**"
                    st.markdown(selected_cohort)
                    st.table(df_selected_update.iloc[:, 1:3].assign(hack='').set_index('hack'))
                    #st.metric(label='Expected Samples by 2022', value=df_selected_update['Proposed_Samples_by2022'], delta=None)
                    #st.metric(label='Processed Samples', value=df_selected_update['Processed_Samples'], delta=None)
                    
                    ppd=df_selected['Current_PD']
                    nonpd=df_selected['Current_nonPD']
                    d=pd.concat([ppd, nonpd], axis = 1).T
                    d.columns = ['cohort']
                    fig = px.pie(d, values=d['cohort'], names = d.index)
                    fig.update_layout(showlegend=False,
                        width=400,
                        height=400)
                    st.markdown("**Distribution of PD vs Non PD**")
                    st.write(fig)
                    

                with left_column:
                    df_map['cohort_number'] = df_map.groupby('Territory')['Short_Name'].transform('size')
                    geo_map = px.scatter_geo(df_map, locations="Territory", color=np.log10(df_map['Current_Total']),
                                     hover_name="Territory", size = 'cohort_number',
                                     projection="natural earth", color_continuous_scale = px.colors.sequential.Plasma, 
                                     locationmode = "country names")
                    geo_map.update_layout(width=900,height=600)
                    geo_map.update_coloraxes(colorbar_title = "Log10 Pat#",colorscale = "deep", reversescale=False)
                    st.markdown("**GP2 Cohort Participant Numbers Geo Scatter Map**")
                    st.write(geo_map)
                    
                    
                ########################  3rd row   #########################################
                col_1, col_2, col_3, col_4, col_5, col_6 = st.columns([1.5,1,1,1,1,1.5])
                
                
                with col_1:
                    st.markdown("**Study Name**")
                    st.write(df_selected['Full_Name'][0])
                    
                with col_2:
                    st.markdown("**Main Study Site**")
                    df_selected['Main_site'] = df_selected['Location'] + ', ' + df_selected['Territory']
                    st.write(df_selected['Main_site'][0])

                with col_3:
                    st.markdown("**Completion Year**")
                    st.markdown(df_selected['Cohort_completion_Year'][0])
                    
                with col_4:
                    st.markdown("**Multisite Cohort**")
                    st.write(df_selected['Multisite_Study'][0])

                with col_5:
                    st.markdown("**Participant Type**")
                    st.write(df_selected['Participant_type'][0])
                    
                with col_6:
                    st.markdown("**Study Type**")
                    st.write(df_selected['Study_type'][0])                










                    
            else:
                st.warning("Incorrect Username/Password")
            
    elif choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        
        if st.button("Signup"):
            create_usertable()
            add_userdata(new_user, new_password)
            st.success("You have successfully created a valid Account")
            st.info("Go to Login Menu to login")

        
        
        
        
        
        
        
        
if __name__ == '__main__':
    main()
