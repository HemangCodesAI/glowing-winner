from dotenv import load_dotenv
load_dotenv()
import os, random, smtplib, time ,re
import base64
from google import genai
from google.genai import types
import json
import sqlite3

def get_chat_history(email, chat_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # find table from ocr table
    cursor.execute("SELECT ocr_table FROM ocr WHERE email = ? AND chat_id = ?", (email, chat_id))
    row = cursor.fetchone()
    if row is not None:
        table = row[0]
    else:
        table = None
    #  fetch chat history from history table
    cursor.execute("SELECT user_chats FROM history WHERE email = ? AND chat_id = ?", (email, chat_id))
    row = cursor.fetchone()
    conn.close()
    # print(email, chat_id)
    print(table)

    if row is not None:
        # Return the list of chat IDs
        existing_chats = json.loads(row[0]) if row[0] else []
        # print(existing_chats)

        return table, existing_chats
    else:
        return table, []

def delete_recent_chat(email, chat_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Check if the row exists
    cursor.execute("SELECT chat_ids FROM recent_chat WHERE email = ?", (email,))
    row = cursor.fetchone()

    if row is not None:
        # Remove the chat_id from the list
        existing_chat_ids = json.loads(row[0]) if row[0] else []
        if chat_id in existing_chat_ids:
            existing_chat_ids.remove(chat_id)
            cursor.execute(
                "UPDATE recent_chat SET chat_ids = ? WHERE email = ?",
                (json.dumps(existing_chat_ids), email)
            )
            print("Chat ID removed from existing entry.")
        else:
            print("Chat ID not found in the list.")

    conn.commit()
    conn.close()
    print("Recent chat deleted.", chat_id)

def get_recent_chats(email):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Check if the row exists
    cursor.execute("SELECT chat_ids FROM recent_chat WHERE email = ?", (email,))
    row = cursor.fetchone()

    if row is not None:
        # Return the list of chat IDs
        existing_chat_ids = json.loads(row[0]) if row[0] else []
        return existing_chat_ids
    else:
        return []

def add_to_ocr_db(email, chat_id, ocr_table,text):
    conn = sqlite3.connect('database.db')
    # print(text)
    cursor = conn.cursor()
    # insert into a new row in the ocr table
    cursor.execute('''
        INSERT INTO ocr (chat_id, email, ocr_table, extracted_text)
        VALUES (?, ?, ?, ?)
        ''', (chat_id, email, ocr_table, text))
    conn.commit()
    conn.close()
    print("Added to OCR DB")

def get_ocr_text(email, chat_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # select the ocr text from the ocr table
    cursor.execute('''
        SELECT extracted_text FROM ocr WHERE email = ? AND chat_id = ?
        ''', (email, chat_id))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None

def add_to_chat_db(email, chat_id, message, response):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Check if the row exists
    cursor.execute("SELECT user_chats FROM history WHERE email = ? AND chat_id = ?", (email, chat_id))
    row = cursor.fetchone()

    # Create a new entry if none exists
    if row is None:
        data = [{"question": message, "answer": response}]
        cursor.execute(
            "INSERT INTO history (chat_id, email, user_chats) VALUES (?, ?, ?)",
            (chat_id, email, json.dumps(data))
        )
        print("New chat entry created.")
    else:
        # Append to existing json content
        existing_data = json.loads(row[0]) if row[0] else []
        existing_data.append({"question": message, "answer": response})
        cursor.execute(
            "UPDATE history SET user_chats = ? WHERE chat_id = ? AND email = ?",
            (json.dumps(existing_data), chat_id, email)
        )
        print("Existing entry updated.")

    conn.commit()
    conn.close()

def add_recent_chat(email, chat_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Check if the row exists
    cursor.execute("SELECT chat_ids FROM recent_chat WHERE email = ?", (email,))
    row = cursor.fetchone()
    print(chat_id)
    if row is None:
        # Create a new entry if no existing row is found
        chat_list = [chat_id]
        cursor.execute(
            "INSERT INTO recent_chat (email, chat_ids) VALUES (?, ?)",
            (email, json.dumps(chat_list))
        )
        print("New recent chat created.")
    else:
        # Append to existing chat IDs if the row exists
        existing_chat_ids = json.loads(row[0]) if row[0] else []
        
        # Add only if the chat_id is not already in the list
        existing_chat_ids.append(chat_id)
        cursor.execute(
            "UPDATE recent_chat SET chat_ids = ? WHERE email = ?",
            (json.dumps(existing_chat_ids), email)
        )
        print("Chat ID added to existing entry.")
    

    conn.commit()
    conn.close()

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
    print("Users table created.")
    # Create the recent chat table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recent_chat (
            email TEXT NOT NULL,
            chat_ids TEXT,
            FOREIGN KEY (email) REFERENCES users(email)
        )
    ''')
    print("Recent chat table created.")
    # Create the OCR table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr (
            chat_id TEXT NOT NULL,
            email TEXT NOT NULL,
            ocr_table TEXT,
            extracted_text TEXT,
            FOREIGN KEY (email) REFERENCES users(email)
        )
    ''')
    print("OCR table created.")
    # Create the history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            chat_id TEXT NOT NULL,
            email TEXT NOT NULL,
            user_chats TEXT,
            FOREIGN KEY (email) REFERENCES users(email)
        )
    ''')
    print("History table created.")
    # Add a test user (optional)
    # cursor.execute('INSERT OR IGNORE INTO users (email, password) VALUES (?, ?)', ('test@example.com', 'password123'))
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

