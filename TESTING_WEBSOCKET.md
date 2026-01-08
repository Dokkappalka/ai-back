# Инструкция по тестированию WebSocket

## Предварительные требования

1. **Redis сервер должен быть запущен:**
   ```bash
   # macOS (через Homebrew)
   brew services start redis
   
   # Или просто запустить redis-server
   redis-server
   
   # Проверить что Redis работает
   redis-cli ping
   # Должен ответить: PONG
   ```

2. **Установить ASGI сервер:**
   ```bash
   pip install daphne
   # или
   pip install uvicorn[standard]
   ```

## Запуск сервера

### Вариант 1: Daphne (рекомендуется для Django Channels)
```bash
daphne -b 0.0.0.0 -p 8000 backend.asgi:application
```

### Вариант 2: Uvicorn
```bash
uvicorn backend.asgi:application --host 0.0.0.0 --port 8000
```

### Вариант 3: Django runserver (только для разработки)
```bash
python manage.py runserver
```
⚠️ **Примечание:** Django runserver не поддерживает WebSocket полноценно. Используйте daphne или uvicorn.

## Тестирование WebSocket соединения

### 1. Получить JWT токен

Сначала нужно залогиниться и получить access token:

```bash
# POST запрос на /api/auth/login/
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Ответ будет содержать access_token
```

### 2. Тестировать WebSocket соединение

#### Вариант A: Использовать wscat (npm пакет)
```bash
# Установить wscat
npm install -g wscat

# Подключиться к WebSocket
wscat -c "ws://localhost:8000/ws/music/updates/?token=YOUR_ACCESS_TOKEN"
```

#### Вариант B: Использовать Python скрипт

Создайте файл `test_websocket.py`:

```python
import asyncio
import websockets
import json
import sys

async def test_websocket():
    token = sys.argv[1] if len(sys.argv) > 1 else input("Enter access token: ")
    uri = f"ws://localhost:8000/ws/music/updates/?token={token}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            print("Waiting for updates...")
            
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"\n📨 Received update:")
                print(json.dumps(data, indent=2))
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ Connection closed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
```

Запуск:
```bash
pip install websockets
python test_websocket.py YOUR_ACCESS_TOKEN
```

#### Вариант C: Использовать браузерную консоль

Откройте консоль браузера (F12) на вашем фронтенде:

```javascript
const token = 'YOUR_ACCESS_TOKEN';
const ws = new WebSocket(`ws://localhost:8000/ws/music/updates/?token=${token}`);

ws.onopen = () => {
    console.log('✅ WebSocket connected');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📨 Received update:', data);
};

ws.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
};

ws.onclose = (event) => {
    console.log('🔌 WebSocket closed:', event.code, event.reason);
};
```

## Тестирование полного потока

1. **Создать запрос на генерацию музыки:**
   ```bash
   curl -X POST http://localhost:8000/api/music/ \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "A happy upbeat song",
       "model": "V4_5ALL"
     }'
   ```
   
   Запомните `id` из ответа и `task_id`.

2. **Подключиться к WebSocket** (используя один из методов выше)

3. **Симулировать callback от Suno API** (вручную или дождаться реального):
   ```bash
   curl -X POST http://localhost:8000/api/music/callback/ \
     -H "Content-Type: application/json" \
     -d '{
       "code": 200,
       "msg": "success",
       "data": {
         "callbackType": "complete",
         "task_id": "YOUR_TASK_ID",
         "data": [{
           "id": "song_1_id",
           "audio_url": "https://example.com/song1.mp3",
           "stream_audio_url": "https://example.com/song1_stream.mp3",
           "image_url": "https://example.com/song1.jpg",
           "duration": 120.5,
           "tags": "happy, upbeat",
           "model_name": "V4_5ALL"
         }]
       }
     }'
   ```

4. **Проверить, что WebSocket получил обновление** с полными данными трека.

## Проверка логов

Смотрите логи Django для отладки:
- Успешное подключение WebSocket
- Ошибки аутентификации
- Отправка сообщений в группы
- Обработка callback'ов

## Возможные проблемы

1. **"Channel layer not available"** - Redis не запущен
2. **"Invalid token"** - Токен протухший или невалидный
3. **Connection refused** - Сервер не запущен или неправильный порт
4. **CORS ошибки** - Проверьте настройки CORS в settings.py

