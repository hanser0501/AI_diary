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

# 删除日记
@app.route('/delete', methods=['POST'])
def delete():
    date = request.json.get('date')
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM diary WHERE date = ?", (date,))
    return jsonify({'status': 'success'})

# 情绪分析 + 推荐歌曲
@app.route('/analyze', methods=['POST'])
def analyze():
    content = request.json.get('content')
    # 第一部分：分析情绪
    mood_response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[
            {'role': 'system', 'content': "你是一个情绪分析助手。请用单个英文单词回答用户的心情，必须是happy、sad、angry、neutral中的一个。"},
            {'role': 'user', 'content': f"分析以下日记内容的心情：\n{content}"}
        ],
        temperature=0.3  # 降低随机性
    )
    
    mood = mood_response.choices[0].message.content.lower().strip()
    mood_keywords = ['happy', 'sad', 'angry', 'neutral']
    if mood not in mood_keywords:
        mood = 'neutral'  # 默认值
    
    # 第二部分：生成鼓励话语
    encouragement_response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[
            {'role': 'system', 'content': f"根据用户的心情({mood})，写一段体贴的鼓励或安慰的话。保持温暖积极的语气，不超过30字。"},
            {'role': 'user', 'content': f"这是我的日记内容：\n{content}"}
        ],
        temperature=0.7
    )
    encouragement = encouragement_response.choices[0].message.content.strip()
    
    # 歌曲推荐
    mood_to_song = {
        'happy': {'name': 'Happy - Pharrell Williams', 'url': '/static/happy.mp3'},
        'sad': {'name': 'Someone Like You - Adele', 'url': '/static/sad.mp3'},
        'angry': {'name': 'Lose Yourself - Eminem', 'url': '/static/angry.mp3'},
        'neutral': {'name': 'Let It Be - Beatles', 'url': '/static/neutral.mp3'}
    }
    song = mood_to_song.get(mood, mood_to_song['neutral'])
    
    return jsonify({
        'mood': mood,
        'song': song,
        'encouragement': encouragement,
        'ai_reply': f"检测到你的心情是{mood}。{encouragement}"
    })

if __name__ == '__main__':
    app.run(debug=True)
