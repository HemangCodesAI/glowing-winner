from flask import Blueprint, request, jsonify, render_template
from app.utils.otp import generate_otp, verify_otp
from app.models.user import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get('email')
    print("your email is", email)
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    generate_otp(email)
    return jsonify({'message': f'OTP sent to {email}'}), 200

@auth_bp.route('/verify_otp', methods=['POST'])
def verify():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    if verify_otp(email, otp):
        return jsonify({'message': 'OTP verified!'}), 200
    return jsonify({'error': 'Invalid or expired OTP'}), 400

@auth_bp.route('/signup',methods=['GET'])
def signup_page():
    return render_template('signup.html')  

@auth_bp.route('/signup',methods=['POST'])
def signup_user():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    password = data.get('password')
    
    if not all([email, otp, password]):
        return jsonify({'error': 'All fields are required'}), 400

    if not verify_otp(email, otp):
        return jsonify({'error': 'Invalid or expired OTP'}), 400
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 400
    
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # In-memory example — replace with actual DB
    #print(f"✅ User created: {email} with password: {password}")

    return jsonify({'message': f'User {email} registered successfully'}), 200


@auth_bp.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([
        {'id': u.id, 'email': u.email, 'password_hash': u.password_hash}
        for u in users
    ])

@auth_bp.route('/auth', methods=['GET'])
def unified_auth_page():
    return render_template('auth.html')