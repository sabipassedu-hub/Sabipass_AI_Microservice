from concurrent.futures import TimeoutError as SymPyTimeoutError

from app.services.math_verifier import verify_math_request
from app.math.equivalence import check_expression_equivalence


def test_surds_grounding_excludes_pi_as_surd():
    result = verify_math_request("what are surds", concept_key="surds")

    assert result.status == "conceptual"
    assert result.source == "sympy_rulebook"
    assert "Pi is irrational, but it is not a surd" in result.response_text


def test_quadratic_grounding_factorises_and_solves_plain_language_expression(monkeypatch):
    monkeypatch.setenv("SYMPY_TIMEOUT_MS", "2000")

    result = verify_math_request(
        "solve x squared plus 5x plus 6",
        concept_key="quadratic_equations",
    )

    assert result.status == "verified"
    assert result.source == "sympy"
    assert "(x + 2)*(x + 3)" in result.response_text
    assert "x = -3, -2" in result.response_text


def test_quadratic_grounding_uses_bounded_sympy_worker(monkeypatch):
    calls = []

    def fake_execute_sympy_verification(task_name, payload):
        calls.append((task_name, payload))
        return {
            "expression": "x**2 + 5*x + 6",
            "factorized": "(x + 2)*(x + 3)",
            "roots": ["-3", "-2"],
        }

    monkeypatch.setattr(
        "app.services.math_verifier.execute_sympy_verification",
        fake_execute_sympy_verification,
    )

    result = verify_math_request(
        "solve x squared plus 5x plus 6",
        concept_key="quadratic_equations",
    )

    assert calls == [
        (
            "factor_and_solve_zero",
            {"expression": "x**2 + 5*x + 6"},
        )
    ]
    assert result.status == "verified"
    assert result.source == "sympy"


def test_quadratic_timeout_fails_closed_to_conceptual_fallback(monkeypatch):
    def fake_execute_sympy_verification(task_name, payload):
        raise SymPyTimeoutError("timed out")

    monkeypatch.setattr(
        "app.services.math_verifier.execute_sympy_verification",
        fake_execute_sympy_verification,
    )

    result = verify_math_request(
        "solve x squared plus 5x plus 6",
        concept_key="quadratic_equations",
    )

    assert result.status == "conceptual"
    assert result.source == "sympy_timeout"
    assert "could not verify the exact factors quickly" in result.response_text
    assert "do not claim exact roots" in result.prompt_context


def test_unsupported_prompt_does_not_claim_verification():
    result = verify_math_request("explain indices", concept_key="indices")

    assert result.status == "unsupported"
    assert result.response_text is None


def test_math_verify_equivalence_layer_accepts_equivalent_expressions():
    assert check_expression_equivalence("(x + 2)*(x + 3)", "x**2 + 5*x + 6")
