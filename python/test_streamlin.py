import streamlit as st 
import numpy as np
import pandas as pd

st.title("My First Streamlit App")  # This will display a title on the app
st.write("this is simple app to demonstrate how to get started with Streamlit. You can use Streamlit to create interactive web applications with Python. Let's explore some of the features of Streamlit together.")# This will display some text on the app    
st.sidebar.header("User Input features")  # This will create a header in the sidebar

# This will create a slider in the sidebar for user input
user_name = st.sidebar.slider("Select your name", "AMol deshmukh")

#slider for age
age = st.sidebar.slider("Select your age", 0, 100, 25)

#selectbox for gender
gender = st.sidebar.selectbox("Select your gender", ["Male", "Female", "Other"])    

