from app.services.math_verifier import verify_math_request
from app.math.equivalence import check_expression_equivalence


def test_surds_grounding_excludes_pi_as_surd():
    result = verify_math_request("what are surds", concept_key="surds")

    assert result.status == "conceptual"
    assert result.source == "sympy_rulebook"
    assert "Pi is irrational, but it is not a surd" in result.response_text


def test_quadratic_grounding_factorises_and_solves_plain_language_expression():
    result = verify_math_request(
        "solve x squared plus 5x plus 6",
        concept_key="quadratic_equations",
    )

    assert result.status == "verified"
    assert result.source == "sympy"
    assert "(x + 2)*(x + 3)" in result.response_text
    assert "x = -3, -2" in result.response_text


def test_unsupported_prompt_does_not_claim_verification():
    result = verify_math_request("explain indices", concept_key="indices")

    assert result.status == "unsupported"
    assert result.response_text is None


def test_math_verify_equivalence_layer_accepts_equivalent_expressions():
    assert check_expression_equivalence("(x + 2)*(x + 3)", "x**2 + 5*x + 6")
