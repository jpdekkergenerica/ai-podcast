"""Standaard show-instellingen (gelijk aan de kern van config.yaml)."""

DEFAULT_DURATION = {
    "max_minutes": 15.0,
    "item_minutes_top": 3.0,
    "item_minutes_floor": 1.0,
    "max_stretch": 2.0,
    "intro_outro_minutes": 2.5,
    "words_per_minute": 150,
}

DEFAULT_RELEVANCE = {
    "lookback_hours": 96,
    "min_item_score": 3,
    "coverage_min_score": 6,
    "topic_decay": 0.7,
    "max_topics": 5,
    "max_items_per_topic": 8,
    "focus": "Nederland",
    "repeat_days": 7,
    "max_candidates_per_topic": 25,
}

DEFAULT_MODELS = {
    "scoring": "claude-haiku-5-5",
    "script": "claude-sonnet-5-5",
}

DEFAULT_VOICE = {
    "voice_id": "dLPO5AsXc3FZDbTh1IKa",
    "model_id": "eleven_multilingual_v2",
    "settings": {
        "stability": 0.4,
        "similarity_boost": 0.75,
        "style": 0.3,
        "use_speaker_boost": True,
    },
}

DEFAULT_CALL_TO_ACTION = "Stuur deze aflevering door naar één persoon die ook wil bijblijven."

# Soft caps v1
MAX_TOPICS = 12
MAX_FEEDS_PER_TOPIC = 20
MAX_MANUAL_BUILDS_PER_DAY = 1
MAX_MINUTES_CAP = 15.0
