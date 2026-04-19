import streamlit as st
import joblib
import numpy as np

# Load the saved model
try:
    model = joblib.load('iris_model.joblib')
except FileNotFoundError:
    st.error("Model file 'iris_model.joblib' not found. Please run model.py first.")
    st.stop()

# Define the target names for the Iris dataset
target_names = ['Setosa', 'Versicolor', 'Virginica']

st.title("Iris Flower Prediction App")
st.write("Enter the measurements below to predict the iris species.")

# Create input fields for the four features
col1, col2 = st.columns(2)

with col1:
    sepal_length = st.number_input("Sepal Length (cm)", min_value=0.0, max_value=10.0, value=5.1)
    sepal_width = st.number_input("Sepal Width (cm)", min_value=0.0, max_value=10.0, value=3.5)

with col2:
    petal_length = st.number_input("Petal Length (cm)", min_value=0.0, max_value=10.0, value=1.4)
    petal_width = st.number_input("Petal Width (cm)", min_value=0.0, max_value=10.0, value=0.2)

# Prediction button
if st.button("Predict Species"):
    # Prepare the input data for the model
    features = np.array([[sepal_length, sepal_width, petal_length, petal_width]])
    
    # Make prediction
    prediction = model.predict(features)
    predicted_species = target_names[prediction[0]]
    
    st.success(f"The predicted species is: **{predicted_species}**")
