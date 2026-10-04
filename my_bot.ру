import os
import requests
from bs4 import BeautifulSoup

# ================= НАСТРОЙКИ =================
TG_TOKEN = "8706725141:AAFrtMaAkCQC5j94gNQBR-Vi144pB-zhPfQ"
TG_CHAT_ID = "@mihailgoski"
VK_WALL_URL = "https://m.vk.com/avto35"  # Ссылка на группу ВК

KEYWORDS = [
    "2107", "2105", "ваз 2107", "ваз 2105", 
    "семёрка", "пятёрка", 
    "цена подарок", "на каракат", "снегоход"
]
# =============================================

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "disable_web_page_preview": False}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def main():
    seen_posts = set()
    if os.path.exists("seen.txt"):
        with open("seen.txt", "r", encoding="utf-8") as f:
            seen_posts = set(line.strip() for line in f)

    print("Проверяю стену ВК...")
    try:
        response = requests.get(VK_WALL_URL, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Ошибка загрузки ВК: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        posts = soup.find_all("div", class_="pi_text")

        new_seen = list(seen_posts)

        for post in posts:
            text = post.get_text().strip()
            text_lower = text.lower()
            post_id = str(hash(text))

            if post_id in seen_posts:
                continue

            if any(keyword in text_lower for keyword in KEYWORDS):
                msg = f"🔍 Найдено объявление!\n\n{text[:300]}...\n\nИсточник: {VK_WALL_URL}"
                send_tg_message(msg)
                print("[+] Отправлено новое объявление!")

            new_seen.append(post_id)

        # Сохраняем последние 100 постов
        with open("seen.txt", "w", encoding="utf-8") as f:
            for item in new_seen[-100:]:
                f.write(f"{item}\n")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
