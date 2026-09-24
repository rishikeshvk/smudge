import re

THUMBS = "👍"
HEART = "❤️"
LAUGH = "😄"
MOON = "🌙"

# A closed list, so nothing with real content, a crisis included, can ever match.
REACTIONS = {
    **dict.fromkeys(
        ["ok", "okay", "k", "kk", "cool", "sure", "got it", "sounds good", "will do"],
        THUMBS,
    ),
    **dict.fromkeys(["thanks", "thank you", "thx", "ty", "cheers"], HEART),
    **dict.fromkeys(["lol", "haha", "hahaha", "lmao"], LAUGH),
    **dict.fromkeys(["gn", "night", "good night", "goodnight"], MOON),
    **dict.fromkeys(["👍", "🙏", "❤️", "❤"], HEART),
    "😂": LAUGH,
}


def reaction_to(message: str, last_buddy_message: str | None) -> str | None:
    """The emoji a friend would react with instead of replying, or None when the
    message deserves a reply. An "ok" to a question is an answer, so it gets one."""
    if last_buddy_message is not None and last_buddy_message.rstrip().endswith("?"):
        return None
    return REACTIONS.get(_normalised(message))


def _normalised(message: str) -> str:
    # "Ok!!", "thanks." and "haha  " all count.
    return re.sub(r"\s+", " ", message.strip().lower()).rstrip(".!~ ")
