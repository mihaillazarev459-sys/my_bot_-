import os
import re
import requests
from bs4 import BeautifulSoup
import hashlib

# ================== НАСТРОЙКИ ==================
TG_TOKEN = "8706725141:AAFrtMaAkCQC5j94gNQBR-Vi144pB-zhPfQ"
TG_CHAT_ID = "1752884535"
VK_DOMAIN = "avto35"

# Оставьте True для первой проверки (пришлет тестовый пост), 
# затем поменяйте на False для работы по ключевым словам.
TEST_MODE = True

KEYWORDS = [
    # ВАЗ классика
    "ваз 2107", "ваз-2107", "ваз2107", "лада 2107", "2107", "семёрка", "семерка",
    "ваз 2105", "ваз-2105", "ваз2105", "лада 2105", "2105", "пятёрка", "пятерка",
    # УАЗ и его модификации
    "уаз", "уазик", "уаз-469", "уаз 469", "уаз-39094", "фермер", "буханка", 
    "головастик", "469", "хантер",
    # Цена / Выгода
    "цена подарок", "цена-подарок", "отдам даром",
    # Каракат
    "каракат", "каракаты", "вездеход каракат"
]
# ===============================================

def get_numeric_group_id(domain):
    url = f"https://vk.com/{domain}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        match = re.search(r'["\']group_id["\']?\s*:\s*(\d+)', res.text)
        if not match:
            match = re.search(r'wall-(\d+)_', res.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Ошибка при определении ID группы: {e}")
    return None

def send_tg_message(text):
    if len(text) > 4000:
        text = text[:3990] + "\n\n...[текст обрезан]"

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.ok:
            print("УСПЕХ: Сообщение успешно доставлено в Telegram!")
        else:
            print(f"Ошибка ответа TG API: {res.text}")
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def get_stable_id(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def main():
    gid = get_numeric_group_id(VK_DOMAIN)
    if not gid:
        print(f"Не удалось определить числовой ID группы {VK_DOMAIN}.")
        return

    widget_url = f"https://vk.com/widget_community.php?gid={gid}&mode=4&width=500"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9"
    }

    try:
        response = requests.get(widget_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Ошибка загрузки виджета ВК: {response.status_code}")
            return
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Жесткая фильтрация: ищем только посты стены и отсекаем виджеты бизнеса и рекламу
    all_posts = soup.select(".wall_item, .post, [id^='post-']")
    posts = []
    
    for p in all_posts:
        classes = " ".join(p.get("class", []))
        # Пропускаем служебные блоки, рекламу и ВК Бизнес
        if any(bad in classes.lower() for bad in ["ads", "business", "widget_app", "market", "audio"]):
            continue
            
        text_elem = p.select_one(".wall_post_text, .wpost_text, div.post_text")
        if text_elem:
            posts.append(text_elem)

    if not posts:
        print("Посты не найдены.")
        return

    # --- ТЕСТОВЫЙ РЕЖИМ ---
    if TEST_MODE:
        print("⚠️ ТЕСТОВЫЙ РЕЖИМ ВКЛЮЧЕН: Отправляю первый попавшийся текст поста...")
        sample_text = posts[0].get_text(separator="\n", strip=True)
        msg = f"🧪 **ТЕСТОВОЕ СООБЩЕНИЕ ИЗ avto35**:\n\n{sample_text}"
        send_tg_message(msg)
        return

    # --- ОСНОВНОЙ РАБОЧИЙ РЕЖИМ ---
    seen_posts = set()
    if os.path.exists("seen.txt"):
        with open("seen.txt", "r", encoding="utf-8") as f:
            seen_posts = set(line.strip() for line in f)

    new_seen = set(seen_posts)
    new_posts_found = 0

    for post in reversed(posts[:10]):
        text = post.get_text(separator="\n", strip=True)
        if not text or len(text) < 5:
            continue

        text_lower = text.lower()

        if KEYWORDS and not any(kw.lower() in text_lower for kw in KEYWORDS):
            continue

        post_id = get_stable_id(text)

        if post_id in seen_posts:
            continue

        print(f"Найден подходящий пост: {text[:30]}...")
        
        msg = f"🚘 **Новый пост в avto35**:\n\n{text}"
        send_tg_message(msg)
        
        new_seen.add(post_id)
        new_posts_found += 1

    with open("seen.txt", "w", encoding="utf-8") as f:
        for pid in new_seen:
            f.write(f"{pid}\n")
            
    print(f"Скрипт отработал. Новых отправленных постов: {new_posts_found}")

if __name__ == "__main__":
    main()
