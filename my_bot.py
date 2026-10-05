import os
import re
import requests
from bs4 import BeautifulSoup

# ================== НАСТРОЙКИ ==================
TG_TOKEN = "8706725141:AAFrtMaAKCQC5j94gNQBR-V144pB-zhPFQ"  # Ваш Telegram-бот
TG_CHAT_ID = "@mihailgoski"                             # Ваш канал/чат
VK_DOMAIN = "avto35"

# Список кодовых слов и фраз для фильтрации (в нижнем регистре)
KEYWORDS = [
    "ваз 2107",
    "ваз 2105",
    "цена подарок",
    "каракат"
]
# ===============================================

def get_numeric_group_id(domain):
    """Находит числовой ID группы VK по её буквенному имени"""
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
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if not res.ok:
            print(f"Ошибка ответа TG API: {res.text}")
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def main():
    first_run = not os.path.exists("seen.txt")
    seen_posts = set()

    if not first_run:
        with open("seen.txt", "r", encoding="utf-8") as f:
            seen_posts = set(line.strip() for line in f)

    print("Определяю числовой ID группы...")
    gid = get_numeric_group_id(VK_DOMAIN)

    if not gid:
        print(f"Не удалось определить числовой ID группы {VK_DOMAIN}.")
        return

    print(f"Числовой ID группы найден: {gid}")
    widget_url = f"https://vk.com/widget_community.php?gid={gid}&mode=4&width=500"

    print("Загружаю стену ВК через виджет...")
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
    
    # Расширенный селектор для поиска постов в виджете
    posts = soup.select("[id^='post-'], .wall_item, .wpost, .wpost_text, .wall_post_text, [class*='wpost'], [class*='post']")

    if not posts:
        posts = soup.find_all("div", class_=lambda c: c and ("post" in c or "wall" in c))

    if not posts:
        print("Посты в виджете не найдены. Заголовки страницы:")
        print(response.text[:300])
        return

    print(f"Успешно найдено постов в виджете: {len(posts)}")

    new_seen = set(seen_posts)

    # Перебираем посты от старых к новым
    for post in reversed(posts[:10]):
        text = post.get_text(separator="\n", strip=True)
        if not text or len(text) < 5:
            continue

        text_lower = text.lower()

        # Фильтр по кодовым словам
        if KEYWORDS and not any(kw.lower() in text_lower for kw in KEYWORDS):
            continue

        post_id = str(hash(text))

        if post_id in seen_posts:
            continue

        print(f"Найден совпавший пост: {text[:30]}...")

        if not first_run:
            msg = f"🚘 **Новый пост в avto35**:\n\n{text}"
            send_tg_message(msg)

        new_seen.add(post_id)

    with open("seen.txt", "w", encoding="utf-8") as f:
        for pid in new_seen:
            f.write(f"{pid}\n")

if __name__ == "__main__":
    main()
