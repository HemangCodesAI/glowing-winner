from dotenv import load_dotenv
load_dotenv()
import os, random, smtplib, time ,re
import base64
from google import genai
from google.genai import types
import json
import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Create a users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Add a test user (optional)
    cursor.execute('INSERT OR IGNORE INTO users (email, password) VALUES (?, ?)', ('test@example.com', 'password123'))
    conn.commit()
    conn.close()
    print("Database initialized.")

def user_exists(email):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    print("User exists:", user is not None)
    return user is not None

def create_user(email, password):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        print("User created successfully.")
    except sqlite3.IntegrityError:
        print("User already exists.")
    finally:
        conn.close()

def check_password(email, password):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    print(email,password)
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    conn.close()
    print("Password check:", user is not None)
    return user is not None

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

def process_image(path):
    response= generate(path)
    # print(response)
    result = json.loads(response[response.find("```json")+7:response.find("}\n```")+1].replace("\n",""))
    # print(result)
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

