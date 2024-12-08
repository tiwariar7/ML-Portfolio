import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
import statistics

# Load data
DATA_PATH = "DATASET/Training.csv"
data = pd.read_csv(DATA_PATH).dropna(axis=1)

# Encode disease labels
encoder = LabelEncoder()
data["prognosis"] = encoder.fit_transform(data["prognosis"])
X, y = data.iloc[:, :-1], data.iloc[:, -1]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=24)

# Train models
models = {
    "SVC": SVC(),
    "Naive Bayes": GaussianNB(),
    "Random Forest": RandomForestClassifier(random_state=18)
}

for model in models.values():
    model.fit(X_train, y_train)

# Train final models on the entire dataset
final_models = {
    "SVC": SVC().fit(X, y),
    "Naive Bayes": GaussianNB().fit(X, y),
    "Random Forest": RandomForestClassifier(random_state=18).fit(X, y)
}

# Symptom dictionary for input processing
symptom_index = {symptom: i for i, symptom in enumerate(X.columns)}

def predict_disease(symptoms):
    input_data = [0] * len(symptom_index)
    for symptom in symptoms.split(", "):
        if symptom in symptom_index:
            input_data[symptom_index[symptom]] = 1

    input_df = pd.DataFrame([input_data], columns=X.columns)
    predictions = [model.predict(input_df)[0] for model in final_models.values()]
    final_prediction = statistics.mode(predictions)
    return encoder.inverse_transform([final_prediction])[0]