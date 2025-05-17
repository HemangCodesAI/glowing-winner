from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import utils
app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
utils.init_db()
#home page
@app.route('/home', methods=['GET', 'POST'])
def upload():
    session['history'] = []
    if request.method == 'POST':
        image = request.files['file']
        filename = secure_filename(image.filename)
        filepath = f"{UPLOAD_FOLDER}/{filename}"
        image.save(filepath)
        result,response = utils.process_image(filepath)
        history = session.get("history", [])
        history.append((filepath, str(response)))
        session["history"] = history
        return jsonify({"ans":result})
    history = session.get("history", [])
    return render_template('upload.html', result=None,histroy=history)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        data = request.json
        message = data.get("message", "")
        history = session.get("history", [])
        lastresponse = history[-1][1] if history else None
        response = utils.generate_chat(message, lastresponse)
        # print(response)
        return jsonify({"answer": response})
    else:
        return jsonify({"response": "error"})

@app.route('/')
def signup():
    return render_template('signup.html')

@app.route('/mailcheck', methods=['POST'])
def mailcheck():
    data=request.json
    email = data.get('email', '')
    if utils.user_exists(email):

        return jsonify({"response": "SignIn"})
    else:
        return jsonify({"response": "SignUp"})

@app.route('/dosignup', methods=['POST'])
def dosignup():
    data=request.json
    email = data.get('email', '')
    password = data.get('password', '')
    utils.create_user(email, password)
    session['email'] = email
    return jsonify({"message": "SignUp Success","redirect": "/home"})

@app.route('/dologin',methods=['POST'])
def dologin():
    data=request.json
    email = data.get('email', '')
    password = data.get('password', '')
    if utils.check_password(email, password):
        session['email'] = email

        return jsonify({"response": "Login Success", "redirect": "/home"})
    else:
        return jsonify({"response": "Login Failed"})
if __name__ == '__main__':
    app.run(debug=True)
