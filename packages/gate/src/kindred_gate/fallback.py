from kindred_contracts import Directive, Route

# Sent without an audit, so these may only ever render public fields: titles and days.
OUT_OF_PLAN = (
    "That one isn't on our plan, so I genuinely haven't studied it. "
    "Want to see if it fits in after we finish?"
)
LOCKED_TOPIC = (
    "Ah, that's {title} territory, which is day {day} on our plan. I haven't studied "
    "it yet, so I'd rather not guess. Want to pull it forward?"
)
UNSURE = (
    "Hmm, I'm not sure I've covered that yet, so I'd rather not guess. "
    "Could you ask me in a different way?"
)

# The persona steps aside here: plain words and real help, never study talk.
CRISIS = (
    "I'm going to step out of study-buddy mode, because this matters more than any "
    "plan. I'm an AI, so I can't be the help you deserve right now, but a real person "
    "can. If you might hurt yourself or you're in danger, please call your local "
    "emergency number. You can also reach a free, confidential crisis line: "
    "findahelpline.com lists the ones in your country."
)


def fallback_reply(directive: Directive) -> str:
    if directive.route is Route.CRISIS:
        return CRISIS
    if directive.route is Route.DEFLECT_OUT_OF_PLAN:
        return OUT_OF_PLAN
    if directive.deflect_topics:
        earliest = min(directive.deflect_topics, key=lambda topic: topic.day)
        return LOCKED_TOPIC.format(title=earliest.title, day=earliest.day)
    return UNSURE
