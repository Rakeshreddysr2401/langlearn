from tools.twillo_tool import send_whatsapp_message, WhatsAppMessageArgs
from unittest.mock import patch

def test_send_whatsapp_message_approval():
    args = {
        "to_number": "9959995587",
        "body": "Test message"
    }

    with patch("tools.twillo_tool.interrupt") as mock_interrupt, \
         patch("tools.twillo_tool.client.messages.create") as mock_create:

        mock_interrupt.return_value = {"status": "approved", "text_msg": args["body"]}
        mock_create.return_value.sid = "fake_sid"
        mock_create.return_value.status = "sent"

        result = send_whatsapp_message.invoke(args)

        assert result.status == "success"
        assert result.message_sid == "fake_sid"
