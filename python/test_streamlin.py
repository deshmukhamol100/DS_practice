import streamlit as st 
import numpy as np
import pandas as pd

st.title("My First Streamlit App")  # This will display a title on the app
st.write("Welcome to my first Streamlit app! This is a simple calculator to find the square of a number.")# This will display some text on the app    


st.header("select a number")  # This will create a header in the app

number = st.slider("Select a number", 0, 100, 25)  # This will create a slider for user input

st.subheader("Resuts")  # This will create a subheader in the app

square = number * number

# This will calculate the square of the selected number

st.write("The square of the ", number, " selected number is:", square)  # This will display the result on the app

#seletbox