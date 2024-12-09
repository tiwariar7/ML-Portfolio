from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import numpy as np
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)
app.secret_key = "d8b3cc8ff96741aa4b4f213a9b8e57ff"  # Replace with a secure key

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load models, scaler, and label encoder
logreg_chd = joblib.load('logreg_chd_model.pkl')
logreg_disease = joblib.load('logreg_disease_model.pkl')
scaler = joblib.load('scaler.pkl')
label_encoder = joblib.load('label_encoder.pkl')

# User database (email: hashed_password)
users_db = {
    "test@example.com": {
        "username": "testuser",
        "password": generate_password_hash("password123")
    }
}
stored_data = []  # List to store user data
reviews_db = []  # List to store customer reviews
contact_messages_db = []  # Stores contact form submissions

@app.route('/save_data', methods=['POST'])
def save_data():
    """Endpoint to save user data."""
    data = request.get_json()
    if data.get('save') == 'yes':
        entry = {
            "name": data.get("name"),
            "prediction": data.get("prediction"),
        }
        stored_data.append(entry)
        logging.info(f"Saved data: {entry}")
    return jsonify({"message": "Data saved successfully!"}), 200

# New Route: Submit a review
@app.route('/submit_review', methods=['POST', 'GET'])
def submit_review():
    """Route to handle customer reviews."""
    if request.method == 'POST':
        customer_name = request.form.get('name', 'Anonymous')
        review_text = request.form.get('review', '').strip()
        
        if not review_text:
            flash("Review text cannot be empty.", "danger")
            return redirect(url_for('submit_review'))
        
        # Save the review
        review_entry = {
            "name": customer_name,
            "review": review_text
        }
        reviews_db.append(review_entry)
        logging.info(f"New review added: {review_entry}")
        flash("Thank you for your review!", "success")
        return redirect(url_for('reviews'))

    return render_template('submit_review.html')

# New Route: Display all reviews
@app.route('/reviews')
def reviews():
    """Route to display all customer reviews."""
    return render_template('reviews.html', reviews=reviews_db)

# OAuth blueprints
google_blueprint = make_google_blueprint(client_id="GOOGLE_CLIENT_ID", client_secret="GOOGLE_CLIENT_SECRET", redirect_to="oauth_login")
app.register_blueprint(google_blueprint, url_prefix="/login/google")

github_blueprint = make_github_blueprint(client_id="GITHUB_CLIENT_ID", client_secret="GITHUB_CLIENT_SECRET", redirect_to="oauth_login")
app.register_blueprint(github_blueprint, url_prefix="/login/github")

@app.route("/")
def home():
    return render_template('home.html')

@app.route('/predict', methods=['POST'])
def predict(): 
    """Handle predictions."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        # Required fields validation
        required_fields = ['age', 'sex_male', 'cigsPerDay', 'totChol', 'sysBP', 'glucose']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

        # Extract and validate features
        try:
            features = [
                float(data.get('age')),
                float(data.get('sex_male')),
                float(data.get('cigsPerDay')),
                float(data.get('totChol')),
                float(data.get('sysBP')),
                float(data.get('glucose'))
            ]
        except ValueError:
            return jsonify({'error': 'All input features must be numeric'}), 400

        input_data = np.array(features).reshape(1, -1)
        input_data_scaled = scaler.transform(input_data)

        # Predictions
        chd_prediction = logreg_chd.predict(input_data_scaled)[0]
        disease_prediction = "No Heart Disease Detected"
        if chd_prediction == 1:
            disease_prediction = label_encoder.inverse_transform(
                logreg_disease.predict(input_data_scaled)
            )[0]

        # Optional save
        if data.get('save') == 'yes':
            name = data.get('name', 'Anonymous')
            stored_data.append({'name': name, 'prediction': disease_prediction})

        # Response
        response = {
            'TenYearCHD': int(chd_prediction),
            'DiseaseType': disease_prediction
        }
        return jsonify(response), 200

    except ValueError as e:
        logging.error(f"Value error: {e}")
        return jsonify({'error': 'Invalid input format'}), 400
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return jsonify({'error': 'Internal server error occurred'}), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email in users_db and check_password_hash(users_db[email]["password"], password):
            session["user"] = email
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password.", "danger")
    
    return render_template("login.html")

@app.route("/oauth_login")
def oauth_login():
    if google.authorized:
        resp = google.get("/oauth2/v2/userinfo")
        user_info = resp.json()
        session["user"] = user_info["email"]
        flash("Logged in using Google!", "success")
    elif github.authorized:
        resp = github.get("/user")
        user_info = resp.json()
        session["user"] = user_info["login"]
        flash("Logged in using GitHub!", "success")
    else:
        flash("OAuth login failed. Please try again.", "danger")
        return redirect(url_for("login"))
    
    return redirect(url_for("home"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        if not email or "@" not in email or "." not in email:
            errors.append("Invalid email format.")
        if email in users_db:
            errors.append("Email already registered.")
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        elif not any(char.isdigit() for char in password):
            errors.append("Password must contain at least one number.")
        elif not any(char.isalpha() for char in password):
            errors.append("Password must contain at least one letter.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return redirect(url_for("signup"))

        users_db[email] = {
            "username": username,
            "password": generate_password_hash(password)
        }
        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for("login"))
    
    user_email = session["user"]
    username = users_db[user_email]["username"]
    return render_template("dashboard.html", username=username, email=user_email)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Route for handling contact form and review submissions."""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if name and email and message:
            contact_entry = {"name": name, "email": email, "message": message}
            contact_messages_db.append(contact_entry)
            logging.info(f"Contact message received: {contact_entry}")
            flash("Your message has been received!", "info")
        
        # Handle review submission
        reviewer = request.form.get('reviewer')
        review_text = request.form.get('review-text')
        rating = request.form.get('rating')
        
        if reviewer and review_text and rating:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:
                    review_entry = {"name": reviewer, "review": review_text, "rating": rating}
                    reviews_db.append(review_entry)
                    logging.info(f"Review added: {review_entry}")
                    flash("Thank you for your review!", "success")
            except ValueError:
                flash("Invalid rating value!", "danger")
        
        return redirect(url_for('contact'))  # Redirect to avoid re-submission on refresh

    # Render contact form with existing reviews
    return render_template('contact.html', reviews=reviews_db)


@app.route('/data')
def display_data():
    logging.info(f"Displaying data: {stored_data}")
    return render_template('data.html', data=stored_data)


if __name__ == '__main__':
    app.run(debug=True)
