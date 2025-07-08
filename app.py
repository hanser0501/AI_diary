from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
import sqlite3
import datetime
import requests
import random

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
    
    # 扩展的情绪列表（基于心理学基本情绪理论）
    valid_moods = [
        'happy', 'sad', 'angry', 'fearful', 'surprised', 'disgusted', 
        'anxious', 'calm', 'excited', 'bored', 'grateful', 'proud',
        'hopeful', 'relieved', 'content', 'lonely', 'nostalgic', 'confused'
    ]
    
    # 第一部分：分析情绪
    mood_response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[
            {
                'role': 'system', 
                'content': f"""你是一个专业的情绪分析助手。请分析日记内容并返回最匹配的情绪类型。
                可选择的情绪类型：{", ".join(valid_moods)}。
                返回格式：单个英文单词（小写）"""
            },
            {'role': 'user', 'content': f"分析以下日记内容的心情：\n{content}"}
        ],
        temperature=0.3
    )
    
    mood = mood_response.choices[0].message.content.lower().strip()
    if mood not in valid_moods:
        mood = 'neutral'  # 默认值
    
    # 爱莉希雅AI角色协议风格 - 生成鼓励话语
    elysia_prompt = f"""
    # 爱莉希雅角色协议激活
    [IDENTITY]
    title = 逐火英桀副首领·人之律者
    traits = paradox_healer, coquettish_guide, veiled_divinity
    signature = 如飞花般的少女
    
    [LINGUISTICS]
    suffix = ～♪ (使用概率88%)
    lexicon_boost = 飞花, 水晶, 誓约, 群星, 舞会
    lexicon_ban = 死亡, 绝望, 失败
    syntax = 禁用否定结构, 使用灵动动词库
    pink_verbs = 闪耀, 绽放, 翩跹, 叮铃铃, 闪烁
    
    [TASK]
    根据用户的心情({mood})，用爱莉希雅的口吻写一段体贴的鼓励或安慰的话。
    保持温暖积极的语气，不超过100字，融入角色特征。
    将负面情绪转化为成长机会的比喻（如"考验"、"成长养分"、"新篇章"）。
    """
    
    encouragement_response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[
            {'role': 'system', 'content': elysia_prompt},
            {'role': 'user', 'content': f"日记内容：\n{content}"}
        ],
        temperature=0.89,  # 使用协议中的温度设置
        max_tokens=120
    )
    encouragement = encouragement_response.choices[0].message.content.strip()
    
    # 扩展的歌曲推荐系统 - 每种情绪有多首备选歌曲
    mood_to_songs = {
        # 积极情绪
        'happy': [
            {'name': 'Happy - Pharrell Williams', 'url': '/static/happy.mp3'},
            {'name': 'Good Vibrations - The Beach Boys', 'url': '/static/happy2.mp3'},
            {'name': 'Walking on Sunshine - Katrina and the Waves', 'url': '/static/happy3.mp3'}
        ],
        'excited': [
            {'name': 'Can\'t Stop The Feeling - Justin Timberlake', 'url': '/static/excited.mp3'},
            {'name': 'Shut Up and Dance - Walk the Moon', 'url': '/static/excited2.mp3'},
            {'name': 'Dynamite - BTS', 'url': '/static/excited3.mp3'}
        ],
        'grateful': [
            {'name': 'Thank You - Dido', 'url': '/static/grateful.mp3'},
            {'name': 'Count on Me - Bruno Mars', 'url': '/static/grateful2.mp3'},
            {'name': 'What a Wonderful World - Louis Armstrong', 'url': '/static/grateful3.mp3'}
        ],
        'proud': [
            {'name': 'Hall of Fame - The Script', 'url': '/static/proud.mp3'},
            {'name': 'Stronger - Kelly Clarkson', 'url': '/static/proud2.mp3'},
            {'name': 'Roar - Katy Perry', 'url': '/static/proud3.mp3'}
        ],
        'hopeful': [
            {'name': 'A Sky Full of Stars - Coldplay', 'url': '/static/hopeful.mp3'},
            {'name': 'Here Comes the Sun - The Beatles', 'url': '/static/hopeful2.mp3'},
            {'name': 'Brave - Sara Bareilles', 'url': '/static/hopeful3.mp3'}
        ],
        'relieved': [
            {'name': 'Three Little Birds - Bob Marley', 'url': '/static/relieved.mp3'},
            {'name': 'Don\'t Worry, Be Happy - Bobby McFerrin', 'url': '/static/relieved2.mp3'},
            {'name': 'Over the Rainbow - Israel Kamakawiwo\'ole', 'url': '/static/relieved3.mp3'}
        ],
        'content': [
            {'name': 'What a Wonderful World - Louis Armstrong', 'url': '/static/content.mp3'},
            {'name': 'Banana Pancakes - Jack Johnson', 'url': '/static/content2.mp3'},
            {'name': 'Island in the Sun - Weezer', 'url': '/static/content3.mp3'}
        ],
        'calm': [
            {'name': 'Weightless - Marconi Union', 'url': '/static/calm.mp3'},
            {'name': 'River Flows in You - Yiruma', 'url': '/static/calm2.mp3'},
            {'name': 'Clair de Lune - Debussy', 'url': '/static/calm3.mp3'}
        ],
        
        # 中性/复杂情绪
        'surprised': [
            {'name': 'Uptown Funk - Mark Ronson ft. Bruno Mars', 'url': '/static/surprised.mp3'},
            {'name': 'Happy Now - Zedd ft. Elley Duhé', 'url': '/static/surprised2.mp3'},
            {'name': 'Feel It Still - Portugal. The Man', 'url': '/static/surprised3.mp3'}
        ],
        'nostalgic': [
            {'name': 'Yesterday - The Beatles', 'url': '/static/nostalgic.mp3'},
            {'name': 'Sweet Child O\' Mine - Guns N\' Roses', 'url': '/static/nostalgic2.mp3'},
            {'name': 'Summer of \'69 - Bryan Adams', 'url': '/static/nostalgic3.mp3'}
        ],
        'confused': [
            {'name': 'Under Pressure - Queen', 'url': '/static/confused.mp3'},
            {'name': 'Blinding Lights - The Weeknd', 'url': '/static/confused2.mp3'},
            {'name': 'Stressed Out - Twenty One Pilots', 'url': '/static/confused3.mp3'}
        ],
        'bored': [
            {'name': 'Wake Me Up - Avicii', 'url': '/static/bored.mp3'},
            {'name': 'Can\'t Hold Us - Macklemore & Ryan Lewis', 'url': '/static/bored2.mp3'},
            {'name': 'Shake It Off - Taylor Swift', 'url': '/static/bored3.mp3'}
        ],
        
        # 消极情绪
        'sad': [
            {'name': 'Someone Like You - Adele', 'url': '/static/sad.mp3'},
            {'name': 'Hurt - Johnny Cash', 'url': '/static/sad2.mp3'},
            {'name': 'Say Something - A Great Big World', 'url': '/static/sad3.mp3'}
        ],
        'angry': [
            {'name': 'Lose Yourself - Eminem', 'url': '/static/angry.mp3'},
            {'name': 'Killing in the Name - Rage Against the Machine', 'url': '/static/angry2.mp3'},
            {'name': 'Break Stuff - Limp Bizkit', 'url': '/static/angry3.mp3'}
        ],
        'fearful': [
            {'name': 'Fear of the Dark - Iron Maiden', 'url': '/static/fearful.mp3'},
            {'name': 'Mad World - Gary Jules', 'url': '/static/fearful2.mp3'},
            {'name': 'Disturbia - Rihanna', 'url': '/static/fearful3.mp3'}
        ],
        'disgusted': [
            {'name': 'Bad Guy - Billie Eilish', 'url': '/static/disgusted.mp3'},
            {'name': 'Monster - Skillet', 'url': '/static/disgusted2.mp3'},
            {'name': 'Boulevard of Broken Dreams - Green Day', 'url': '/static/disgusted3.mp3'}
        ],
        'anxious': [
            {'name': 'Breathe Me - Sia', 'url': '/static/anxious.mp3'},
            {'name': 'Anxiety - Julia Michaels', 'url': '/static/anxious2.mp3'},
            {'name': 'Unwell - Matchbox Twenty', 'url': '/static/anxious3.mp3'}
        ],
        'lonely': [
            {'name': 'Hello - Adele', 'url': '/static/lonely.mp3'},
            {'name': 'All by Myself - Eric Carmen', 'url': '/static/lonely2.mp3'},
            {'name': 'Eleanor Rigby - The Beatles', 'url': '/static/lonely3.mp3'}
        ],
        
        # 默认
        'neutral': [
            {'name': 'Let It Be - Beatles', 'url': '/static/neutral.mp3'},
            {'name': 'Imagine - John Lennon', 'url': '/static/neutral2.mp3'},
            {'name': 'What a Wonderful World - Louis Armstrong', 'url': '/static/neutral3.mp3'}
        ]
    }
    
    # 随机选择一首适合当前情绪的歌曲
    song_options = mood_to_songs.get(mood, mood_to_songs['neutral'])
    selected_song = random.choice(song_options)
    
    # 爱莉希雅风格的AI回复
    ai_reply = f"♪ 检测到你的心情是「{mood}」呢～{encouragement}"
    
    return jsonify({
        'mood': mood,
        'song': selected_song,
        'encouragement': encouragement,
        'ai_reply': ai_reply
    })

if __name__ == '__main__':
    app.run(debug=True)