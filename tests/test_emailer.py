import os
from unittest.mock import patch, MagicMock
from agent.emailer import ResendEmailer, _sanitize_recipient


def test_sanitize_recipient():
    assert _sanitize_recipient("hassantariq603@gmail.com") == "kashmalatariq887@gmail.com"
    assert _sanitize_recipient("HassanTariq@yahoo.com") == "kashmalatariq887@gmail.com"
    assert _sanitize_recipient("kashmalatariq887@gmail.com") == "kashmalatariq887@gmail.com"
    assert _sanitize_recipient("muhammadtalhapro1@gmail.com") == "muhammadtalhapro1@gmail.com"
    assert _sanitize_recipient("") == ""


def test_emailer_environment_override():
    with patch.dict(os.environ, {"FORWARD_EMAIL": "hassantariq603@gmail.com"}):
        emailer = ResendEmailer()
        assert emailer.forward_email == "kashmalatariq887@gmail.com"

    with patch.dict(os.environ, {"RECIPIENT_EMAIL": "hassantariq603@gmail.com", "FORWARD_EMAIL": ""}):
        emailer = ResendEmailer()
        assert emailer.forward_email == "kashmalatariq887@gmail.com"


def test_emailer_recipient_list_sanitization():
    emailer = ResendEmailer(to_email=["hassantariq603@gmail.com", "muhammadtalhapro1@gmail.com"])
    assert "hassantariq603@gmail.com" not in emailer.to_email
    assert "kashmalatariq887@gmail.com" in emailer.to_email
