from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ComplyADI - GIFT City Compliance Assistant"
    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Security
    jwt_secret_key: str = "super_secret_complyadi_giftcity_key_change_in_prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password123@localhost:5432/compliance_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "gift_city_compliance"
    qdrant_api_key: str = ""

    # Groq Provider
    groq_api_key: str = ""
    groq_primary_model: str = "openai/gpt-oss-120b"
    groq_fallback_model: str = "qwen/qwen-2.5-32b"

    # OpenAI Backup
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Guardrails & Gibberish Detection
    enable_guardrails: bool = True
    enable_gibberish_detector: bool = True
    gibberish_min_vowel_ratio: float = 0.15
    gibberish_max_repeat_chars: int = 4
    compliance_company_name: str = "ADI International"
    compliance_jurisdiction: str = "GIFT City IFSC, Gujarat, India"
    blocked_offtopic_keywords: list[str] = [
        "cricket", "ipl", "recipe", "movie", "football", "song", "lyrics",
        "weather", "horoscope", "joke", "poem", "story", "python code",
        "javascript", "react code", "write code", "hack", "bitcoin price",
        "today date", "todays date", "today's date", "current time", "birthday",
        "celebrity", "actor", "actress", "cooking", "gaming", "astrology",
    ]

    # Smalltalk / Conversational Vocabulary (handled locally at 0 LLM token cost)
    smalltalk_vocab: list[str] = [
        # Greetings
        "hi", "hii", "hiii", "hello", "helloo", "hey", "heyy", "hola", "namaste",
        "namaskar", "good morning", "good afternoon", "good evening", "good night",
        "morning", "evening", "howdy", "greetings", "yo", "sup", "what's up", "whats up",
        # Courtesy & Polite Phrases
        "excuse me", "pardon", "pardon me", "sorry", "my bad", "please",
        "how are you", "how r u", "hru", "how are u", "who are you", "what are you",
        "nice to meet you", "pleased to meet you",
        # Gratitude & Acknowledgments
        "thanks", "thank you", "thank u", "thx", "ty", "tysm", "thankyou",
        "appreciate it", "much appreciated", "ok", "okay", "kk", "cool", "great",
        "awesome", "got it", "understood", "alright", "fine", "good", "nice",
        # Farewells
        "bye", "byee", "goodbye", "good bye", "see you", "see ya", "cya",
        "take care", "tc", "later", "catch you later", "gn", "tata",
    ]

    # Dynamic NLP / Retrieval / Graph Tuning
    stopwords: list[str] = [
        "what", "which", "where", "when", "does", "have", "with", "from",
        "that", "this", "tell", "about", "your", "some", "more", "and", "the", "for",
    ]
    short_compliance_terms: list[str] = ["tax", "ibu", "fme", "gst", "kyc", "aml", "sez", "ifsc", "ifsca", "mat", "tds"]
    retrieval_scan_limit: int = 8
    retrieval_top_k: int = 3
    direct_hit_threshold: float = 0.75
    llm_history_window: int = 4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
