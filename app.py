import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, abort, send_from_directory
from werkzeug.utils import secure_filename
import utils
import json
import shutil
from datetime import datetime
import sqlite3
def get_files(email, department):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # select the ocr table from the ocr table
    cursor.execute('''
        SELECT chat_id FROM ocr WHERE email = ?  AND department = ?
        ''', (email, department))
    result = cursor.fetchall()
    for i in range(len(result)):
        result[i] = result[i][0]
    conn.close()
    if result:
        return result
    else:
        return []
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
    return jsonify({"message": "SignUp Success","redirect": "/cmo"})

@app.route('/dologin',methods=['POST'])
def dologin():
    data=request.json
    email = data.get('email', '')
    password = data.get('password', '')
    if utils.check_password(email, password):
        session['email'] = email

        return jsonify({"response": "Login Success", "redirect": "/cmo"})
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
    # print(form_data)
    return render_template('web_form.html', form_data=json.loads(json.dumps(form_data)))



# 2. (Optional) Restrict allowed extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "csv"}

# 1. Where to save uploads (adjust as needed)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")  # e.g., /path/to/your/project/uploads
DEPT_FILES_BASE = os.path.join(BASE_DIR, "department_files")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit (optional)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

@app.route('/cmo', methods=['GET', 'POST'])
def cmo():
    print("Accessed CMO route")
    if request.method == "POST":
        print("Received POST request for file upload")
        # 3a. Ensure we got a file part
        if "file" not in request.files:
            flash("No file part in request")
            print("No file part in request")
            return redirect(request.url)

        file = request.files["file"]

        # 3b. Did the user actually select something?
        if file.filename == "":
            flash("No file chosen")
            print("No file chosen")
            return redirect(request.url)

        # 3c. (Optional) Check extension
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)
            print(f"File saved to {save_path}")

            print("file sent for classification")
            result,response = utils.process_image(save_path)
            
            # Extract department from the response JSON
            Department = response.get("Department", "unknown")
            print(f"Department extracted: {Department}")
            departments=["public-health-engineering","panchayati-raj","local-self-government(municipal-bodies)","revenue","social-justice-and-empowerment","food-civil-supplies-and-consumer-affairs-department","police","mgnrega","rural-development","medical-and-health","cooperative","skills,-employment-and-entrepreneurship","public-works-(pwd)","labour","women-and-child-development","secondary-education","economics-and-statistics","elementry-education","information-tech-and-ommunication","agriculture","excise"]
            department = Department.lower().replace(" ", "-").replace("&", "and")
            if department not in departments:
                department = "miscellaneous"
            # Create department-specific folder path
            dept_folder = os.path.join(DEPT_FILES_BASE, department)

            # Check if department folder exists, if not use "unknown"
            if not os.path.exists(dept_folder):
                os.makedirs(dept_folder, exist_ok=True)

            # Move the file to the appropriate department folder
            dest_path = os.path.join(dept_folder, filename)
            # Check if file already exists in destination
            if os.path.exists(dest_path):
                # Generate timestamp-based filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"
                dest_path = os.path.join(dept_folder, filename)
            utils.add_to_ocr_db(session['email'], filename, str(result), str(response), department)
            session['chat_id'] = filename
            shutil.move(save_path, dest_path)
            print(f"File moved to {dest_path}")
            # 3d. Optionally, you can store the file path in a database or session

            return redirect(url_for("departments", selected_dept=department))
        else:
            flash(f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
            print("File type not allowed")
            return redirect(request.url)

    # If GET, simply render the form
    return render_template("document_dashboard.html")

@app.route('/departments', methods=['GET', 'POST'])
def departments():
    selected_dept = request.args.get("selected_dept", "")
    
    return render_template('departments.html', selected_dept=selected_dept)

@app.route("/departments/<dept>")
def department_files(dept):
    """
    Given a department name (e.g. “public-health”), look into
    department_files/public-health/, list all files there, and pass them
    to department_files.html for display in a table.
    """
    # 1) Construct the absolute path to that department’s folder
    folder_path = os.path.join(DEPT_FILES_BASE, dept)

    # 2) If it’s not an existing directory, return 404
    if not os.path.isdir(folder_path):
        abort(404, description=f"No such department: {dept}")

    # 3) List all files inside (ignore subdirectories)
    print(session.get('email'), dept)
    all_items = get_files(session['email'],dept)
    file_list = [
        fname for fname in all_items
        if os.path.isfile(os.path.join(folder_path, fname))
    ]

    # 4) Render a template that shows a table of these file names
    return render_template(
        "department_files.html",
        department=dept,
        files=file_list
    )

@app.route("/departments/<dept>/files/<filename>")
def serve_file(dept, filename):
    """
    Sends back the file so it can be embedded inline. Do NOT force attachment.
    """
    folder_path = os.path.join(DEPT_FILES_BASE, dept)
    if not os.path.isdir(folder_path):
        abort(404)

    safe_path = os.path.join(folder_path, filename)
    if not os.path.isfile(safe_path):
        abort(404)

    # send_from_directory with as_attachment=False so browser may display inline:
    return send_from_directory(folder_path, filename, as_attachment=False)

@app.route("/departments/<dept>/view/<filename>")
def view_file(dept, filename):
    form_data = utils.get_form_data(session.get('email'),session.get('chat_id'))
    print(session.get('email'),session.get('chat_id'))
    # print(form_data)
    folder_path = os.path.join(DEPT_FILES_BASE, dept)
    if not os.path.isdir(folder_path):
        abort(404)

    safe_path = os.path.join(folder_path, filename)
    if not os.path.isfile(safe_path):
        abort(404)
    # print(form_data)
    # python_obj = ast.literal_eval(form_data)
    # json_string = json.dumps(python_obj)
    # print(json.loads(json_string))
    # Pass both dept and filename so template can build URLs
    return render_template("file_view.html", department=dept, filename=filename, form_data=form_data)
if __name__ == '__main__':
    app.run(debug=True)