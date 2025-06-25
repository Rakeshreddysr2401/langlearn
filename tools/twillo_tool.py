from twilio.rest import Client
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv
import os
import time
from langgraph.types import interrupt

# 🔐 Load environment variables
load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

# 📞 Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# 📝 Input schema
class WhatsAppMessageArgs(BaseModel):
    to_number: str = Field(
        ...,
        description="Recipient's phone number in international or local format. E.g. 9959995587 or +919959995587"
    )
    body: str = Field(
        ...,
        description="The text message to send via WhatsApp."
    )

# 📝 Output schema
class WhatsAppMessageResult(BaseModel):
    status: str = Field(..., description="success or fail")
    message_sid: Optional[str] = Field(
        None, description="Unique Twilio message SID if successful"
    )
    error_message: Optional[str] = Field(
        None, description="Error details if failed"
    )

@tool(
    "send_whatsapp_message",
    args_schema=WhatsAppMessageArgs,
)
def send_whatsapp_message(
        to_number: str,
        body: str,
) -> WhatsAppMessageResult:
    """
    Use this to send a WhatsApp message to any of my contacts and make sure to have a contact number.
    The phone number can be with or without +91. The message will go to WhatsApp.
    Make sure the message sounds casual and natural as if I wrote it myself.
    Returns a status, message_sid, and optional error_message.
    NOTE:Don't call this tool without a valid phone number
    ⚠️ This tool requires human approval before sending messages.
    """

    # ✅ Normalize number first
    clean_num = to_number.strip().replace(" ", "").replace("whatsapp:", "")

    if clean_num.startswith("+"):
        normalized = clean_num
    elif clean_num.startswith("91") and len(clean_num) == 12:
        normalized = f"+{clean_num}"
    elif len(clean_num) == 10 and clean_num.isdigit():
        normalized = f"+91{clean_num}"
    else:
        normalized = f"+{clean_num}"

    # 🛑 REQUEST HUMAN APPROVAL BEFORE SENDING
    approval_request = {
        "type": "approve_reject",
        "action": "send_whatsapp_message",
        "number": normalized,
        "text_msg": body,
    }

    # This will pause execution and wait for human input
    human_approval = interrupt(approval_request)

    # Check if human approved the action
    print("human approval...",human_approval)
    if not human_approval or human_approval.get("status") != "approved":
        return WhatsAppMessageResult(
            status="fail",
            message_sid=None,
            error_message= human_approval.get("text_msg")
        )

    # 📨 If approved, proceed with sending
    try:
        # ✅ Send message
        msg = client.messages.create(
            from_=f"whatsapp:{TWILIO_FROM_NUMBER}",
            to=f"whatsapp:{normalized}",
            body=human_approval.get("text_msg")
        )
        print("Message is being sent... ⏳")

        time.sleep(3)
        final = client.messages(msg.sid).fetch()

        # ✅ Check status
        if final.status in ("sent", "delivered"):
            return WhatsAppMessageResult(
                status="success",
                message_sid=final.sid,
                error_message=None
            )
        else:
            return WhatsAppMessageResult(
                status="fail",
                message_sid=final.sid,
                error_message=final.error_message or final.status
            )

    except Exception as e:
        return WhatsAppMessageResult(
            status="fail",
            message_sid=None,
            error_message=str(e)
        )

# 🎯 Example standalone test
if __name__ == "__main__":
    result = send_whatsapp_message.invoke(
        {"to_number": "9959995587", "body": "Hey buddy, I'm agent Rakhi 2.0!"}
    )
    print(result)
