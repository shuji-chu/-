import requests
import json
import time
import os
import io
import re

# ========== 读取配置 ==========
with open("config.json", "r") as f:
    config = json.load(f)

SAFEW_TOKEN = config["safew_token"]
MUSIC_API = config["music_api_url"]
ADMIN_ID = config["admin_id"]
BOT_LINK = config["bot_link"]
ZHAOSHANG_LINK = config["zhaoshang_link"]
CONTACT = config["contact"]

SAFEW_BASE = f"https://api.safew.bot/bot{SAFEW_TOKEN}"

AD_CONFIG_FILE = "ad_config.json"

# ========== 广告配置读写 ==========
def load_ad_config():
    if os.path.exists(AD_CONFIG_FILE):
        with open(AD_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"zhaoshang_text": "", "ads": []}

def save_ad_config(data):
    with open(AD_CONFIG_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False)

# ========== SafeW API 调用 ==========
def send_message(chat_id, text, parse_mode="HTML", reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{SAFEW_BASE}/sendMessage", json=payload)

def send_audio(chat_id, audio_bytes, filename, caption):
    files = {"audio": (filename, audio_bytes, "audio/mpeg")}
    data = {"chat_id": chat_id, "caption": caption}
    requests.post(f"{SAFEW_BASE}/sendAudio", data=data, files=files)

# ========== 用户命令处理 ==========
def handle_start(chat_id):
    text = """
👋 欢迎使用音乐搜索机器人

🎵 发送歌名即可搜索

🔎 全网最多歌曲

📊 点击蓝色链接领取文件

👇 /hlpl 使用帮助

💼 /kefu 商务合作
"""
    send_message(chat_id, text)

def handle_hlpl(chat_id):
    text = """
📖 使用帮助

1️⃣ 发送歌名

2️⃣ 选择喜欢的版本

3️⃣ 点击链接领取文件

🔎 把机器人拉到群里

4️⃣ 群成员直接发歌名就能搜歌

❓ 问题反馈 /kefu
"""
    send_message(chat_id, text)

def handle_kefu(chat_id):
    text = f"""
💼 商务合作

📢 招商广告位火热招商

💱 全网最高TRX汇率兑换

📩 联系：{CONTACT}
"""
    send_message(chat_id, text)

# ========== 搜索歌曲 ==========
def handle_search(chat_id, song_name):
    try:
        # 1. 调用 go-music-api 搜索
        search_resp = requests.get(f"{MUSIC_API}/api/v1/music/search", params={"q": song_name}, timeout=10)
        search_data = search_resp.json()
        
        if not search_data.get("data"):
            send_message(chat_id, "❌ 没找到这首歌，换个关键词试试。")
            return
        
        # 2. 取前8条
        songs = search_data["data"][:8]
        
        # 3. 读取广告配置
        ad_config = load_ad_config()
        zhaoshang_text = ad_config.get("zhaoshang_text", "")
        ads = ad_config.get("ads", [])
        
        # 4. 拼装文案
        text = ""
        
        # 顶部招商广告
        if zhaoshang_text:
            text += f"{zhaoshang_text}\n\n━━━━━━━━━━━━\n\n"
        
        # 搜索结果
        text += f"🔎 <b>搜索到全网最多歌曲</b>\n\n━━━━━━━━━━━━\n\n"
        
        # 逐条展示
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
        for i, song in enumerate(songs, start=1):
            title = song["title"]
            artist = song["artist"]
            song_id = song["id"]
            emoji = emojis[i-1] if i <= 8 else "🔹"
            text += f"{emoji} <a href=\"{BOT_LINK}?start=song_{song_id}\">{title} - {artist}</a>\n\n"
        
        text += "━━━━━━━━━━━━\n\n"
        
        # 5. 拼装底部内联按钮
        keyboard = []
        if ads:
            for ad in ads:
                keyboard.append([{"text": ad["name"], "url": ad["link"]}])
        reply_markup = {"inline_keyboard": keyboard} if keyboard else None
        
        # 6. 发送消息
        send_message(chat_id, text, reply_markup=reply_markup)
    except Exception as e:
        print("搜索出错:", e)
        send_message(chat_id, "❌ 搜索失败，请稍后再试。")

# ========== 音频领取处理 ==========
def handle_download(chat_id, song_id):
    try:
        # 调用 go-music-api 获取音频流
        stream_resp = requests.get(f"{MUSIC_API}/api/v1/music/stream?id={song_id}&source=netease", stream=True)
        audio_bytes = io.BytesIO(stream_resp.content)
        
        # 发送音频
        send_audio(chat_id, audio_bytes, f"{song_id}.mp3", "🎵 歌曲已送达")
    except Exception as e:
        print("下载出错:", e)
        send_message(chat_id, "❌ 下载失败，请稍后再试。")

# ========== 长轮询 ==========
def long_polling():
    offset = 0
    while True:
        try:
            resp = requests.get(f"{SAFEW_BASE}/getUpdates", params={"offset": offset, "timeout": 50}, timeout=60)
            data = resp.json()
            if not data.get("ok"):
                print("API错误:", data.get("description"))
                time.sleep(5)
                continue
            
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message", {})
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "")
                
                # 处理命令
                if text.startswith("/"):
                    if text == "/start":
                        handle_start(chat_id)
                    elif text == "/hlpl":
                        handle_hlpl(chat_id)
                    elif text == "/kefu":
                        handle_kefu(chat_id)
                    elif text.startswith("/set_ad"):
                        if str(chat_id) == str(ADMIN_ID):
                            save_ad_config({"zhaoshang_text": text[7:].strip(), "ads": load_ad_config().get("ads", [])})
                            send_message(chat_id, "✅ 顶部招商广告已更新！")
                        else:
                            send_message(chat_id, "⛔ 您没有权限操作")
                    elif text.startswith("/ad_add"):
                        if str(chat_id) == str(ADMIN_ID):
                            parts = text[7:].strip().split("|")
                            if len(parts) < 2:
                                send_message(chat_id, "❌ 格式错误，正确格式：/ad_add 名称|链接")
                                return
                            name, link = parts[0].strip(), parts[1].strip()
                            ad_config = load_ad_config()
                            ad_config["ads"].append({"name": name, "link": link})
                            save_ad_config(ad_config)
                            send_message(chat_id, f"✅ 已添加广告商：{name}")
                        else:
                            send_message(chat_id, "⛔ 您没有权限操作")
                    elif text.startswith("/ad_del"):
                        if str(chat_id) == str(ADMIN_ID):
                            try:
                                index = int(text[7:].strip()) - 1
                                ad_config = load_ad_config()
                                if index < 0 or index >= len(ad_config.get("ads", [])):
                                    send_message(chat_id, "❌ 编号不存在")
                                    return
                                removed = ad_config["ads"].pop(index)
                                save_ad_config(ad_config)
                                send_message(chat_id, f"✅ 已删除广告商：{removed['name']}")
                            except Exception:
                                send_message(chat_id, "❌ 格式错误，正确格式：/ad_del 编号")
                        else:
                            send_message(chat_id, "⛔ 您没有权限操作")
                    elif text.startswith("/ad_list"):
                        if str(chat_id) == str(ADMIN_ID):
                            ad_config = load_ad_config()
                            if "ads" not in ad_config or len(ad_config["ads"]) == 0:
                                send_message(chat_id, "当前没有广告商按钮")
                            else:
                                msg = "📋 当前广告商列表：\n"
                                for i, ad in enumerate(ad_config["ads"], start=1):
                                    msg += f"{i}. {ad['name']} - {ad['link']}\n"
                                send_message(chat_id, msg)
                        else:
                            send_message(chat_id, "⛔ 您没有权限操作")
                    elif text.startswith("/ad_clear"):
                        if str(chat_id) == str(ADMIN_ID):
                            ad_config = load_ad_config()
                            ad_config["ads"] = []
                            save_ad_config(ad_config)
                            send_message(chat_id, "✅ 已清空所有广告商")
                        else:
                            send_message(chat_id, "⛔ 您没有权限操作")
                    continue
                
                # 处理用户搜索
                if text:
                    handle_search(chat_id, text)
        except Exception as e:
            print("长轮询出错:", e)
            time.sleep(5)

if __name__ == "__main__":
    print("机器人启动中...")
    long_polling()
