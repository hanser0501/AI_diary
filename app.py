from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
import sqlite3
import datetime
import requests

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'diary.db')

# 初始化数据库
if not os.access(BASE_DIR, os.W_OK):
    raise PermissionError(f"No write permission in directory: {BASE_DIR}")
def init_db():
    print("Trying to create database at:", DB_PATH)
    if not os.path.exists(BASE_DIR):
        raise Exception("Project base directory does not exist.")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS diary (
                date TEXT PRIMARY KEY,
                content TEXT
            )
        ''')
    print(f"Creating DB at: {DB_PATH}")
init_db()

# 首页
@app.route('/')
def index():
    return render_template('index.html')

# 保存日记
@app.route('/save', methods=['POST'])
def save():
    content = request.json.get('content')
    today = datetime.date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("REPLACE INTO diary (date, content) VALUES (?, ?)", (today, content))
    return jsonify({'status': 'success'})

# 获取所有日记
@app.route('/get_all', methods=['GET'])
def get_all():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT date, content FROM diary ORDER BY date DESC").fetchall()
    return jsonify([{'date': d, 'content': c} for d, c in rows])

client = OpenAI(
    api_key="sk-oovpsxqnpcfalcidxfzqptoehotpgbfdjhjivqxilkqpntop", 
    base_url="https://api.siliconflow.cn/v1"
)

# 情绪分析 + 推荐歌曲
@app.route('/analyze', methods=['POST'])
def analyze():
    content = request.json.get('content')
    responce = client.chat.completions.create(
        # model='Pro/deepseek-ai/DeepSeek-R1',
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[
            {'role': 'user', 'content': f"请分析以下日记内容的用户心情，并返回一个关键词，例如 happy、sad、angry、neutral 等：\n{content}"}
            ],
            stream=True
        )

    result_text = ""
    for chunk in responce:
        if chunk.choices and chunk.choices[0].delta.content:
            result_text += chunk.choices[0].delta.content

    mood_keywords = ['happy', 'sad', 'angry', 'neutral']
    for key in mood_keywords:
        if key in result_text.lower():
            mood = key
            break

    mood_to_song = {
        'happy': {'name': 'Happy - Pharrell Williams', 'url': '/static/happy.mp3'},
        'sad': {'name': 'Someone Like You - Adele', 'url': '/static/sad.mp3'},
        'angry': {'name': 'Lose Yourself - Eminem', 'url': '/static/angry.mp3'},
        'neutral': {'name': 'Let It Be - Beatles', 'url': '/static/neutral.mp3'}
    }
    # mp3 文件放在 static 文件夹下,命名必须与上面一致
    song = mood_to_song.get(mood, mood_to_song['neutral'])
    return jsonify({
        'mood': mood,
        'song': song,
        'ai_reply': result_text.strip()
        })

if __name__ == '__main__':
    app.run(debug=True)
