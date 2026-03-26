# Инструкция для реализации фронтенда — Chat с AI

## Общее описание

Бэкенд реализует полноценный чат с AI-моделями через OpenRouter API. Поддерживаются:
- Множество **разговоров (conversations)** — пользователь может создавать, переименовывать, архивировать и удалять чаты
- **Выбор модели** — пользователь выбирает AI-модель из актуального списка OpenRouter
- **Системный промпт** — можно задать инструкцию для AI на уровне разговора
- **Настройки генерации** — temperature, max_tokens
- **🆕 Streaming (SSE)** — ответ AI отображается в реальном времени, токен за токеном
- **🆕 Загрузка файлов** — пользователь может прикреплять изображения, текстовые файлы, PDF к сообщениям
- **🆕 Возможности моделей** — API сообщает, какие модели поддерживают vision (изображения), а какие нет

Аутентификация через JWT (Bearer token). Все запросы требуют заголовок:
```
Authorization: Bearer <access_token>
```

Базовый URL: `/api/chat/`

---

## ⚡ Что изменилось (Changelog)

### Streaming (SSE) — Новый эндпоинт
- **Новый эндпоинт:** `POST /api/chat/conversations/{id}/send_message_stream/`
- Ответ приходит в формате **Server-Sent Events (SSE)** — текст печатается в реальном времени
- Старый эндпоинт `send_message/` сохранён для обратной совместимости (возвращает полный ответ сразу)
- **Рекомендация:** используйте `send_message_stream/` для основного UI чата

### Загрузка файлов
- Оба эндпоинта (`send_message/` и `send_message_stream/`) теперь принимают `multipart/form-data` с файлами
- Поддерживаемые типы: **изображения** (PNG, JPEG, GIF, WebP), **текстовые файлы** (TXT, CSV, HTML, MD, JSON, XML), **PDF**
- Максимальный размер файла: **20 MB**
- Изображения автоматически конвертируются в base64 и отправляются в модель через vision API
- Текстовые файлы читаются и вставляются в контекст как текст

### Возможности моделей
- `GET /api/chat/models/` теперь возвращает дополнительные поля:
  - `supports_vision` — модель принимает изображения (true/false)
  - `supports_file_input` — модель принимает файлы напрямую (true/false)
  - `modality` — строка вида `"text+image->text"`, описывающая входы/выходы модели
- **Важно:** если `supports_vision = false`, не показывайте кнопку прикрепления изображений (или показывайте предупреждение)

### Вложения в сообщениях
- Сообщения теперь содержат поле `attachments` — массив прикреплённых файлов
- Каждый attachment содержит `url`, `original_filename`, `file_type`, `mime_type`, `file_size`

---

## API Эндпоинты

### 1. Получить список доступных моделей

```
GET /api/chat/models/
```

**Ответ (список административно разрешённых моделей):**
```json
[
  {
    "id": "anthropic/claude-3-haiku",
    "name": "Claude 3 Haiku",
    "provider": "Anthropic",
    "description": "Fast and compact model for near-instant responsiveness...",
    "context_length": 200000,
    "pricing": {
      "prompt": "0.00000025",
      "completion": "0.00000125",
      "image": "0.00000095",
      "request": "0"
    },
    "supports_vision": true,
    "supports_file_input": false,
    "modality": "text+image->text"
  },
  {
    "id": "openai/gpt-4o-mini",
    "name": "GPT-4o Mini",
    "provider": "OpenAI",
    "description": "Fast and affordable small model for lightweight tasks...",
    "context_length": 128000,
    "pricing": {
      "prompt": "0",
      "completion": "0",
      "image": "0",
      "request": "0"
    },
    "supports_vision": true,
    "supports_file_input": false,
    "modality": "text+image->text"
  },
  {
    "id": "meta-llama/llama-3-8b-instruct",
    "name": "Llama 3 8B",
    "provider": "Meta-llama",
    "description": "...",
    "context_length": 8192,
    "pricing": { ... },
    "supports_vision": false,
    "supports_file_input": false,
    "modality": "text->text"
  }
]
```

**Использование `supports_vision`:**
- Если `supports_vision = true` — можно прикреплять изображения к сообщениям
- Если `supports_vision = false` — изображения не будут обработаны моделью. Рекомендуется скрыть кнопку прикрепления изображений или показать предупреждение
- Текстовые файлы (TXT, CSV, JSON, XML, MD, HTML) и PDF работают с любой моделью — их содержимое вставляется как текст в контекст

---

### 2. Управление разговорами (Conversations)

#### 2.1 Список разговоров

```
GET /api/chat/conversations/
```

Query параметры:
- `is_archived=true|false` — фильтр по архивным (необязательно)
- `page=1` — пагинация (по 20 штук)

**Ответ:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Помоги с рефакторингом",
      "model": "openai/gpt-4o-mini",
      "system_prompt": null,
      "temperature": 0.7,
      "max_tokens": 4096,
      "is_archived": false,
      "message_count": 12,
      "last_message": {
        "id": 45,
        "role": "assistant",
        "content": "Конечно, давайте разберёмся с вашим кодом...",
        "created_at": "2026-03-07T16:00:00Z"
      },
      "created_at": "2026-03-07T15:30:00Z",
      "updated_at": "2026-03-07T16:00:00Z"
    }
  ]
}
```

#### 2.2 Создать разговор

```
POST /api/chat/conversations/
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "title": "Новый чат",
  "model": "openai/gpt-4o-mini",
  "system_prompt": "Ты полезный помощник. Отвечай на русском.",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

Все поля необязательны. Значения по умолчанию:
- `title`: `"New Chat"`
- `model`: `"openai/gpt-4o-mini"`
- `system_prompt`: `null`
- `temperature`: `0.7`
- `max_tokens`: `4096`

**Ответ:** объект Conversation (см. формат выше)

#### 2.3 Получить детали разговора

```
GET /api/chat/conversations/{id}/
```

#### 2.4 Обновить разговор

```
PATCH /api/chat/conversations/{id}/
Content-Type: application/json
```

**Тело запроса** (частичное обновление):
```json
{
  "title": "Новое название",
  "model": "anthropic/claude-3.5-sonnet",
  "temperature": 0.5
}
```

#### 2.5 Удалить разговор

```
DELETE /api/chat/conversations/{id}/
```

Удаляет разговор вместе со ВСЕМИ сообщениями и вложениями.

#### 2.6 Архивировать / Разархивировать

```
POST /api/chat/conversations/{id}/archive/
POST /api/chat/conversations/{id}/unarchive/
```

---

### 3. Сообщения

#### 3.1 Получить историю сообщений

```
GET /api/chat/conversations/{id}/messages/
```

**Ответ:**
```json
[
  {
    "id": 1,
    "conversation": 1,
    "role": "user",
    "content": "Привет! Что на этом изображении?",
    "model": null,
    "tokens_used": null,
    "attachments": [
      {
        "id": 1,
        "message": 1,
        "file": "/media/chat_attachments/1/1/photo.png",
        "original_filename": "photo.png",
        "file_type": "image",
        "mime_type": "image/png",
        "file_size": 245000,
        "url": "http://localhost:8000/media/chat_attachments/1/1/photo.png",
        "created_at": "2026-03-07T15:30:00Z"
      }
    ],
    "created_at": "2026-03-07T15:30:00Z",
    "updated_at": "2026-03-07T15:30:00Z"
  },
  {
    "id": 2,
    "conversation": 1,
    "role": "assistant",
    "content": "На изображении я вижу...",
    "model": "openai/gpt-4o-mini",
    "tokens_used": 156,
    "attachments": [],
    "created_at": "2026-03-07T15:30:02Z",
    "updated_at": "2026-03-07T15:30:02Z"
  }
]
```

---

### 4. Отправка сообщений

#### 4.1 🆕 Отправить сообщение со streaming (РЕКОМЕНДУЕТСЯ)

```
POST /api/chat/conversations/{id}/send_message_stream/
```

Поддерживает два формата:

**Формат 1: JSON (только текст)**
```
Content-Type: application/json

{
  "content": "Привет! Расскажи о себе."
}
```

**Формат 2: multipart/form-data (текст + файлы)**
```
Content-Type: multipart/form-data

content: "Что на этом изображении?"
files: [file1.png, file2.txt]
```

**Ответ: `text/event-stream` (Server-Sent Events)**

Формат SSE событий:

```
event: user_message
data: {"id": 1, "conversation": 1, "role": "user", "content": "Привет!", "attachments": [...], ...}

event: chunk
data: {"content": "Привет"}

event: chunk
data: {"content": "! Я"}

event: chunk
data: {"content": " — AI"}

event: chunk
data: {"content": "-ассистент."}

event: done
data: {"assistant_message": {"id": 2, "conversation": 1, "role": "assistant", "content": "Привет! Я — AI-ассистент.", "model": "openai/gpt-4o-mini", "tokens_used": 42, "attachments": [], ...}, "model": "openai/gpt-4o-mini", "usage": {"prompt_tokens": 10, "completion_tokens": 42, "total_tokens": 52}, "finish_reason": "stop"}
```

**В случае ошибки:**
```
event: error
data: {"error": "OpenRouter API returned HTTP 429: Rate limit exceeded", "assistant_message": {...}}
```

#### Пример реализации на фронтенде (JavaScript/TypeScript):

```typescript
async function sendMessageStream(
  conversationId: number,
  content: string,
  files?: File[],
  onChunk: (text: string) => void,
  onDone: (data: any) => void,
  onError: (error: string) => void,
  onUserMessage: (message: any) => void,
) {
  const url = `/api/chat/conversations/${conversationId}/send_message_stream/`;

  // Build request body
  let body: FormData | string;
  let headers: Record<string, string> = {
    'Authorization': `Bearer ${accessToken}`,
  };

  if (files && files.length > 0) {
    // Use FormData for file uploads
    const formData = new FormData();
    formData.append('content', content);
    files.forEach(file => formData.append('files', file));
    body = formData;
    // Don't set Content-Type — browser will set it with boundary
  } else {
    // Use JSON for text-only messages
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify({ content });
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body,
  });

  if (!response.ok) {
    onError(`HTTP ${response.status}`);
    return;
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events from buffer
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer

    let currentEvent = '';
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        switch (currentEvent) {
          case 'user_message':
            onUserMessage(data);
            break;
          case 'chunk':
            onChunk(data.content);
            break;
          case 'done':
            onDone(data);
            break;
          case 'error':
            onError(data.error);
            break;
        }
        currentEvent = '';
      }
    }
  }
}

// Использование:
let assistantText = '';

sendMessageStream(
  conversationId,
  'Привет! Расскажи о себе.',
  selectedFiles, // File[] или undefined
  // onChunk — вызывается для каждого фрагмента текста
  (text) => {
    assistantText += text;
    updateAssistantMessageUI(assistantText); // Обновить UI
  },
  // onDone — вызывается когда генерация завершена
  (data) => {
    // data.assistant_message — полное сохранённое сообщение
    // data.usage — статистика токенов
    finalizeAssistantMessage(data.assistant_message);
  },
  // onError
  (error) => {
    showErrorToast(error);
  },
  // onUserMessage — вызывается сразу с сохранённым сообщением пользователя
  (message) => {
    addUserMessageToUI(message);
  },
);
```

#### Пример с использованием EventSource API (альтернативный подход):

> **Примечание:** Стандартный `EventSource` не поддерживает POST-запросы и кастомные заголовки.
> Рекомендуется использовать `fetch` + `ReadableStream` (пример выше) или библиотеку
> [`@microsoft/fetch-event-source`](https://www.npmjs.com/package/@microsoft/fetch-event-source).

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source';

await fetchEventSource(`/api/chat/conversations/${id}/send_message_stream/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ content: 'Привет!' }),
  onmessage(ev) {
    const data = JSON.parse(ev.data);
    switch (ev.event) {
      case 'user_message':
        addUserMessageToUI(data);
        break;
      case 'chunk':
        appendToAssistantMessage(data.content);
        break;
      case 'done':
        finalizeAssistantMessage(data.assistant_message);
        break;
      case 'error':
        showError(data.error);
        break;
    }
  },
});
```

---

#### 4.2 Отправить сообщение без streaming (legacy)

```
POST /api/chat/conversations/{id}/send_message/
```

Работает как раньше — возвращает полный ответ после завершения генерации.
Теперь также поддерживает `multipart/form-data` для загрузки файлов.

**Формат 1: JSON (только текст)**
```json
{
  "content": "Привет! Расскажи о себе."
}
```

**Формат 2: multipart/form-data (текст + файлы)**
```
content: "Что на этом изображении?"
files: [file1.png]
```

**Ответ (201 Created):**
```json
{
  "user_message": {
    "id": 1,
    "conversation": 1,
    "role": "user",
    "content": "Привет! Расскажи о себе.",
    "model": null,
    "tokens_used": null,
    "attachments": [],
    "created_at": "2026-03-07T15:30:00Z",
    "updated_at": "2026-03-07T15:30:00Z"
  },
  "assistant_message": {
    "id": 2,
    "conversation": 1,
    "role": "assistant",
    "content": "Привет! Я — AI-ассистент, работающий через OpenRouter...",
    "model": "openai/gpt-4o-mini",
    "tokens_used": 234,
    "attachments": [],
    "created_at": "2026-03-07T15:30:02Z",
    "updated_at": "2026-03-07T15:30:02Z"
  }
}
```

---

## Загрузка файлов — Подробности

### Поддерживаемые типы файлов

| Тип | MIME-типы | Как обрабатывается | Требует vision? |
|-----|-----------|-------------------|-----------------|
| **Изображения** | `image/png`, `image/jpeg`, `image/gif`, `image/webp` | Конвертируется в base64 data URL и отправляется как `image_url` в OpenRouter API | ✅ Да |
| **Текстовые файлы** | `text/plain`, `text/csv`, `text/html`, `text/markdown`, `application/json`, `application/xml`, `text/xml` | Содержимое читается и вставляется как текст в контекст сообщения | ❌ Нет |
| **PDF** | `application/pdf` | Описание файла добавляется в контекст (полное извлечение текста из PDF пока не реализовано) | ❌ Нет |

### Ограничения
- **Максимальный размер файла:** 20 MB
- **Количество файлов:** не ограничено (но учитывайте размер контекста модели)
- Файлы сохраняются на сервере и доступны по URL в поле `attachments[].url`

### Рекомендации для UI

1. **Проверяйте `supports_vision`** перед отправкой изображений:
   ```typescript
   const model = models.find(m => m.id === conversation.model);
   if (!model?.supports_vision && hasImageFiles) {
     showWarning('Выбранная модель не поддерживает изображения. Переключитесь на модель с поддержкой vision.');
   }
   ```

2. **Показывайте превью** прикреплённых файлов перед отправкой

3. **Отображайте вложения** в истории сообщений:
   - Для изображений — показывайте миниатюру (используйте `attachments[].url`)
   - Для текстовых файлов — показывайте иконку файла + имя
   - Для PDF — показывайте иконку PDF + имя

4. **Drag & Drop** — рекомендуется поддержать перетаскивание файлов в область чата

---

## Типичный flow на фронтенде

### Открытие страницы чата
1. `GET /api/chat/models/` — загрузить список доступных моделей (для UI выбора). Сохранить `supports_vision` для каждой модели.
2. `GET /api/chat/conversations/` — загрузить список чатов пользователя

### Создание нового чата
1. `POST /api/chat/conversations/` — создать чат (можно указать `model`, `system_prompt`)
2. Показать пустой чат, фокус на поле ввода

### Открытие существующего чата
1. `GET /api/chat/conversations/{id}/messages/` — загрузить историю сообщений (включая `attachments`)

### Отправка сообщения (РЕКОМЕНДУЕМЫЙ FLOW со streaming)
1. Пользователь вводит текст и (опционально) прикрепляет файлы
2. **Сразу** показать сообщение пользователя в UI (оптимистичный рендеринг)
3. Показать индикатор "AI печатает..."
4. `POST /api/chat/conversations/{id}/send_message_stream/` (с `multipart/form-data` если есть файлы)
5. Обработать SSE события:
   - `user_message` → обновить ID сообщения пользователя (заменить оптимистичное на реальное)
   - `chunk` → добавлять текст к сообщению ассистента в реальном времени
