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
    # print("Deleting recent chat for email:", email, "chat_id:", chat_id)
    if chat_id != "aLl":
        if row is not None:
            # Remove the chat_id from the list
            existing_chat_ids = json.loads(row[0]) if row[0] else []
            # print(existing_chat_ids)
            # print(chat_id)
            if chat_id in existing_chat_ids:
                existing_chat_ids.remove(chat_id)
                cursor.execute(
                    "UPDATE recent_chat SET chat_ids = ? WHERE email = ?",
                    (json.dumps(existing_chat_ids), email)
                )
                print("Chat ID removed from existing entry.")
            else:
                print("Chat ID not found in the list.")
    else:
        # If chat_id is "aLl", delete the entire row
        cursor.execute("DELETE FROM recent_chat WHERE email = ?", (email,))
        print("All recent chats deleted for email:", email)
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
            "[problem 1 title ]": {
                "explanation": "[Explanation of problem 1]",
                "department": "[Responsible Department for problem 1]"
            },
            "[problem 2 title]": {
                "explanation": "[Explanation of prblem 2]",
                "department": "[Responsible Department for problem 2]"
            },
            "[problem 3 title]": {
                "explanation": "[Explanation of prblem 3]",
                "department": "[Responsible Department for problem 3]"
            },
            "[problem 4 title]": {
                "explanation": "[Explanation of prblem 4]",
                "department": "[Responsible Department for problem 4]"
            }   
        }
        ```

        ---

        **Detailed Explanation of the Problems and Suggestions**

        1. **\[problem 1] **

        * **Problem:** \[Describe the problem related to problem 1]
        * **JSON Summary:** "\[Explanation of problem 1]"
        * **Why it's a problem:** \[Explain why it's a problem]

        2. **\[problem 2] (problem: `[problem 2]`)**

        * **Problem:** \[Describe the problem related to problem 2]
        * **JSON Summary:** "\[Explanation of problem 2]"
        * **Why it's a problem:** \[Explain why it's a problem]

        3. **\[problem 3] (problem: `[problem 3]`)**

        * **Problem:** \[Describe the problem related to problem 3]
        * **JSON Summary:** "\[Explanation of problem 3]"
        * **Why it's a problem:** \[Explain why it's a problem]

        4. **\[problem 4] (problem: `[problem 4]`)**

        * **Problem:** \[Describe the problem related to problem 4]
        * **JSON Summary:** "\[Explanation of problem 4]"
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
                types.Part.from_text(text=f"""ocr the image and translate it to english.then process this letter in such a way that i get a json response .which is this format:a JSON object in the following format:{template}

                Use only the following departments:
                - Dept. of Home Affairs
                - Dept. of Railways
                - Municipal Corporation / Urban Local Bodies
                - Dept. of Food and Civil Supplies
                - Dept. of Road Transport and Highways
                - Dept. of Power
                - Dept. of Education
                - Dept. of Health and Family Welfare
                - Revenue Department
                - Dept. of Labour and Employment
                - Miscellaneous

                Guidelines:
                - the titles of the problems should be space separated and not contain any special characters.even in the keys of the json.
                - Keep the explanation concise (1–2 lines max).
                - Classify each title under the most appropriate department.
                - Use 'Miscellaneous' only if it doesn’t fall under any given department."""),
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

