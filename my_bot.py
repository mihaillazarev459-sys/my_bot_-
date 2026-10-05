import os
import requests
from bs4 import BeautifulSoup

# ================== НАСТРОЙКИ ==================
TG_TOKEN = "8706725141:AAFrtMaAKCQC5j94gNQBR-V144pB-zhPFQ"  # Ваш Telegram-бот
TG_CHAT_ID = "@mihailgoski"                             # Ваш канал/чат

# Виджет сообщества — отдаёт чистый HTML без проверок и авторизации
VK_WIDGET_URL = "https://vk.com/widget_community.php?gid=avto35"

# Список кодовых слов и фраз для фильтрации (в нижнем регистре)
KEYWORDS = [
    "ваз 2107",
    "ваз 2105",
    "цена подарок",
    "каракат"
]
# ===============================================

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

    print("Загружаю стену ВК через публичный виджет...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(VK_WIDGET_URL, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Ошибка загрузки виджета ВК: {response.status_code}")
            return
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Виджет хранит тексты постов в классах .wpost_text и .wpost_content
    posts = soup.select(".wpost_text, .wpost_content")

    if not posts:
        # Запасной вариант поиска по элементам виджета
        posts = soup.find_all("div", class_=lambda c: c and "wpost" in c)

    if not posts:
        print("Посты в виджете не найдены.")
        return

    print(f"Успешно найдено постов в виджете: {len(posts)}")

    new_seen = set(seen_posts)

    # Перебираем посты от старых к новым
    for post in reversed(posts[:10]):
        text = post.get_text(separator="\n", strip=True)
        if not text or len(text) < 5:
            continue

        text_lower = text.lower()

        # Фильтр по кодовым словам: пропускаем пост, если нет совпадений
        if KEYWORDS and not any(kw.lower() in text_lower for kw in KEYWORDS):
            continue

        # Уникальный идентификатор текста поста
        post_id = str(hash(text))

        if post_id in seen_posts:
            continue

        print(f"Найден совпавший пост: {text[:30]}...")

        # На первом запуске только запоминаем тексты, отправку делаем со второго
        if not first_run:
            msg = f"🚘 **Новый пост в avto35**:\n\n{text}"
            send_tg_message(msg)

        new_seen.add(post_id)

    # Сохраняем обработанные посты
    with open("seen.txt", "w", encoding="utf-8") as f:
        for pid in new_seen:
            f.write(f"{pid}\n")

if __name__ == "__main__":
    main()
    main()
