from dashboard.app import app as flask_app
from dashboard.csrf import generate_csrf_token, validate_csrf_token


def test_csrf_token_round_trip():
    with flask_app.test_request_context("/"):
        token = generate_csrf_token()

        assert token
        assert validate_csrf_token(token) is True
        assert validate_csrf_token("wrong-token") is False
        assert validate_csrf_token(None) is False


def test_csrf_token_is_stable_within_a_session():
    with flask_app.test_request_context("/"):
        first_token = generate_csrf_token()
        second_token = generate_csrf_token()

        assert first_token == second_token
