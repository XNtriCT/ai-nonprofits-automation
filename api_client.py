"""Unified API client — routes chat completions to the selected provider."""

from config import cfg

PROVIDER_CONFIGS = {
    "freellmapi": {"base_url": "http://172.24.197.38:3001/v1", "sdk": "openai", "label": "FreeLLMAPI"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "sdk": "openai", "label": "OpenRouter"},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "sdk": "openai", "label": "Groq"},
    "deepseek": {"base_url": "https://api.deepseek.com", "sdk": "openai", "label": "DeepSeek"},
    "nvidia": {"base_url": "https://integrate.api.nvidia.com/v1", "sdk": "openai", "label": "NVIDIA"},
    "google": {"base_url": "https://generativelanguage.googleapis.com", "sdk": "google", "label": "Google AI Studio"},
    "custom": {"base_url": "", "sdk": "openai", "label": "Custom (OpenAI-compatible)"},
}

DEFAULT_MODELS = {
    "freellmapi": "gpt-4o",
    "openrouter": "openai/gpt-oss-120b:free",
    "groq": "llama-3.3-70b-versatile",
    "deepseek": "deepseek-v4-flash",
    "nvidia": "nvidia/nemotron-3-super-120b-a12b",
    "google": "gemini-2.5-flash",
    "custom": "gpt-4o",
}


def _resolve_url():
    provider = cfg.PROVIDER
    config = PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS["custom"])
    return cfg.BASE_URL or config.get("base_url", "")


def chat_completion(messages, model=None, temperature=0.7, max_tokens=1000):
    provider = cfg.PROVIDER
    api_key = cfg.API_KEY
    model = model or cfg.MODEL or DEFAULT_MODELS.get(provider, "gpt-4o")
    config = PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS["custom"])

    if config["sdk"] == "google":
        return _google_chat(messages, model, api_key, temperature, max_tokens)
    else:
        return _openai_chat(messages, model, api_key, _resolve_url(), temperature, max_tokens)


def _openai_chat(messages, model, api_key, base_url, temperature, max_tokens):
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url or None)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def _google_chat(messages, model, api_key, temperature, max_tokens):
    content = _messages_to_google_prompt(messages)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model=model, contents=content)
        return resp.text.strip()
    except ImportError:
        pass

    import google.generativeai as genai
    genai.configure(api_key=api_key)
    gm = genai.GenerativeModel(model)
    resp = gm.generate_content(content)
    return resp.text.strip()


def _messages_to_google_prompt(messages):
    parts = []
    for m in messages:
        role = m.get("role", "user")
        text = m.get("content", "")
        if role == "system":
            parts.append(f"[System Instruction]\n{text}")
        elif role == "user":
            parts.append(f"[User]\n{text}")
        elif role == "assistant":
            parts.append(f"[Assistant]\n{text}")
    return "\n\n".join(parts)


def fetch_models():
    """Return sorted model ID list for the current provider, or empty list."""
    provider = cfg.PROVIDER
    api_key = cfg.API_KEY
    config = PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS["custom"])

    if config["sdk"] != "openai":
        return []

    base_url = _resolve_url()
    if not base_url:
        return []

    try:
        import requests
        resp = requests.get(f"{base_url}/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        data = resp.json()
        ids = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
        ids.sort()
        return ids
    except Exception:
        return []
