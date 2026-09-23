from kindred_api.openapi_export import openapi_with_contracts


def test_contracts_the_app_reads_are_in_the_schema() -> None:
    schemas = openapi_with_contracts()["components"]["schemas"]

    for name in [
        "ChatTurn",
        "RetrievedNote",
        "RoadmapEntry",
        "StudyNote",
        "TopicRef",
        "TurnTrace",
    ]:
        assert name in schemas


def test_contracts_merge_alongside_endpoint_schemas() -> None:
    schemas = openapi_with_contracts()["components"]["schemas"]

    retrieved = schemas["TurnTrace"]["properties"]["retrieved"]
    assert retrieved["items"] == {"$ref": "#/components/schemas/RetrievedNote"}
    assert "HealthResponse" in schemas
