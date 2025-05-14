from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, random, smtplib, time ,re
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
import base64
from google import genai
from google.genai import types
import json
from pdf2image import convert_from_path
# import tempfile
# import requests
# from PIL import Image
# from pydub import AudioSegment
# from pydub.utils import which
# import sqlite3
# import traceback
# import magic
# import speech_recognition as sr


def generate(path):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    files = [
        # Please ensure that the file is available in local system working direrctory or change the file path.
        client.files.upload(file=path),
    ]
    model = "gemini-2.0-flash"
    template = """

        **OCR and Translation**

        **Original OCR:**

        ```
        [Insert OCR Text Here]
        ```

        **Translated Text:**
        ```
        [Insert english translated Text Here]
        ```

        **JSON Response:**

        ```json
        {
        "[Key 1]": "[Explanation of Key 1]",
        "[Key 2]": "[Explanation of Key 2]",
        "[Key 3]": "[Explanation of Key 3]",
        "[Key 4]": "[Explanation of Key 4]"
        }
        ```

        ---

        **Detailed Explanation of the Problems and Suggestions**

        1. **\[Key 1] (Key: `[Key 1]`)**

        * **Problem:** \[Describe the problem related to Key 1]
        * **JSON Summary:** "\[Explanation of Key 1]"
        * **Why it's a problem:** \[Explain why it's a problem]

        2. **\[Key 2] (Key: `[Key 2]`)**

        * **Problem:** \[Describe the problem related to Key 2]
        * **JSON Summary:** "\[Explanation of Key 2]"
        * **Why it's a problem:** \[Explain why it's a problem]

        3. **\[Key 3] (Key: `[Key 3]`)**

        * **Problem:** \[Describe the problem related to Key 3]
        * **JSON Summary:** "\[Explanation of Key 3]"
        * **Why it's a problem:** \[Explain why it's a problem]

        4. **\[Key 4] (Key: `[Key 4]`)**

        * **Problem:** \[Describe the problem related to Key 4]
        * **JSON Summary:** "\[Explanation of Key 4]"
        * **Why it's a problem:** \[Explain why it's a problem]

        ---

        """
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=files[0].uri,
                    mime_type=files[0].mime_type,
                ),
                types.Part.from_text(text=f"""ocr the image and translate it to english.then process this letter in such a way that i get a json response . in which the problems of the person  who has written the letter is explained . set the key to be the department which should handle that problem and the key is one line summary of the problem . make as many key value pair as many there are problems.answer should be strictly in this format:{template}"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )

    result= client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
        # print(chunk.text, end="")
    return result.text

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'

def process_image(path):
    response= generate(path)
    print(response)
    result = json.loads(response[response.find("```json")+7:response.find("}\n```")+1].replace("\n",""))
    print(result)
    return result,response

def generate_chat(message, lastresponse):
    # use google genai to generate chat response
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )
    model = "gemini-2.0-flash"
    prompt = f"""You are a helpful assistant. Extract the most relevant answer to the question from the document.
                .

        Document:
        {lastresponse}

        Question: {message}
        Answer:"""
    print(prompt)
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
                
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )
    result= client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    return result.text

@app.route('/', methods=['GET', 'POST'])
def upload():
    session['history'] = []
    if request.method == 'POST':
        # image = request.files['image']
        
        image = request.files['file']

        filename = secure_filename(image.filename)
        filepath = f"{UPLOAD_FOLDER}/{filename}"
        image.save(filepath)
        result,response = process_image(filepath)
        history = session.get("history", [])
        history.append((filepath, str(response)))
        # session.clear()

        session["history"] = history
        return jsonify({"ans":result})
    history = session.get("history", [])
    return render_template('upload.html', result=None,histroy=history)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        data = request.json
        message = data.get("message", "")
        # message = request.form['message']
        # Process the message and generate a response
        history = session.get("history", [])
        lastresponse = history[-1][1] if history else None
        # get_chat_response = generate_chat(message, lastresponse)
        # # response = "This is a dummy response to: " + message
        # print(get_chat_response)
        response = generate_chat(message, lastresponse)
        print(response)
        return jsonify({"answer": response})
    else:
        return jsonify({"response": "error"})

if __name__ == '__main__':
    app.run(debug=True)
