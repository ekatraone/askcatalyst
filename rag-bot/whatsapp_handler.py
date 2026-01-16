"""
WhatsApp Cloud API Integration Handler for Ask Catalyst RAG Bot
Direct integration with Meta's WhatsApp Business Platform
"""
import os
import logging
import requests
import hmac
import hashlib
from typing import Dict, Optional
from datetime import datetime
from assistant_manager import assistant_manager
from database import db
from retry import retry_whatsapp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppHandler:
    """Handles WhatsApp messaging via Meta's Cloud API"""

    def __init__(self):
        """Initialize WhatsApp handler with Cloud API credentials"""
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
        self.verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', 'askcatalyst_verify_token')
        self.app_secret = os.getenv('WHATSAPP_APP_SECRET')
        self.api_version = os.getenv('WHATSAPP_API_VERSION', 'v18.0')

        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        # CRITICAL: Enforce app secret for production security
        if not self.app_secret:
            logger.error("WHATSAPP_APP_SECRET not configured - signature verification disabled!")
            logger.error("This is a SECURITY RISK. Set WHATSAPP_APP_SECRET immediately.")
            # In production, raise an error instead:
            # raise ValueError("WHATSAPP_APP_SECRET is required for webhook security")

        if not self.access_token or not self.phone_number_id:
            logger.warning("WhatsApp Cloud API not configured, features disabled")
            logger.warning("Required: WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID")

    def is_enabled(self) -> bool:
        """Check if WhatsApp integration is properly configured"""
        return self.access_token is not None and self.phone_number_id is not None

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature for security
        CRITICAL: Signature verification is mandatory for production

        Args:
            payload: Request body bytes
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid
        """
        if not self.app_secret:
            logger.error("Cannot verify signature - WHATSAPP_APP_SECRET not set")
            return False  # CHANGED: Fail closed instead of True

        try:
            expected_signature = hmac.new(
                self.app_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Signature format: sha256=<hash>
            if signature.startswith('sha256='):
                signature = signature[7:]

            is_valid = hmac.compare_digest(expected_signature, signature)

            if not is_valid:
                logger.warning(f"Invalid webhook signature received")

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify WhatsApp webhook during setup

        Args:
            mode: Verification mode (should be 'subscribe')
            token: Verification token
            challenge: Challenge string to return

        Returns:
            Challenge string if verification succeeds, None otherwise
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("WhatsApp webhook verified successfully")
            return challenge
        else:
            logger.warning(f"WhatsApp webhook verification failed: mode={mode}, token_match={token == self.verify_token}")
            return None

    @retry_whatsapp
    def send_text_message(self, phone_number: str, message: str) -> bool:
        """
        Send a text message via WhatsApp Cloud API

        Args:
            phone_number: Recipient's phone number (with country code, no +)
            message: Message text

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.error("WhatsApp integration not configured")
            return False

        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': phone_number,
                'type': 'text',
                'text': {
                    'preview_url': False,
                    'body': message
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f"Message sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False

    @retry_whatsapp
    def send_template_message(self, phone_number: str, template_name: str,
                            language_code: str = 'en', components: list = None) -> bool:
        """
        Send a template message via WhatsApp Cloud API

        Args:
            phone_number: Recipient's phone number
            template_name: Name of the approved template
            language_code: Template language code (default: 'en')
            components: Template components (header, body, buttons)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.error("WhatsApp integration not configured")
            return False

        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {
                        'code': language_code
                    }
                }
            }

            if components:
                payload['template']['components'] = components

            response = requests.post(url, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f"Template message sent to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send template: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending template message: {e}")
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read

        Args:
            message_id: WhatsApp message ID

        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False

        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'messaging_product': 'whatsapp',
                'status': 'read',
                'message_id': message_id
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False

    def send_reaction(self, phone_number: str, message_id: str, emoji: str) -> bool:
        """
        Send a reaction to a message

        Args:
            phone_number: Recipient's phone number
            message_id: Message ID to react to
            emoji: Emoji to react with

        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False

        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': phone_number,
                'type': 'reaction',
                'reaction': {
                    'message_id': message_id,
                    'emoji': emoji
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error sending reaction: {e}")
            return False

    def process_webhook(self, webhook_data: Dict) -> Dict:
        """
        Process incoming WhatsApp webhook

        Args:
            webhook_data: Webhook payload from Meta

        Returns:
            Dict with processing result
        """
        try:
            # Validate webhook structure
            if 'entry' not in webhook_data:
                return {'success': False, 'error': 'Invalid webhook structure'}

            for entry in webhook_data['entry']:
                if 'changes' not in entry:
                    continue

                for change in entry['changes']:
                    if change.get('field') != 'messages':
                        continue

                    value = change.get('value', {})

                    # Process status updates
                    if 'statuses' in value:
                        self._handle_status_update(value['statuses'])

                    # Process incoming messages
                    if 'messages' in value:
                        for message in value['messages']:
                            result = self._process_message(message, value.get('metadata', {}), value.get('contacts', []))

                            # Mark as read
                            if result.get('success'):
                                self.mark_as_read(message.get('id'))

            return {'success': True, 'message': 'Webhook processed'}

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {'success': False, 'error': str(e)}

    def _process_message(self, message: Dict, metadata: Dict, contacts: list) -> Dict:
        """
        Process a single incoming message

        Args:
            message: Message object
            metadata: Metadata about the business phone
            contacts: Contact information

        Returns:
            Processing result
        """
        try:
            phone_number = message.get('from')
            message_id = message.get('id')
            timestamp = message.get('timestamp')
            message_type = message.get('type')

            # Get contact name
            contact_name = None
            for contact in contacts:
                if contact.get('wa_id') == phone_number:
                    contact_name = contact.get('profile', {}).get('name')
                    break

            logger.info(f"Processing {message_type} message from {contact_name or phone_number}")

            # Send typing indicator (reaction)
            self.send_reaction(phone_number, message_id, '👀')

            # Handle different message types
            if message_type == 'text':
                text = message.get('text', {}).get('body', '')
                return self._handle_text_message(phone_number, text, message_id, contact_name)

            elif message_type == 'interactive':
                return self._handle_interactive_message(phone_number, message, contact_name)

            elif message_type in ['image', 'document', 'audio', 'video', 'sticker']:
                return self._handle_media_message(phone_number, message, message_type, contact_name)

            elif message_type == 'button':
                button_payload = message.get('button', {}).get('payload', '')
                button_text = message.get('button', {}).get('text', '')
                return self._handle_text_message(phone_number, button_text or button_payload, message_id, contact_name)

            else:
                logger.warning(f"Unsupported message type: {message_type}")
                self.send_text_message(phone_number, "Sorry, I don't support this message type yet.")
                return {'success': False, 'error': f'Unsupported type: {message_type}'}

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {'success': False, 'error': str(e)}

    def _handle_text_message(self, phone_number: str, message_text: str,
                           message_id: str, contact_name: str = None) -> Dict:
        """
        Handle incoming text message with RAG

        Args:
            phone_number: Sender's phone number
            message_text: Message content
            message_id: WhatsApp message ID
            contact_name: Sender's name

        Returns:
            Processing result
        """
        try:
            # Check if assistant is available
            if not assistant_manager.is_enabled():
                error_msg = "🤖 I'm currently unavailable. Please try again later."
                self.send_text_message(phone_number, error_msg)
                return {'success': False, 'error': 'Assistant not configured'}

            # Update user profile
            if db.is_enabled():
                db.create_or_update_user(phone_number, {
                    'name': contact_name,
                    'phone_number': phone_number,
                    'platform': 'whatsapp',
                    'last_message': message_text
                })

            # Get or create thread for this user
            user_profile = db.get_user_profile(phone_number) if db.is_enabled() else None
            thread_id = user_profile.get('thread_id') if user_profile else None

            # Process message through RAG
            start_time = datetime.utcnow()
            result = assistant_manager.process_user_message(
                user_id=phone_number,
                message=message_text,
                thread_id=thread_id
            )

            if not result['success']:
                error_msg = "❌ Sorry, I encountered an error processing your message. Please try again."
                self.send_text_message(phone_number, error_msg)
                return result

            # Save thread ID for future messages
            if db.is_enabled() and result.get('thread_id'):
                db.create_or_update_user(phone_number, {
                    'thread_id': result['thread_id']
                })

            # Format response with citations
            response_text = result.get('response', '')
            citations = result.get('citations', [])

            if citations:
                response_text += "\n\n📚 _Sources: Information from knowledge base_"

            # Send response
            success = self.send_text_message(phone_number, response_text)

            # Send success reaction
            if success:
                self.send_reaction(phone_number, message_id, '✅')

            # Log conversation
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            if db.is_enabled():
                db.log_conversation(phone_number, {
                    'message': message_text,
                    'response': response_text,
                    'thread_id': result.get('thread_id'),
                    'citations': citations,
                    'processing_time': processing_time,
                    'platform': 'whatsapp',
                    'contact_name': contact_name,
                    'message_type': 'text',
                    'message_id': message_id
                })

                db.log_analytics_event('whatsapp_message', {
                    'user_id': phone_number,
                    'processing_time': processing_time,
                    'has_citations': len(citations) > 0,
                    'message_length': len(message_text),
                    'response_length': len(response_text)
                })

            return {
                'success': success,
                'response': response_text,
                'processing_time': processing_time
            }

        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            error_msg = "⚠️ Sorry, something went wrong. Please try again."
            self.send_text_message(phone_number, error_msg)
            return {'success': False, 'error': str(e)}

    def _handle_interactive_message(self, phone_number: str, message: Dict,
                                   contact_name: str = None) -> Dict:
        """Handle button or list reply"""
        interactive = message.get('interactive', {})
        interactive_type = interactive.get('type')

        if interactive_type == 'button_reply':
            button_id = interactive.get('button_reply', {}).get('id', '')
            button_title = interactive.get('button_reply', {}).get('title', '')
            text = button_title or button_id

        elif interactive_type == 'list_reply':
            list_id = interactive.get('list_reply', {}).get('id', '')
            list_title = interactive.get('list_reply', {}).get('title', '')
            text = list_title or list_id

        else:
            text = "Interactive message received"

        return self._handle_text_message(phone_number, text, message.get('id'), contact_name)

    def _handle_media_message(self, phone_number: str, message: Dict,
                             media_type: str, contact_name: str = None) -> Dict:
        """Handle media messages"""
        try:
            ack_msg = f"📎 I've received your {media_type}. Media processing is coming soon!"
            self.send_text_message(phone_number, ack_msg)

            # Log media receipt
            if db.is_enabled():
                db.log_analytics_event('whatsapp_media', {
                    'user_id': phone_number,
                    'contact_name': contact_name,
                    'media_type': media_type
                })

            return {'success': True, 'message': f'{media_type} received'}

        except Exception as e:
            logger.error(f"Error handling media: {e}")
            return {'success': False, 'error': str(e)}

    def _handle_status_update(self, statuses: list):
        """Handle message status updates (sent, delivered, read)"""
        for status in statuses:
            message_id = status.get('id')
            status_type = status.get('status')
            logger.debug(f"Message {message_id} status: {status_type}")

    def send_welcome_message(self, phone_number: str, name: str = None) -> bool:
        """
        Send welcome message to new user

        Args:
            phone_number: User's phone number
            name: User's name (optional)

        Returns:
            True if successful
        """
        greeting = f"Hello *{name}*!" if name else "Hello!"
        welcome_text = f"""{greeting} 👋

Welcome to *Ask Catalyst*! I'm your AI-powered assistant.

I can help you find information from our knowledge base. Just ask me anything!

*Examples:*
• What are your business hours?
• Tell me about your products
• How do I contact support?

How can I assist you today?"""

        return self.send_text_message(phone_number, welcome_text)


# Global instance
whatsapp_handler = WhatsAppHandler()
