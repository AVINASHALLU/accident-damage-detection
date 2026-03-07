import os
import streamlit as st

mysql_credentials = {
    'host': st.secrets['DB_HOST'],
    'user': st.secrets['DB_USER'],
    'password' : st.secrets['DB_PASSWORD'],
    'database' : st.secrets['DB_NAME']
}
