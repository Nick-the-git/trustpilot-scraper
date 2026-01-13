import streamlit as st

st.title("Hello!")
st.write("If you can see this, Streamlit is working.")

name = st.text_input("What's your name?")
if name:
    st.write(f"Hello, {name}!")
