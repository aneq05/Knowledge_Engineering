import pytest

from package_manager.loaders import load_repository, load_requests

OK = '{"packages": {"app": {"versions": {"1.0": {}}}}}'

# (opis, treść pliku JSON, fragment oczekiwanego komunikatu)
BAD_REPOSITORIES = [
    ("niepoprawny JSON", '{"packages": ', "repo.json:1:"),
    ("brak packages", "{}", "brak wymaganego pola"),
    ("nieznane pole", '{"packages": {}, "foo": 1}', "nieznane pole"),
    ("requires nie jest listą", '{"packages": {"a": {"versions": {"1.0": {"requires": "b"}}}}}', "oczekiwano listy"),
    ("zła nazwa", '{"packages": {"bad name!": {"versions": {"1.0": {}}}}}', "Niepoprawna nazwa"),
    ("zła wersja", '{"packages": {"a": {"versions": {"1.x": {}}}}}', "Niepoprawna wersja"),
    ("zły operator", '{"packages": {"a": {"versions": {"1.0": {"requires": ["b =>1"]}}}}}', "Niepoprawne ograniczenie"),
    ("wersje 1.0 i 1.0.0", '{"packages": {"a": {"versions": {"1.0": {}, "1.0.0": {}}}}}', "powtarza"),
    ("pakiety Foo_Bar i foo-bar", '{"packages": {"Foo_Bar": {"versions": {"1.0": {}}}, "foo-bar": {"versions": {"1.0": {}}}}}', "powtórzony pakiet"),
    ("pakiet wymaga siebie", '{"packages": {"a": {"versions": {"1.0": {"requires": ["a"]}}}}}', "samego siebie"),
    ("pakiet konfliktuje z sobą", '{"packages": {"a": {"versions": {"1.0": {"conflicts": ["a"]}}}}}', "samym sobą"),
    ("powtórzony klucz", '{"packages": {"a": {"versions": {"1.0": {}, "1.0": {}}}}}', "powtórzony klucz"),
    ("pusty versions", '{"packages": {"a": {"versions": {}}}}', "co najmniej jedną wersję"),
]


@pytest.mark.parametrize(("name", "text", "fragment"), BAD_REPOSITORIES, ids=[b[0] for b in BAD_REPOSITORIES])
def test_bad_repository_is_rejected(tmp_path, name, text, fragment):
    path = tmp_path / "repo.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=fragment):
        load_repository(path)


def test_error_points_to_path_in_document(tmp_path):
    path = tmp_path / "repo.json"
    path.write_text('{"packages": {"app": {"versions": {"2.0": {"requires": ["ok", "x =>1"]}}}}}', encoding="utf-8")
    with pytest.raises(ValueError) as info:
        load_repository(path)
    assert "packages['app'].versions['2.0'].requires[1]" in str(info.value)


def test_file_with_bom_is_accepted(tmp_path):
    path = tmp_path / "repo.json"
    path.write_bytes(b"\xef\xbb\xbf" + OK.encode("utf-8"))
    assert "app" in load_repository(path).packages


def test_requests_error_has_line_number(tmp_path):
    path = tmp_path / "requests.txt"
    path.write_text("# komentarz\napp\n\nlib =>1\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"requests.txt:4:"):
        load_requests(path)


def test_requests_skip_comments_and_blank_lines(tmp_path):
    path = tmp_path / "requests.txt"
    path.write_text("# x\napp==2.0  # tak\n\ntool\n", encoding="utf-8")
    assert [str(r) for r in load_requests(path)] == ["app ==2.0", "tool"]
