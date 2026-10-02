from kindred_film.phone import Element, parse_elements

DUMP = (
    '<hierarchy><node index="0" text="" content-desc="" bounds="[0,0][1080,2400]">'
    '<node text="Continue" content-desc="" bounds="[60,2220][1020,2330]" />'
    '<node text="" content-desc="Send" bounds="[900,2200][1000,2300]" />'
    "</node></hierarchy>"
)


def test_labelled_elements_come_back_with_their_centres() -> None:
    assert parse_elements(DUMP) == [
        Element("Continue", 540, 2275),
        Element("Send", 950, 2250),
    ]
