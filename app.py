from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, random, smtplib, time ,re
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
import base64
from google import genai
from google.genai import types
import json

import ollama
import base64

# Step 1: Read and encode the image as base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

# Step 2: Send image and prompt to llava model via Ollama's Python SDK
def generate(image_path):
    image_b64 = encode_image_to_base64(image_path)
    
    response = ollama.chat(
        model="gemma3:4b",
        messages=[
            {
                "role": "user",
                "content": """ocr the image and translate it to english.then process this letter in such a way that i get a json response . in which the problems of the person  who has written the letter is explained . set the key to be the department which should handle that problem and the key is one line summary of the problem . make as many key value pair as many there are problems""",
                "images": [image_b64]
            }
        ]
    )
    
    return response["message"]["content"]
# def generate(path):
#     client = genai.Client(
#         api_key=os.environ.get("GEMINI_API_KEY"),
#     )

#     files = [
#         # Please ensure that the file is available in local system working direrctory or change the file path.
#         client.files.upload(file=path),
#     ]
#     model = "gemini-2.0-flash"
#     contents = [
#         types.Content(
#             role="user",
#             parts=[
#                 types.Part.from_uri(
#                     file_uri=files[0].uri,
#                     mime_type=files[0].mime_type,
#                 ),
#                 types.Part.from_text(text="""ocr the image and translate it to english.then process this letter in such a way that i get a json response . in which the problems of the person  who has written the letter is explained . set the key to be the department which should handle that problem and the key is one line summary of the problem . make as many key value pair as many there are problems"""),
#             ],
#         ),
#     ]
#     generate_content_config = types.GenerateContentConfig(
#         response_mime_type="text/plain",
#     )

#     result= client.models.generate_content(
#         model=model,
#         contents=contents,
#         config=generate_content_config,
#     )
#         # print(chunk.text, end="")
#     return result.text

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'

# Email OTP sender


# Dummy image processing
def process_image(path):
    response= generate(path)
    # print(response)
    result = json.loads(response[response.find("```json")+7:response.find("}\n```")+1].replace("\n",""))
    # print(result)
    return result



@app.route('/', methods=['GET', 'POST'])
def upload():

    if request.method == 'POST':
        image = request.files['image']
        filename = secure_filename(image.filename)
        filepath = f"{UPLOAD_FOLDER}/{filename}"
        image.save(filepath)
        result = process_image(filepath)
        history = session.get("history", [])
        history.append((filepath, result))
        session.clear()

        session["history"] = history
        return render_template('upload.html', result=result,image=image,history=history)
    history = session.get("history", [])
    return render_template('upload.html', result=None,histroy=history)

if __name__ == '__main__':
    app.run(debug=True)
