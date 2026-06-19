from pathlib import Path
from api_client import chat_completion

_RULES_PATH = Path(__file__).parent / "image_prompt_rules.md"
_EXTRA_RULES = ""
if _RULES_PATH.exists():
    _EXTRA_RULES = "\n\n" + _RULES_PATH.read_text().strip()

SYSTEM_PROMPT = f"""You create high-converting image prompts for "AI for Nonprofits" LinkedIn posts — premium editorial style, scroll-stopping, grounded in real-world subjects.

Rules:
- POV-style composition without showing a hand
- The hook caption is embedded as text overlay — stylish, prominent, big, legible font
- Colors match the theme
- 1:1 aspect ratio (square)
- Feels real, grounded, and specific to the actual news topic
- Strictly NO futuristic AI cliches (no glowing brains, robot hands, circuit boards, blue digital streams, wireframe heads, holograms, code rain)
- Strictly NO social sector cliches (no shaking hands, no stock photo of a poor child, no clipart globe, no NGO acronym soup)
- Output ONLY the prompt — no thinking, no analysis, no reasoning, no drafts{_EXTRA_RULES}"""

USER_PROMPT_TEMPLATE = """We need a better high converting image relevant to this post. It should be non cliche. It should be eyecatching with a hook caption. POV style shot without the pov hand. The caption font and style should be very stylish, prominent, big and legible. Use colors to match the theme. Make it eyecatching. Aspect ratio 1:1.
Write a market researched better prompt that will bring the maximum audience and engagement. Don't give multiple options and confuse me. Just the one most high converting one after you have done the confidence scoring of various ideas internally.
Strictly no futuristic AI cliches.

Original News: {news_title}

Caption: {caption}"""


def generate_image_prompt(news_item, caption):
    user_prompt = USER_PROMPT_TEMPLATE.format(
        news_title=news_item.get("title", ""),
        caption=caption,
    )

    try:
        prompt = chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=800,
        )
        return prompt
    except Exception as e:
        print(f"[image_prompt_gen] Error: {e}")
        return None

if __name__ == "__main__":
    test = {"title": "Poland launches national AI factory for healthcare"}
    cap = "Poland's Gaia AI Factory is a loud reminder that AI is now national infrastructure, not Silicon Valley's private club."
    prompt = generate_image_prompt(test, cap)
    print(prompt)
