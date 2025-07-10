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
            {'name': 'Ed Sheeran - Galway Girl ', 'url': '/static/happy2.mp3'},
            {'name': 'Troye Sivan - YOUTH', 'url': '/static/happy3.mp3'}
        ],
        'excited': [
            {'name': 'Hillsong Young & Free - Wake', 'url': '/static/excited.mp3'},
            {'name': 'RADWIMPS - 前前前世', 'url': '/static/excited2.mp3'},
            {'name': 'Taio Cruz _ Flo Rida - Hangover', 'url': '/static/excited3.mp3'}
        ],
        'grateful': [
            {'name': 'YOASOBI - もしも命が描けたら (若能描绘生命)', 'url': '/static/grateful.mp3'},
            {'name': '雨のパレード - morning (モーニング)', 'url': '/static/grateful2.mp3'},
            {'name': '周杰伦 - 晴天', 'url': '/static/grateful3.mp3'}
        ],
        'proud': [
            {'name': 'Hall of Fame - The Script', 'url': '/static/proud.mp3'},
            {'name': 'James Carter _ Nevve - Hands in the Fire (Explicit)', 'url': '/static/proud2.mp3'},
            {'name': 'Stephen William Cornish _ Amanda Leigh Wilson - Stronger Than You Know', 'url': '/static/proud3.mp3'}
        ],
        'hopeful': [
            {'name': 'A Sky Full of Stars - Coldplay', 'url': '/static/hopeful.mp3'},
            {'name': 'Asher Monroe - Here With You', 'url': '/static/hopeful2.mp3'},
            {'name': 'Fall Out Boy - Fake Out', 'url': '/static/hopeful3.mp3'}
        ],
        'relieved': [
            {'name': 'Goose house - 光るなら (若能绽放光芒)', 'url': '/static/relieved.mp3'},
            {'name': 'Mayn - 人生進行形', 'url': '/static/relieved2.mp3'},
            {'name': 'RADWIMPS - なんでもないや (没什么大不了) (Movie ver_)', 'url': '/static/relieved3.mp3'}
        ],
        'content': [
            {'name': 'SawanoHiroyuki[nZk] _ Laco - Hands Up to the Sky', 'url': '/static/content.mp3'},
            {'name': 'YOASOBI (ヨアソビ) - 群青', 'url': '/static/content2.mp3'},
            {'name': '周杰伦 - 稻香', 'url': '/static/content3.mp3'}
        ],
        'calm': [
            {'name': 'Aimer (エメ) - Ref_rain', 'url': '/static/calm.mp3'},
            {'name': '塞壬唱片-MSR_横山克 (よこやま まさる) - 春弦', 'url': '/static/calm2.mp3'},
            {'name': '庄东茹 - 给我无尽不眠的春天', 'url': '/static/calm3.mp3'}
        ],
        
        # 中性/复杂情绪
        'surprised': [
            {'name': 'Uptown Funk - Mark Ronson ft. Bruno Mars', 'url': '/static/surprised.mp3'},
            {'name': 'Alexandra Stan _ Manilla Maniacs - All My People', 'url': '/static/surprised2.mp3'},
            {'name': '就是南方凯 - 离别开出花 (弹唱版)', 'url': '/static/surprised3.mp3'}
        ],
        'nostalgic': [
            {'name': 'Justin Timberlake、Carey Mulligan、Stark Sands - Five Hundred Miles', 'url': '/static/nostalgic.mp3'},
            {'name': '王诗安 - Home', 'url': '/static/nostalgic2.mp3'},
            {'name': '周杰伦 _ 费玉清 - 千里之外', 'url': '/static/nostalgic3.mp3'}
        ],
        'confused': [
            {'name': 'YOASOBI - もしも命が描けたら (若能描绘生命)', 'url': '/static/confused.mp3'},
            {'name': '郭顶 - 凄美地', 'url': '/static/confused2.mp3'},
            {'name': '平凡之路 - 朴树', 'url': '/static/confused3.mp3'}
        ],
        'bored': [
            {'name': 'Akie秋绘 _ 夏璃夜 - アスノヨゾラ哨戒班 (明日的夜空哨戒班)', 'url': '/static/bored.mp3'},
            {'name': 'Approaching Nirvana - You', 'url': '/static/bored2.mp3'},
            {'name': '徐梦圆 _ 双笙 - 藏', 'url': '/static/bored3.mp3'}
        ],
        
        # 消极情绪
        'sad': [
            {'name': 'Avicii - The Days', 'url': '/static/sad.mp3'},
            {'name': 'LiSA (織部里沙) - unlasting', 'url': '/static/sad2.mp3'},
            {'name': '知更鸟_HOYO-MiX_Chevy - 使一颗心免于哀伤', 'url': '/static/sad3.mp3'}
        ],
        'angry': [
            {'name': 'King Gnu - 飛行艇', 'url': '/static/angry.mp3'},
            {'name': 'Little Mix - Shout Out to My Ex', 'url': '/static/angry2.mp3'},
            {'name': 'TK from 凛冽时雨 (TK from 凛として時雨) - unravel', 'url': '/static/angry3.mp3'}
        ],
        'fearful': [
            {'name': 'Akie秋绘 - 春よ、来い。春天，来吧。', 'url': '/static/fearful.mp3'},
            {'name': 'Fall Out Boy-Immortals-(电影《超能陆战队》主题曲)', 'url': '/static/fearful2.mp3'},
            {'name': '米津玄師 (よねづ けんし) - Lemon', 'url': '/static/fearful3.mp3'}
        ],
        'disgusted': [
            {'name': 'Aimer (エメ) - カタオモイ (单相思)', 'url': '/static/disgusted.mp3'},
            {'name': '周杰伦 - 花海', 'url': '/static/disgusted2.mp3'},
            {'name': '周深 - 光亮', 'url': '/static/disgusted3.mp3'}
        ],
        'anxious': [
            {'name': 'Hugh Jackman _ Zac Efron - The Other Side', 'url': '/static/anxious.mp3'},
            {'name': 'RADWIMPS (ラッドウィンプス) - カナタハルカ (遥远的彼方)', 'url': '/static/anxious2.mp3'},
            {'name': '易言 _ 肥皂菌丨珉珉的猫咪丨 _ 赵方婧 _ 音阙诗听 - 彩虹节拍', 'url': '/static/anxious3.mp3'}
        ],
        'lonely': [
            {'name': 'Asher Monroe - Here With You', 'url': '/static/lonely.mp3'},
            {'name': 'DAISHI DANCE _ Cécile Corbel - Take Me Hand', 'url': '/static/lonely2.mp3'},
            {'name': '周杰伦 - 花海', 'url': '/static/lonely3.mp3'}
        ],
        
        # 默认
        'neutral': [
            {'name': 'AIYUE _ 理名 _ 塞壬唱片-MSR - Heavenly Me', 'url': '/static/neutral.mp3'},
            {'name': 'HOYO-MiX _ NIDA - 拂晓 Proi Proi', 'url': '/static/neutral2.mp3'},
            {'name': '明透 - 0g', 'url': '/static/neutral3.mp3'}
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