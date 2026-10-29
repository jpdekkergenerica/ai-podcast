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
