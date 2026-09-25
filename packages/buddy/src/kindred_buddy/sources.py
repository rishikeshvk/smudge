from kindred_contracts import SourceExcerpt


def excerpts(sources: list[SourceExcerpt], budget_chars: int) -> str:
    """A topic's sources for a prompt, within a character budget."""
    # Split the budget evenly so one long page can't crowd out the rest.
    share = budget_chars // len(sources)
    return "\n\n".join(
        f"[{source.title}]({source.url})\n{source.text[:share]}" for source in sources
    )
