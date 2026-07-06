from unittest.mock import MagicMock, patch

from tools.twillo_tool import send_whatsapp_message


def test_send_whatsapp_message_approved_success():
    args = {"to_number": "9959995587", "body": "Test message"}

    with patch("tools.twillo_tool.interrupt") as mock_interrupt, \
         patch("tools.twillo_tool.client") as mock_client, \
         patch("tools.twillo_tool.time.sleep"):

        mock_interrupt.return_value = {"status": "approved", "text_msg": args["body"]}
        mock_client.messages.create.return_value = MagicMock(sid="fake_sid")
        mock_client.messages.return_value.fetch.return_value = MagicMock(
            sid="fake_sid", status="sent", error_message=None
        )

        result = send_whatsapp_message.invoke(args)

        assert result.status == "success"
        assert result.message_sid == "fake_sid"


def test_send_whatsapp_message_rejected():
    args = {"to_number": "9959995587", "body": "Test message"}

    with patch("tools.twillo_tool.interrupt") as mock_interrupt, \
         patch("tools.twillo_tool.client") as mock_client:

        mock_interrupt.return_value = {"status": "rejected", "text_msg": "declined by user"}

        result = send_whatsapp_message.invoke(args)

        assert result.status == "fail"
        mock_client.messages.create.assert_not_called()


def test_send_whatsapp_message_twilio_error():
    args = {"to_number": "9959995587", "body": "Test message"}

    with patch("tools.twillo_tool.interrupt") as mock_interrupt, \
         patch("tools.twillo_tool.client") as mock_client:

        mock_interrupt.return_value = {"status": "approved", "text_msg": args["body"]}
        mock_client.messages.create.side_effect = Exception("Twilio is down")

        result = send_whatsapp_message.invoke(args)

        assert result.status == "fail"
        assert "Twilio is down" in result.error_message
