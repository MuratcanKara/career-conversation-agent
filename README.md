# Career Conversation Agent

Kişisel kariyer asistanı — İK profesyonellerine yönelik, özgeçmiş bilgileri üzerinden otonom yanıt veren agentic chatbot. OpenAI Function Calling ve Gradio ile çalışır.

Demo: [huggingface.co/spaces/Muratcan22/career_conversation_v3](https://huggingface.co/spaces/Muratcan22/career_conversation_v3)

## Mimari

```
┌──────────────────────────────────────────┐
│           Gradio ChatInterface           │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│               Me (Agent)                 │
│                                          │
│  ┌──────────────┐   ┌────────────────┐   │
│  │ System Prompt │   │   Evaluator    │   │
│  │  (gpt-4o-mini)│   │ (gpt-4o-mini) │   │
│  └──────┬───────┘   └───────┬────────┘   │
│         │                   │            │
│  ┌──────▼───────────────────▼────────┐   │
│  │          Tool Functions           │   │
│  │  record_user_details              │   │
│  │  request_meeting                  │   │
│  │  search_knowledge_database        │   │
│  │  get_resume_link                  │   │
│  │  record_unknown_question          │   │
│  └───────────────────────────────────┘   │
│              │              │            │
│       SQLite (FAQ)    Pushover API       │
└──────────────────────────────────────────┘
```

## Özellikler

- **Kariyer Bilgi Sunumu** — LinkedIn profili ve PDF özgeçmişten okunan verilerle sorulara yanıt
- **Bilgi Bankası Sorgusu** — SQLite veritabanında proje, beceri ve deneyim araması
- **Toplantı Planlama** — İsim, email ve zaman bilgisi alarak toplantı talebi oluşturma
- **Kalite Kontrol (Evaluator)** — Her yanıt ikinci bir model tarafından doğrulanır
- **Pushover Bildirimler** — Kullanıcı kaydı, toplantı talebi ve cevaplanamayan sorularda anlık bildirim
- **Çift Dil Desteği** — Kullanıcının diline (TR/EN) otomatik uyum

## Kurulum

```bash
git clone https://github.com/Muratcan22/career-agent.git
cd career-agent

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Gerekli Dosyalar

```
career-agent/
├── career_conversation.py
├── me/
│   ├── Profile.pdf          # LinkedIn profil PDF'i (gitignored)
│   ├── summary.txt          # Kişisel özet metni (gitignored)
│   └── summary.example.txt  # Şablon dosya
├── my_knowledge.db           # SQLite bilgi bankası (FAQ tablosu)
├── requirements.txt
├── .env.example
└── .env                      # (gitignored)
```

> `me/Profile.pdf` ve `me/summary.txt` kişisel veri içerdiği için repo'ya dahil edilmez. `summary.example.txt` şablonunu referans alarak kendi dosyalarınızı oluşturun.

### Ortam Değişkenleri

```bash
cp .env.example .env
# .env dosyasını kendi anahtarlarınızla doldurun
```

### Çalıştırma

```bash
python career_conversation.py
```

Uygulama `http://localhost:7860` adresinde açılır.

## Teknolojiler

- **LLM:** OpenAI API (gpt-4o-mini) — Function Calling + Structured Output
- **UI:** Gradio ChatInterface
- **Veritabanı:** SQLite (bilgi bankası)
- **Bildirim:** Pushover API
- **Veri Kaynakları:** pypdf (PDF okuma), dotenv (ortam değişkenleri)
