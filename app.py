# ... [其他导入保持不变] ...
from flask import Flask, render_template, request, jsonify, send_from_directory
from openai import OpenAI
import os
import sqlite3
import datetime
import requests


app = Flask(__name__, static_folder='static')

# 初始化数据库
def init_db():
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS diary
                 (date TEXT PRIMARY KEY, content TEXT)''')
    conn.commit()
    conn.close()

init_db()  # 应用启动时调用

# 获取所有日记
@app.route('/get_all')
def get_all():
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("SELECT date, content FROM diary ORDER BY date DESC")
    diaries = [{'date': row[0], 'content': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(diaries)

# 保存日记
@app.route('/save', methods=['POST'])
def save():
    content = request.json.get('content')
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("INSERT INTO diary (date, content) VALUES (?, ?)", (date, content))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# 删除日记
@app.route('/delete', methods=['POST'])
def delete():
    date = request.json.get('date')
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("DELETE FROM diary WHERE date=?", (date,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# OpenAI 客户端初始化（请替换为你的实际 API KEY）
client = OpenAI(
    api_key="sk-oovpsxqnpcfalcidxfzqptoehotpgbfdjhjivqxilkqpntop",
    base_url="https://api.siliconflow.cn/v1"
)

# ... [数据库初始化代码保持不变] ...

# 首页
@app.route('/')
def index():
    return render_template('index.html')

# 静态文件路由
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# ... [其他路由保持不变] ...

# 情绪分析 + 推荐歌曲 + 颜色推荐 + 诗歌生成
@app.route('/analyze', methods=['POST'])
def analyze():
    content = request.json.get('content')
    # 第一部分：分析情绪（保持不变）
    mood_response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[
            {'role': 'system', 'content': "你是一个情绪分析助手。请用单个英文单词回答用户的心情，必须是happy、sad、angry、neutral中的一个。"},
            {'role': 'user', 'content': f"分析以下日记内容的心情：\n{content}"}
        ],
        temperature=0.3
    )
    
    mood = mood_response.choices[0].message.content.lower().strip()
    mood_keywords = ['happy', 'sad', 'angry', 'neutral']
    if mood not in mood_keywords:
        mood = 'neutral'
    
    # 第二部分：生成鼓励话语（保持不变）
    encouragement_response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[
            {'role': 'system', 'content': f"根据用户的心情({mood})，写一段体贴的鼓励或安慰的话。保持温暖积极的语气，不超过50字。称呼用户为'亲爱的'。"},
            {'role': 'user', 'content': f"这是我的日记内容：\n{content}"}
        ],
        temperature=0.7
    )
    encouragement = encouragement_response.choices[0].message.content.strip()
    
    # 第三部分：歌曲推荐（保持不变）
    mood_to_song = {
        'happy': {'name': 'Happy - Pharrell Williams', 'url': '/static/happy.mp3'},
        'sad': {'name': 'Someone Like You - Adele', 'url': '/static/sad.mp3'},
        'angry': {'name': 'Lose Yourself - Eminem', 'url': '/static/angry.mp3'},
        'neutral': {'name': 'Let It Be - Beatles', 'url': '/static/neutral.mp3'}
    }
    song = mood_to_song.get(mood, mood_to_song['neutral'])
    
    # 新增：颜色映射（主色+渐变色）
    color_mapping = {
        'happy': {
            'primary': '#3498db',       # 冷色主色（蓝色）
            'gradient': 'linear-gradient(135deg, #e6f2ff 0%, #d1e9ff 100%)',  # 浅蓝渐变
            'text': '#2c3e50',          # 深色文字
            'recommended': '蓝色或紫色等冷色系' # 推荐冷色系
        },
        'sad': {
            'primary': '#f39c12',       # 暖色主色（橙色）
            'gradient': 'linear-gradient(135deg, #fff6e3 0%, #ffe9c7 100%)',  # 浅橙渐变
            'text': '#2c3e50',          # 深色文字
            'recommended': '橙色、黄色等暖色系' # 推荐暖色系
        },
        'angry': {
            'primary': '#2980b9',       # 冷色主色（深蓝）
            'gradient': 'linear-gradient(135deg, #e6f2ff 0%, #d1e9ff 100%)',  # 浅蓝渐变
            'text': '#2c3e50',          # 深色文字
            'recommended': '蓝色或紫色等冷色系' # 推荐冷色系
        },
        'neutral': {
            'primary': '#7f8c8d',       # 灰色主色
            'gradient': 'linear-gradient(135deg, #f5f7fa 0%, #eaecee 100%)',  # 浅灰渐变
            'text': '#2c3e50',          # 深色文字
            'recommended': '中性色系'   # 推荐色系
        }
    }
    colors = color_mapping.get(mood, color_mapping['neutral'])
    
    # 新增：海子风格诗歌生成
    poem_response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[
            {'role': 'system', 'content': """你是诗人海子，用他的风格将用户日记写成诗。
            风格特点：充满对生活的热爱、自然意象（太阳、麦子、土地、河流）、
            质朴而富有力量的语言，短句为主，结尾积极温暖。"""},
            {'role': 'user', 'content': f"根据以下日记内容写一首诗：\n{content}"}
        ],
        temperature=0.8
    )
    poem = poem_response.choices[0].message.content.strip()
    
    # 返回结果新增颜色和诗歌信息
    return jsonify({
        'mood': mood,
        'mood_cn': {'happy': '开心', 'sad': '悲伤', 'angry': '生气', 'neutral': '平静'}.get(mood, '平静'),
        'song': song,
        'encouragement': encouragement,
        'colors': colors,          # 新增颜色信息
        'poem': poem               # 新增诗歌信息
    })

# ... [其他代码保持不变] ...

if __name__ == '__main__':
    app.run(debug=True)