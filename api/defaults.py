"""Standaard show-instellingen (gelijk aan de kern van config.yaml)."""

DEFAULT_DURATION = {
    "max_minutes": 15.0,
    "item_minutes_top": 3.0,
    "item_minutes_floor": 1.0,
    "max_stretch": 3.0,
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
    "focus": "",  # geen regionale beperking; de gebruiker bepaalt de onderwerpen
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
MAX_MINUTES_CAP = 20.0
DURATION_CHOICES = (5, 10, 15, 20)  # streefduur in minuten
STYLES = ("zakelijk", "informeel", "verhalend")
MAX_SOURCES = 20
MAX_PODCASTS_PER_USER = 10
MAX_TOPIC_LENGTH = 200
MAX_ATTEMPTS = 3  # pogingen per generatie bij tijdelijke fouten

# Planning: de gebruiker bepaalt dagen en tijd. Standaard uit, zodat er nooit ongevraagd kosten ontstaan.
# days: 0 = maandag … 6 = zondag. time in lokale tijd van timezone.
DEFAULT_SCHEDULE = {
    "enabled": True,
    "days": [0, 1, 2, 3, 4, 5, 6],  # dagelijks; werkdagen = [0..4]; wekelijks = één dag
    "every_days": None,  # eigen interval (2-30 dagen); heeft voorrang op days
    "time": "07:00",  # moment waarop de aflevering klaarstaat
    "timezone": "Europe/Amsterdam",
}
SCHEDULE_LEAD_MINUTES = 45  # de generatie start zoveel minuten eerder, zodat de aflevering op het gekozen tijdstip klaarstaat
# Een geplande run mag hooguit zoveel uur na het gekozen tijdstip nog starten (worker was even weg).
SCHEDULE_CATCHUP_HOURS = 2
