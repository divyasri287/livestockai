from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import json
import uuid
import hashlib
import datetime
from PIL import Image
from model.breed_classifier import load_breed_model, predict_breed, BREED_LABELS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'breed_classifier.h5')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
USERS_FILE = os.path.join(BASE_DIR, 'users.json')

app = Flask(__name__)
app.secret_key = 'livestockai-production-secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = load_breed_model(MODEL_PATH)

BREED_DETAILS = {
    'Gir': {
        'category': 'Dairy',
        'origin': 'Gujarat, India',
        'characteristics': 'High milk yield, docile temperament, heat tolerant.',
        'milk_production': 'High',
        'animal_type': 'Cattle'
    },
    'Sahiwal': {
        'category': 'Dairy',
        'origin': 'Punjab, India',
        'characteristics': 'Good milk yield, disease resistant, adaptive.',
        'milk_production': 'High',
        'animal_type': 'Cattle'
    },
    'Ongole': {
        'category': 'Dual-purpose',
        'origin': 'Andhra Pradesh, India',
        'characteristics': 'Robust frame, drought resistance, versatile.',
        'milk_production': 'Moderate',
        'animal_type': 'Cattle'
    },
    'Red Sindhi': {
        'category': 'Dairy',
        'origin': 'Sindh region',
        'characteristics': 'Heat tolerant, consistent milk yield, gentle nature.',
        'milk_production': 'Moderate',
        'animal_type': 'Cattle'
    },
    'Murrah': {
        'category': 'Dairy',
        'origin': 'Haryana / Punjab, India',
        'characteristics': 'High fat content, muscular build, strong lactation.',
        'milk_production': 'Very High',
        'animal_type': 'Buffalo'
    },
    'Surti': {
        'category': 'Dairy',
        'origin': 'Gujarat, India',
        'characteristics': 'Compact build, gentle temperament, good fat content.',
        'milk_production': 'Moderate',
        'animal_type': 'Buffalo'
    }
}


def load_json(file_path, default_value):
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as handle:
            json.dump(default_value, handle, indent=2)
        return default_value

    with open(file_path, 'r', encoding='utf-8') as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError:
            return default_value


def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2)


def load_history():
    return load_json(HISTORY_FILE, [])


def save_history(records):
    save_json(HISTORY_FILE, records)


def append_history(record):
    history = load_history()
    history.insert(0, record)
    save_history(history)


def load_users():
    return load_json(USERS_FILE, [])


def save_users(users):
    save_json(USERS_FILE, users)


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def find_user(username):
    for user in load_users():
        if user.get('username') == username:
            return user
    return None


def compute_stats(records):
    total = len(records)
    confidence_values = [row.get('confidence', 0) for row in records if row.get('confidence') is not None]
    average_confidence = f"{(sum(confidence_values) / len(confidence_values)):.1f}%" if confidence_values else '0%'
    breed_counts = {}
    source_counts = {}
    category_counts = {}

    for record in records:
        breed_counts[record['breed']] = breed_counts.get(record['breed'], 0) + 1
        source_counts[record['source']] = source_counts.get(record['source'], 0) + 1
        category_counts[record['category']] = category_counts.get(record['category'], 0) + 1

    sorted_breeds = sorted(breed_counts.items(), key=lambda item: item[1], reverse=True)
    sorted_sources = sorted(source_counts.items(), key=lambda item: item[1], reverse=True)
    sorted_categories = sorted(category_counts.items(), key=lambda item: item[1], reverse=True)

    return {
        'total_predictions': total,
        'average_confidence': average_confidence,
        'breed_count': len(breed_counts),
        'user_count': len(load_users()),
        'top_breed': sorted_breeds[0][0] if sorted_breeds else 'N/A',
        'top_category': sorted_categories[0][0] if sorted_categories else 'N/A',
        'top_source': sorted_sources[0][0] if sorted_sources else 'N/A',
        'breed_labels': [item[0] for item in sorted_breeds],
        'breed_values': [item[1] for item in sorted_breeds],
        'source_labels': [item[0] for item in sorted_sources],
        'source_values': [item[1] for item in sorted_sources],
        'recent_predictions': records[:5]
    }


def create_result_record(prediction, confidence, source):
    details = BREED_DETAILS.get(prediction, {})
    return {
        'id': uuid.uuid4().hex,
        'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        'breed': prediction,
        'confidence': round(float(confidence) * 100, 1),
        'category': details.get('category', 'Unknown'),
        'origin': details.get('origin', 'Unknown'),
        'characteristics': details.get('characteristics', 'No additional details available.'),
        'milk_production': details.get('milk_production', 'N/A'),
        'animal_type': details.get('animal_type', 'Cattle'),
        'source': source
    }

@app.route('/')
def home():
    stats = compute_stats(load_history())
    return render_template('index.html', page='home', user=session.get('user'), stats=stats)


@app.route('/detect')
def detect():
    return render_template('detection.html', page='detect', user=session.get('user'))


@app.route('/result')
def result_page():
    return render_template('result.html', page='result', user=session.get('user'), last_prediction=session.get('last_prediction'))


@app.route('/camera')
def camera():
    return render_template('camera.html', page='camera', user=session.get('user'))


@app.route('/history')
def history():
    return render_template('history.html', page='history', user=session.get('user'), records=load_history())


@app.route('/dashboard')
def dashboard():
    stats = compute_stats(load_history())
    return render_template('dashboard.html', page='dashboard', user=session.get('user'), stats=stats)


@app.route('/admin')
def admin():
    if not session.get('user'):
        flash('Please sign in to access the admin panel.')
        return redirect(url_for('login'))

    stats = compute_stats(load_history())
    return render_template('admin.html', page='admin', user=session.get('user'), stats=stats, users=load_users())


@app.route('/admin/clear', methods=['POST'])
def clear_history():
    if not session.get('user'):
        return redirect(url_for('login'))

    save_history([])
    flash('Prediction history cleared successfully.')
    return redirect(url_for('admin'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = find_user(username)

        if user and user.get('password') == hash_password(password):
            session['user'] = username
            flash('Welcome back, {}!'.format(username))
            return redirect(url_for('home'))

        flash('Invalid username or password.')

    return render_template('login.html', page='login', user=session.get('user'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not email or not password:
            flash('Please complete all fields.')
            return redirect(url_for('register'))

        if find_user(username):
            flash('Username is already taken.')
            return redirect(url_for('register'))

        users = load_users()
        users.append({
            'username': username,
            'email': email,
            'password': hash_password(password)
        })
        save_users(users)
        session['user'] = username
        flash('Account created successfully. Welcome, {}!'.format(username))
        return redirect(url_for('home'))

    return render_template('register.html', page='register', user=session.get('user'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/about')
def about():
    return render_template('about.html', page='about', user=session.get('user'))


@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided.'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400

    filename = secure_filename(file.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(image_path)

    try:
        image = Image.open(image_path).convert('RGB')
        prediction, confidence = predict_breed(model, image)
        source = request.form.get('source', 'Upload')
        record = create_result_record(prediction, confidence, source)
        append_history(record)
        session['last_prediction'] = record
        return jsonify(record)
    except Exception as ex:
        return jsonify({'error': str(ex)}), 500


if __name__ == '__main__':
    app.run(debug=True)
