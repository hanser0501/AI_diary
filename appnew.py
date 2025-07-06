# ... [其他导入保持不变] ...
from flask import Flask, render_template, request, jsonify, send_from_directory
from openai import OpenAI
import os
import sqlite3
import datetime
import requests


app = Flask(__name__, static_folder='static')

# OpenAI 客户端初始化（请替换为你的实际 API KEY）
client = OpenAI(
    api_key="sk-oovpsxqnpcfalcidxfzqptoehotpgbfdjhjivqxilkqpntop",
    base_url="https://api.siliconflow.cn/v1"
)

# ... [数据库初始化代码保持不变] ...

# 首页
@app.route('/')
def index():
    return render_template('indexmaimai.html')

# 静态文件路由
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# ... [其他路由保持不变] ...

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
        temperature=0.3
    )
    
    mood = mood_response.choices[0].message.content.lower().strip()
    mood_keywords = ['happy', 'sad', 'angry', 'neutral']
    if mood not in mood_keywords:
        mood = 'neutral'
    
    # 第二部分：生成鼓励话语
    encouragement_response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[
            {'role': 'system', 'content': f"根据用户的心情({mood})，写一段体贴的鼓励或安慰的话。保持温暖积极的语气，不超过50字。称呼用户为'亲爱的'。"},
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
    
    # 添加情绪中文翻译
    mood_translation = {
        'happy': '开心',
        'sad': '悲伤',
        'angry': '生气',
        'neutral': '平静'
    }
    
    return jsonify({
        'mood': mood,
        'mood_cn': mood_translation.get(mood, '平静'),
        'song': song,
        'encouragement': encouragement
    })

# ... [其他代码保持不变] ...

if __name__ == '__main__':
    app.run(debug=True)