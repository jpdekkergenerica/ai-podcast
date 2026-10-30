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
