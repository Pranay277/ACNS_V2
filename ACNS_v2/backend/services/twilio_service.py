import os
import logging
from twilio.rest import Client
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def _send_whatsapp_sync(supervisor_phone: str, issue_description: str, location_data: dict, photo_url: str):
    """Synchronous Twilio API call."""
    try:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        
        if not account_sid or not auth_token:
            logger.error("Twilio credentials missing. Aborting WhatsApp notification.")
            return

        client = Client(account_sid, auth_token)
        
        # Format location
        lat = location_data.get('latitude', 'Unknown')
        lon = location_data.get('longitude', 'Unknown')
        address = location_data.get('address', f"({lat}, {lon})")
        
        # Construct message body
        body = (
            f"🚨 *New Issue Assigned to You*\n\n"
            f"📝 *Description:* {issue_description}\n"
            f"📍 *Location:* {address}"
        )
        
        # Prepare arguments (Twilio requires a list for media_url)
        kwargs = {
            "from_": "whatsapp:+14155238886",
            "body": body,
            "to": supervisor_phone
        }
        if photo_url:
            kwargs["media_url"] = [photo_url]

        # Dispatch message
        message = client.messages.create(**kwargs)
        logger.info(f"WhatsApp notification sent successfully. SID: {message.sid}")
        
    except Exception as e:
        logger.error(f"Failed to send Twilio WhatsApp notification: {e}")


def notify_supervisor_whatsapp(supervisor_phone: str, issue_description: str, location_data: dict, photo_url: str):
    """
    Public function to safely dispatch Twilio notifications asynchronously.
    """
    if not supervisor_phone.startswith("whatsapp:"):
        supervisor_phone = f"whatsapp:{supervisor_phone}"
        
    # Run in a background thread to prevent blocking the main issue reporting flow
    thread = Thread(
        target=_send_whatsapp_sync,
        args=(supervisor_phone, issue_description, location_data, photo_url),
        daemon=True
    )
    thread.start()
