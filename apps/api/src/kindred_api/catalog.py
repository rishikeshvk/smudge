from datetime import datetime, timedelta
from pathlib import Path

import yaml

from kindred_contracts import Course, Curriculum, TopicRef
from kindred_gate import Topic, TopicMap


def load_curriculum(path: Path) -> Curriculum:
    return Curriculum.model_validate(yaml.safe_load(path.read_text()))


def load_catalog(directory: Path) -> list[Curriculum]:
    """The hand-written courses the Planner may offer."""
    return [load_curriculum(path) for path in sorted(directory.glob("*.yaml"))]


def as_course(curriculum: Curriculum) -> Course:
    return Course(
        slug=curriculum.slug,
        title=curriculum.title,
        topics=[
            TopicRef(slug=node.slug, title=node.title, day=node.day)
            for node in curriculum.nodes
        ],
        study_time=curriculum.study_time,
    )


def all_locked(courses: list[Curriculum], now: datetime) -> TopicMap:
    """Every course's topics, all still locked: nothing is studied during onboarding."""
    return TopicMap(
        plan_id=0,
        baseline_card=[item for course in courses for item in course.baseline_card],
        topics=[
            Topic(
                slug=node.slug,
                day=node.day,
                title=node.title,
                audit_brief=node.audit_brief,
                unlock_at=now + timedelta(days=node.day),
                vocabulary=node.vocabulary,
            )
            for course in courses
            for node in course.nodes
        ],
    )
