from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import utils
import json
app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
utils.init_db()
#home page
@app.route('/')
def signup():
    return render_template('signup.html')

@app.route('/home', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        image = request.files['file']
        filename = secure_filename(image.filename)
        filepath = f"{UPLOAD_FOLDER}/{filename}"
        image.save(filepath)
        result,response = utils.process_image(filepath)
        utils.add_to_ocr_db(session['email'], filename, str(result), str(response))
        session['chat_id'] = filename
        return jsonify({"ans":result,"chat_id":filename})
    return render_template('upload.html', result=None,histroy=None)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        data = request.json
        message = data.get("message", "")
        ocr_text=utils.get_ocr_text(session['email'], session['chat_id'])
        response = utils.generate_chat(message, ocr_text)
        # print(response)
        utils.add_to_chat_db(session['email'], session['chat_id'], message, response)
        return jsonify({"answer": response})
    else:
        return jsonify({"response": "error"})

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

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('chat_id', None)
    return redirect(url_for('signup'))

@app.route('/store-recent-chat', methods=['POST'])
def store_recent_chat():
    data = request.json
    email = session.get('email')
    chat_id = data
    utils.add_recent_chat(email, chat_id)
    return jsonify({"response": "Chat stored successfully"})

@app.route('/delete-recent-chats', methods=['POST'])
def delete_recent_chats():
    data = request.json
    email = session.get('email')
    chat_id = data.get('chatId', '')
    # print(email, chat_id)
    utils.delete_recent_chat(email, chat_id)
    return jsonify({"response": "Chat deleted successfully"})

@app.route('/get-recent-chats', methods=['POST'])
def get_recent_chats():
    email = session.get('email')
    recent_chats = utils.get_recent_chats(email)
    return jsonify({"recent_chats": recent_chats})

@app.route('/get-chat-history', methods=['POST'])
def get_chat_history():
    email = session.get('email')
    chat_id = request.json
    table, chat_history = utils.get_chat_history(email, chat_id)
    return jsonify({"chats": chat_history,"table": json.loads(json.dumps(table))})

@app.route('/web-form', methods=['GET', 'POST'])
def web_form():
    form_data = utils.get_form_data(session.get('email'),session.get('chat_id'))
    print(form_data)
    return render_template('web_form.html', form_data=json.loads(json.dumps(form_data)))
if __name__ == '__main__':
    app.run(debug=True)
