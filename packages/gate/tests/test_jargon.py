from kindred_contracts import VocabularyKind, VocabularyTerm
from kindred_gate.jargon import jargon_in, mentions
from kindred_gate.topics import TopicMap


def term(word: str, kind: VocabularyKind = VocabularyKind.TERM) -> VocabularyTerm:
    return VocabularyTerm(term=word, kind=kind)


def test_terms_match_whole_words_ignoring_case() -> None:
    assert mentions("Bucket Policies decide it", term("bucket policy")) is False
    assert mentions("a Bucket Policy decides it", term("bucket policy"))
    assert not mentions("subucket policy-free", term("bucket policy"))


def test_abbreviations_match_case_exactly() -> None:
    assert mentions("the SG allows it", term("SG", VocabularyKind.ABBREVIATION))
    assert not mentions("sg allows it", term("SG", VocabularyKind.ABBREVIATION))


def test_only_locked_specialist_terms_are_flagged(topics: TopicMap) -> None:
    now = topics.topics[0].unlock_at

    found = jargon_in(
        "An IAM principal puts things in a bucket; S3 and an AMI come later.",
        topics,
        now,
    )

    # IAM is unlocked, "bucket" is everyday and "S3" is in a public title.
    assert [(topic.slug, word.term) for topic, word in found] == [("ec2-basics", "AMI")]
