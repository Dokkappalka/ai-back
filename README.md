# AI Hype Backend

Django REST API backend для агрегатора нейронных сетей.

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте PostgreSQL базу данных:

   **3.1. Установите PostgreSQL (если еще не установлен):**
   - macOS: `brew install postgresql@14` или скачайте с [postgresql.org](https://www.postgresql.org/download/)
   - Linux: `sudo apt-get install postgresql postgresql-contrib` (Ubuntu/Debian)
   - Windows: скачайте установщик с официального сайта

   **3.2. Запустите PostgreSQL сервис:**
   ```bash
   # macOS (Homebrew)
   brew services start postgresql@14
   
   # Linux
   sudo systemctl start postgresql
   
   # Windows: PostgreSQL обычно запускается автоматически как служба
   ```

   **3.3. Создайте базу данных и пользователя:**
   ```bash
   # Подключитесь к PostgreSQL
   psql postgres
   
   # В консоли PostgreSQL выполните:
   CREATE DATABASE ai_hype_db;
   CREATE USER your_username WITH PASSWORD 'your_password';
   ALTER ROLE your_username SET client_encoding TO 'utf8';
   ALTER ROLE your_username SET default_transaction_isolation TO 'read committed';
   ALTER ROLE your_username SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE ai_hype_db TO your_username;
   \q
   ```

   **3.4. Создайте файл `.env`:**
   ```bash
   # Скопируйте пример файла
   cp .env.example .env
   ```

   **3.5. Отредактируйте `.env` файл и заполните настройки:**
   ```env
   DB_NAME=ai_hype_db
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   
   SECRET_KEY=сгенерируйте-случайный-секретный-ключ
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Suno API Configuration (для генерации музыки)
   SUNO_API_KEY=your_suno_api_key_here
   ```
   
   **Примечание:** Для получения Suno API ключа посетите [Suno API Dashboard](https://docs.sunoapi.org/)
   
   **Примечание:** Для генерации SECRET_KEY можно использовать:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. Выполните миграции:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Создайте суперпользователя (опционально):
```bash
python manage.py createsuperuser
```

6. Запустите сервер разработки:
```bash
python manage.py runserver
```

## API Endpoints

### Генерация изображений
- `GET /api/image/` - Список всех запросов на генерацию изображений
- `POST /api/image/` - Создать новый запрос на генерацию изображения
- `GET /api/image/{id}/` - Получить конкретный запрос

### Генерация видео
- `GET /api/video/` - Список всех запросов на генерацию видео
- `POST /api/video/` - Создать новый запрос на генерацию видео
- `GET /api/video/{id}/` - Получить конкретный запрос

### Генерация музыки (Suno API)
- `GET /api/music/` - Список запросов на генерацию музыки (только свои, если аутентифицирован)
- `POST /api/music/` - Создать новый запрос на генерацию музыки
- `GET /api/music/{id}/` - Получить конкретный запрос
- `GET /api/music/{id}/status/` - Проверить статус генерации

**Параметры для POST /api/music/:**

Обязательные параметры зависят от режима:

**Custom Mode (`custom_mode: true`):**
- Если `instrumental: true`: требуется `style` и `title`
- Если `instrumental: false`: требуется `style`, `prompt` и `title`

**Non-Custom Mode (`custom_mode: false`):**
- Требуется только `prompt`

**Дополнительные параметры:**
- `custom_mode` (boolean, required) - Включить Custom Mode
- `instrumental` (boolean, required) - Инструментальная композиция (без вокала)
- `model` (string, required) - Модель: `V4`, `V4_5`, `V4_5PLUS`, `V4_5ALL`, `V5`
- `prompt` (string, optional) - Описание желаемой музыки
- `style` (string, optional) - Стиль/жанр музыки
- `title` (string, optional) - Название трека
- `persona_id` (string, optional) - ID персоны для стилизации
- `negative_tags` (string, optional) - Стили для исключения
- `vocal_gender` (string, optional) - Пол вокала: `m` или `f`
- `style_weight` (decimal, optional) - Вес стиля (0.00-1.00)
- `weirdness_constraint` (decimal, optional) - Ограничение креативности (0.00-1.00)
- `audio_weight` (decimal, optional) - Вес входного аудио (0.00-1.00)

**Пример запроса:**
```json
{
  "custom_mode": true,
  "instrumental": false,
  "model": "V4_5ALL",
  "prompt": "A calm and relaxing piano track with soft melodies",
  "style": "Classical",
  "title": "Peaceful Piano Meditation"
}
```

**Примечание:** Каждый запрос генерирует 2 песни. Результаты доступны через поля `song_1_url`, `song_1_stream_url`, `song_2_url`, `song_2_stream_url`.

### Чат
- `GET /api/chat/` - Список всех сообщений
- `POST /api/chat/` - Создать новое сообщение
- `GET /api/chat/{id}/` - Получить конкретное сообщение

## Структура проекта

```
backend/
├── manage.py
├── requirements.txt
├── backend/
│   ├── settings.py      # Настройки Django
│   ├── urls.py          # Главный URL роутер
│   └── wsgi.py
├── api/
│   ├── models.py        # Модели данных
│   ├── serializers.py   # Сериализаторы
│   ├── views.py         # ViewSets
│   ├── urls.py          # API URL роутинг
│   └── admin.py         # Админка
└── authentication/      # Заглушка для будущей аутентификации
```

## TODO

- [x] Интеграция с Suno API для генерации музыки
- [x] Добавление полей пользователя в модели
- [ ] Реализация callback endpoint для Suno API
- [ ] Интеграция с моделями генерации изображений
- [ ] Интеграция с моделями генерации видео
- [ ] Интеграция с чат-моделями
- [ ] Реализация аутентификации пользователей
- [ ] Добавление системы конверсаций для чата

