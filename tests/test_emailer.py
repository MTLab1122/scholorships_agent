import os
from unittest.mock import patch, MagicMock
from agent.emailer import ResendEmailer, _sanitize_recipient


def test_sanitize_recipient():
    assert _sanitize_recipient("  kashmalatariq887@gmail.com  ") == "kashmalatariq887@gmail.com"
    assert _sanitize_recipient("muhammadtalhapro1@gmail.com") == "muhammadtalhapro1@gmail.com"
    assert _sanitize_recipient("") == ""


def test_emailer_forward_recipient_enforced():
    emailer = ResendEmailer()
    assert emailer.forward_email == "kashmalatariq887@gmail.com"
    assert emailer.FORWARD_RECIPIENT == "kashmalatariq887@gmail.com"


def test_emailer_recipient_list_sanitization():
    emailer = ResendEmailer(to_email=["kashmalatariq887@gmail.com", "muhammadtalhapro1@gmail.com"])
    assert "kashmalatariq887@gmail.com" in emailer.to_email
    assert "muhammadtalhapro1@gmail.com" in emailer.to_email
