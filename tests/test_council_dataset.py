import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("council_dataset", Path(__file__).parents[1] / "scripts" / "council_dataset.py")
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)


def test_symmetric_swap_is_only_a_reversed_between_phrase():
    a = "Approves a contract between the Metropolitan Board of Health and the Tennessee Department of Health for exams."
    b = "Approves a contract between the Tennessee Department of Health and the Metropolitan Board of Health for exams."
    assert cd.symmetric_swap(a, b)
    giver = "Gives $50,000 from the Juvenile Court to Pathways Kitchen Corporation through a grant."
    receiver = "Gives $50,000 from the Pathways Kitchen Corporation to Juvenile Court through a grant."
    assert not cd.symmetric_swap(giver, receiver)
    assert not cd.symmetric_swap(a, a.replace("Health for", "Health, for"))
