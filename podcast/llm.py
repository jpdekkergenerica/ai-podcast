import anthropic

_client = None


def ask(prompt: str, *, model: str, system: str = "", max_tokens: int = 4000) -> str:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    msg = _client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")
