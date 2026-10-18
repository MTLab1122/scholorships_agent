import os
from unittest.mock import patch
from agent.emailer import ResendEmailer, _sanitize_recipient


def test_sanitize_recipient():
    assert _sanitize_recipient("  user@example.com  ") == "user@example.com"
    assert _sanitize_recipient("") == ""


def test_emailer_forward_recipient_from_env():
    with patch.dict(os.environ, {"FORWARD_EMAIL": "forward.user@example.com"}):
        emailer = ResendEmailer()
        assert emailer.forward_email == "forward.user@example.com"


def test_emailer_recipient_list_sanitization():
    emailer = ResendEmailer(to_email=["user1@example.com", "user2@example.com"])
    assert "user1@example.com" in emailer.to_email
    assert "user2@example.com" in emailer.to_email
