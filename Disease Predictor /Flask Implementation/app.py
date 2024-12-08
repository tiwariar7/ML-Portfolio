from flask import Flask, request, jsonify, render_template
from predictor import predict_disease  # Import the function from your model script

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])

def index():
    if request.method == "POST":
        symptoms = request.form.get("symptoms")
        prediction = predict_disease(symptoms)
        return render_template("index.html", result=prediction, symptoms=symptoms)
    return render_template("index.html", result=None)
@app.route('/contact')

def contact():
    return render_template('contact.html', page='contact')

@app.route('/about')
def about():
    return render_template('about.html')  # Save this HTML file as 'about.html'

if __name__ == "__main__":
    app.run(debug=True)
