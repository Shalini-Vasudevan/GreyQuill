from score_pair import PLAN, score_pair


def rec(**kw):
    base = dict(name="", email="", phone="", city="", pin_code="", date_of_birth="")
    base.update(kw)
    return base


def test_blank_fields_are_skipped():
    r = score_pair(rec(name="Rohan Gupta", phone=""), rec(name="rohan gupta", phone="9420505680"), PLAN)
    assert set(r.field_scores) == {"name"}
    assert r.confidence == 1.0


def test_nothing_comparable_is_zero():
    r = score_pair(rec(), rec(name="A"), PLAN)
    assert r.confidence == 0.0 and r.field_scores == {}


def test_phone_formats():
    a, b = rec(phone="+91 92792 45222"), rec(phone="09279245222")
    assert score_pair(a, b, PLAN).field_scores["phone"] == 1.0
    assert score_pair(rec(phone="+91-9279245222"), rec(phone="927-924-5222"), PLAN).field_scores["phone"] == 1.0
    assert score_pair(rec(phone="9279245222"), rec(phone="9279245223"), PLAN).field_scores["phone"] == 0.0


def test_dates_in_every_format():
    for other in ("1998-10-13", "13/10/1998", "13.10.98", "13-Oct-1998"):
        r = score_pair(rec(date_of_birth="13/10/1998"), rec(date_of_birth=other), PLAN)
        assert r.field_scores["date_of_birth"] == 1.0, other


def test_exact_trims_and_ignores_case():
    r = score_pair(rec(city=" Pune "), rec(city="PUNE"), PLAN)
    assert r.field_scores["city"] == 1.0


def test_name_variants_score_well():
    for x, y in [("Patel, Fatima", "FATHIMA PATEL"), ("S. Bhat", "Swathi Bhat"), ("Naveen Rao", "Rao, Naveen")]:
        assert score_pair(rec(name=x), rec(name=y), PLAN).field_scores["name"] >= 0.9, (x, y)
    assert score_pair(rec(name="Karthik Patel"), rec(name="Priya Nair"), PLAN).field_scores["name"] < 0.5


def test_confidence_bounds_and_algorithm():
    r = score_pair(rec(name="A B", email="a@x.com", phone="1"), rec(name="A B", email="a@x.com", phone="1"), PLAN)
    assert 0.0 <= r.confidence <= 1.0
    assert r.algorithm == "phonetic+edit_distance+normalized_phone"
