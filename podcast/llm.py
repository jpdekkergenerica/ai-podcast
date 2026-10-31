import json

import anthropic

_client = None


def ask(prompt: str, *, model: str, system: str = "", max_tokens: int = 4000, thinking: dict | None = None) -> str:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    extra = {"thinking": thinking} if thinking else {}
    for attempt in range(2):
        with _client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            **extra,
        ) as stream:
            msg = stream.get_final_message()
        text = "".join(b.text for b in msg.content if b.type == "text").strip()
        if text:
            return text
        kinds = [b.type for b in msg.content]
        print(f"Waarschuwing: leeg antwoord van {model} (stop_reason={msg.stop_reason}, "
              f"blokken={kinds}, tokens={msg.usage.output_tokens}), poging {attempt + 1}/2")
    raise RuntimeError(f"{model} gaf twee keer een leeg antwoord (stop_reason={msg.stop_reason}, blokken={kinds})")


def _json_object(raw: str, required: str, kind: type) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("geen JSON-object")
    data = json.loads(raw[start:end + 1])
    if not isinstance(data, dict) or not isinstance(data.get(required), kind):
        raise ValueError(f"sleutel {required} ontbreekt of heeft het verkeerde type")
    return data


def ask_json(prompt: str, *, model: str, required: str, kind: type, system: str = "",
             max_tokens: int = 4000, thinking: dict | None = None) -> dict:
    """Vraagt een JSON-object. Lukt het lezen niet, dan volgt één reparatiepoging; daarna stopt de aanroep."""
    raw = ask(prompt, model=model, system=system, max_tokens=max_tokens, thinking=thinking)
    try:
        return _json_object(raw, required, kind)
    except ValueError as first:
        print(f"Waarschuwing: JSON niet leesbaar ({first}), één reparatiepoging")
        fixed = ask(
            f"Je vorige antwoord was geen geldige JSON met een sleutel '{required}'. "
            "Geef uitsluitend dat JSON-object, zonder uitleg of codeblok.\n\n"
            f"{raw}",
            model=model, system=system, max_tokens=max_tokens, thinking=thinking,
        )
        try:
            return _json_object(fixed, required, kind)
        except ValueError as e:
            raise RuntimeError(f"{model} gaf geen leesbare JSON (sleutel {required})") from e


SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 5}


def ask_with_search(prompt: str, *, model: str, system: str = "", max_tokens: int = 8000,
                    max_uses: int = 5) -> tuple[str, set[str]]:
    """Vraagt het model met de webzoektool. Geeft (tekst, adressen die echt in de zoekresultaten stonden).

    De adressenlijst dient als controle: een bericht met een adres dat niet uit de zoekresultaten komt is verzonnen."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    tool = {**SEARCH_TOOL, "max_uses": max_uses}
    messages = [{"role": "user", "content": prompt}]
    urls: set[str] = set()
    for _ in range(5):  # pause_turn: de server heeft het zoeken onderbroken; hervatten door het antwoord terug te geven
        with _client.messages.stream(model=model, max_tokens=max_tokens, system=system, messages=messages,
                                     tools=[tool], output_config={"effort": "medium"}) as stream:
            msg = stream.get_final_message()
        for block in msg.content:
            if block.type == "web_search_tool_result" and isinstance(block.content, list):
                urls.update(r.url for r in block.content if getattr(r, "url", None))
            for c in getattr(block, "citations", None) or []:
                if getattr(c, "url", None):
                    urls.add(c.url)
        if msg.stop_reason == "pause_turn":
            messages = [messages[0], {"role": "assistant", "content": msg.content}]
            continue
        return "".join(b.text for b in msg.content if b.type == "text").strip(), urls
    raise RuntimeError(f"{model} bleef zoeken zonder af te ronden")
