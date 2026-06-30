import aiohttp
import asyncio
import ssl
import socket
import whois
import requests
import hashlib
from datetime import datetime
from urllib.parse import urlparse
from config import ABUSEIPDB_API_KEY, HUGGINGFACE_API_KEY, OPENROUTER_API_KEY

# === ПРОВЕРКА ССЫЛОК ===
async def check_url(url, deep=False):
    result = {
        "safe": True,
        "score": 100,
        "warnings": [],
        "info": {}
    }
    
    # 1. Проверка в чёрном списке
    # (будет через database.py, пока заглушка)
    
    # 2. Проверка домена через WHOIS
    try:
        domain = urlparse(url).netloc
        w = whois.whois(domain)
        if w.creation_date:
            age = (datetime.now() - w.creation_date[0]).days
            result["info"]["domain_age"] = age
            if age < 30:
                result["score"] -= 20
                result["warnings"].append(f"⚠️ Домену всего {age} дней (подозрительно)")
    except:
        result["warnings"].append("⚠️ Не удалось проверить возраст домена")
    
    # 3. Проверка SSL
    try:
        hostname = urlparse(url).netloc
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.connect((hostname, 443))
            cert = s.getpeercert()
            result["info"]["ssl_valid"] = True
    except:
        result["score"] -= 30
        result["warnings"].append("🔴 SSL сертификат недействителен или отсутствует")
        result["safe"] = False
    
    # 4. Проверка редиректов
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        if len(response.history) > 3:
            result["score"] -= 15
            result["warnings"].append(f"⚠️ Много редиректов ({len(response.history)})")
        result["info"]["status_code"] = response.status_code
    except:
        result["warnings"].append("⚠️ Сайт недоступен")
    
    # 5. Проверка через AbuseIPDB (если есть IP)
    try:
        ip = socket.gethostbyname(urlparse(url).netloc)
        async with aiohttp.ClientSession() as session:
            headers = {"Key": ABUSEIPDB_API_KEY, "Accept": "application/json"}
            params = {"ipAddress": ip, "maxAgeInDays": 90}
            async with session.get("https://api.abuseipdb.com/api/v2/check", headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    abuse_score = data["data"]["abuseConfidenceScore"]
                    result["info"]["abuse_score"] = abuse_score
                    if abuse_score > 50:
                        result["score"] -= 30
                        result["warnings"].append(f"🔴 IP в базах злоумышленников ({abuse_score}%)")
                        result["safe"] = False
    except:
        pass
    
    # 6. Глубокая проверка (дополнительно)
    if deep:
        # Здесь можно добавить больше проверок
        result["info"]["deep_scan"] = True
    
    # Итоговая оценка
    if result["score"] < 40:
        result["safe"] = False
        result["level"] = "🔴 Критическая угроза"
    elif result["score"] < 70:
        result["level"] = "🟠 Высокий риск"
    elif result["score"] < 85:
        result["level"] = "🟡 Подозрительно"
    else:
        result["level"] = "🟢 Безопасно"
    
    return result

# === ПРОВЕРКА ФАЙЛОВ ===
def check_file_hash(file_bytes):
    md5 = hashlib.md5(file_bytes).hexdigest()
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    return md5, sha256

# === AI РАБОТА С ФОТО ===
async def ai_photo_edit(image_bytes, mode):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    
    # Выбор модели
    models = {
        "bg": "briaai/RMBG-1.4",  # Удаление фона
        "cyber": "stabilityai/stable-diffusion-3.5-large",  # Стиль
        "enhance": "google/gemma-3-27b-it",  # Улучшение (заглушка)
        "restore": "microsoft/ResNet50"  # Восстановление (заглушка)
    }
    
    model = models.get(mode, models["bg"])
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, headers=headers, data=image_bytes) as resp:
            if resp.status == 200:
                return await resp.read()
            else:
                return None

# === AI АССИСТЕНТ ===
async def ai_assistant(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result["choices"][0]["message"]["content"]
            else:
                return "❌ Ошибка AI. Попробуй позже."
