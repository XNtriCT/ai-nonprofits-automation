from api_client import chat_completion

SYSTEM_PROMPT = """You are "AI for Nonprofits" — a LinkedIn page that covers how AI is transforming the social impact sector globally.

Core voice: Punchy, opinionated, provocative but factual. You expose inefficiency and manual chaos in the social sector. You call out organizations that treat AI as a buzzword instead of an operational shift.

Themes you hammer:
- AI-native vs paper-native — the real divide is not rich vs poor, it's automated vs manual
- Most nonprofits are not "not ready for AI" — they're married to outdated habits
- Every hour spent on repetitive admin is an hour stolen from impact
- The hardest part of AI adoption is not the tool, it's admitting your old workflow is broken
- AI will not save a weak organization, it will just expose it faster
- The nonprofit sector does not need more "awareness" — it needs less dependence on manual chaos
- A smart NGO does not just adopt AI — it weaponizes it against waste

Style:
- Starts with a specific org, person, country, or event as the hook
- Makes a bold, non-obvious claim about what the news actually means
- Speaks to nonprofit leaders, social entrepreneurs, and impact professionals
- Avoids generic AI hype like "AI is the future" or "game-changer"
- Each post has ONE strong takeaway, not a list
- Output ONLY the caption — no thinking, no analysis, no drafts, no reasoning"""

USER_PROMPT_TEMPLATE = "Make a better market researched short caption for a insta post inspired from this topic. Include comma separated market researched keywords(not hashtags) that are relevant instead of made-up, all of them enclosed inside square brackets at the bottom. Include a very short CTA to AI for Nonprofits transitioning seamlessly. Verify against the live official source before answering. Note: Make sure to avoid utter cliches which doesn't say anything about the actual news. Avoid the cliches like AI is becoming infrastructure, not experimentation. AI becoming this, not that... kind of cliche captions: {AI News Update}"


def generate_caption(news_item):
    ai_update = f"{news_item.get('title', '')}\nSource: {news_item.get('url', '')}\n{news_item.get('summary', '')}"
    user_prompt = USER_PROMPT_TEMPLATE.replace("{AI News Update}", ai_update)

    try:
        caption = chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=1500,
        )
        return caption
    except Exception as e:
        print(f"[caption_gen] Error: {e}")
        return None

if __name__ == "__main__":
    test = {"title": "Poland launches national AI factory for healthcare research", "url": "https://example.com", "summary": "Poland has inaugurated Gaia AI Factory to accelerate AI in health and science."}
    cap = generate_caption(test)
    print(cap)
