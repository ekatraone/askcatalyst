# WhatsApp Cloud API Integration Setup

Complete guide to integrate Ask Catalyst RAG Bot with WhatsApp using Meta's Cloud API.

## Prerequisites

- Meta Business Account
- WhatsApp Business Account
- Facebook App with WhatsApp product enabled
- Ask Catalyst RAG Bot deployed (Flask or Azure Functions)

## Step 1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **My Apps** → **Create App**
3. Select **Business** as app type
4. Fill in app details:
   - App name: "Ask Catalyst Bot"
   - Contact email: your email
   - Business Portfolio: Select or create
5. Click **Create App**

## Step 2: Add WhatsApp Product

1. In your app dashboard, find **WhatsApp** product
2. Click **Set Up** on WhatsApp
3. Complete the WhatsApp onboarding flow
4. You'll receive a test number and temporary access token

## Step 3: Get Configuration Details

### Access Token (Temporary - for testing)

1. In WhatsApp → **Getting Started** section
2. Copy the **Temporary access token**
3. ⚠️ This expires in 24 hours - create permanent token later

### Phone Number ID

1. In WhatsApp → **Getting Started**
2. Under **From**, you'll see the phone number ID
3. Format: `123456789012345`

### Business Account ID

1. Go to **WhatsApp → Settings**
2. Find **WhatsApp Business Account ID**
3. Copy this ID

### App Secret

1. Go to **Settings → Basic** in left sidebar
2. Click **Show** next to **App Secret**
3. Enter your Facebook password
4. Copy the App Secret

## Step 4: Generate Permanent Access Token

⚠️ Temporary tokens expire in 24 hours. Create a permanent token:

1. Go to **WhatsApp → Getting Started**
2. Scroll to **Permanent token** section
3. Click **Generate token** → **Generate**
4. Select permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
5. Copy and save the permanent token
6. ⚠️ Store securely - shown only once!

## Step 5: Configure Environment Variables

Update your `.env` file:

```env
# WhatsApp Cloud API Configuration
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxx  # Permanent token from Step 4
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_BUSINESS_ACCOUNT_ID=987654321098765
WHATSAPP_VERIFY_TOKEN=askcatalyst_verify_token_123  # Choose your own random string
WHATSAPP_APP_SECRET=abcdef1234567890  # From Step 3
WHATSAPP_API_VERSION=v18.0
```

## Step 6: Deploy Your Application

### Option A: Local Development (Flask)

```bash
cd rag-bot
python api.py
```

Your webhook URL: `http://your-public-url/webhook/whatsapp`

💡 **Tip**: Use [ngrok](https://ngrok.com/) for local testing:
```bash
ngrok http 5000
# Use the HTTPS URL: https://xxxx.ngrok.io/webhook/whatsapp
```

### Option B: Azure Functions (Production)

```bash
cd rag-bot
func azure functionapp publish <your-function-app-name>
```

Your webhook URL: `https://<your-app>.azurewebsites.net/api/webhook/whatsapp`

## Step 7: Configure Webhook

1. Go to **WhatsApp → Configuration** in your Facebook App
2. Click **Edit** next to **Webhook**

### Callback URL
Enter your webhook URL:
- Local (ngrok): `https://xxxx.ngrok.io/webhook/whatsapp`
- Azure Functions: `https://<your-app>.azurewebsites.net/api/webhook/whatsapp`

### Verify Token
Enter the same value as `WHATSAPP_VERIFY_TOKEN` in your `.env`

### Click "Verify and Save"

3. Subscribe to webhook fields:
   - ✅ messages
   - ✅ message_status (optional)

## Step 8: Test the Integration

### Method 1: Send Test Message

1. Go to **WhatsApp → API Setup** in your app
2. Find **Step 5: Send messages with the API**
3. Enter your phone number (with country code, no +)
4. Click **Send Message**
5. You'll receive a test message on WhatsApp
6. Reply to that message
7. Check your logs - you should see the webhook being triggered!

### Method 2: Using API

Send a message via API:

```bash
curl -X POST http://localhost:5000/api/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "1234567890",
    "message": "Hello from Ask Catalyst!"
  }'
```

### Method 3: Send Welcome Message

```bash
curl -X POST http://localhost:5000/api/whatsapp/welcome \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "1234567890",
    "name": "John"
  }'
```

## Step 9: Add Your Phone Number

1. Go to **WhatsApp → API Setup**
2. Scroll to **Step 4: Add a recipient phone number**
3. Enter your phone number
4. You'll receive a verification code via WhatsApp
5. Enter the code
6. Now you can send messages to this number!

## Step 10: Production Setup (Business Verification)

To send messages to any WhatsApp number (not just test numbers):

1. **Complete Business Verification**:
   - Go to **Business Settings**
   - Complete Meta Business verification
   - This can take several days

2. **Get Official Business Number**:
   - Purchase a WhatsApp Business number
   - Or migrate existing number
   - Configure number in WhatsApp → Phone Numbers

3. **Create Message Templates**:
   - Go to **WhatsApp → Message Templates**
   - Create and submit templates for approval
   - Required for outbound messages (first contact)

## Webhook Payload Structure

### Incoming Text Message

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "field": "messages",
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "1234567890",
          "phone_number_id": "123456789012345"
        },
        "contacts": [{
          "profile": {
            "name": "John Doe"
          },
          "wa_id": "1234567890"
        }],
        "messages": [{
          "from": "1234567890",
          "id": "wamid.xxx",
          "timestamp": "1234567890",
          "text": {
            "body": "Hello!"
          },
          "type": "text"
        }]
      }
    }]
  }]
}
```

## Features Supported

✅ **Text Messages**: Receive and respond with text
✅ **Message Reactions**: Send emojis as reactions
✅ **Read Receipts**: Mark messages as read
✅ **Thread-based Conversations**: Maintain context across messages
✅ **Citations**: Include sources from knowledge base
✅ **User Analytics**: Track interactions in Cosmos DB
✅ **Signature Verification**: Secure webhook with HMAC validation

🔄 **Coming Soon**:
- Media messages (images, documents, audio)
- Interactive messages (buttons, lists)
- Location sharing
- Contact cards

## Troubleshooting

### Webhook not receiving messages

1. **Check webhook is verified**:
   - Green checkmark next to webhook URL
   - Subscribed to `messages` field

2. **Test webhook directly**:
   ```bash
   curl -X POST https://your-url/webhook/whatsapp \
     -H "Content-Type: application/json" \
     -d '{
       "object": "whatsapp_business_account",
       "entry": [{
         "changes": [{
           "field": "messages",
           "value": {
             "messages": [{
               "from": "1234567890",
               "id": "test",
               "type": "text",
               "text": {"body": "test"}
             }],
             "contacts": [{"wa_id": "1234567890"}]
           }
         }]
       }]
     }'
   ```

3. **Check logs**:
   - Azure Functions: Application Insights
   - Local: Terminal output

### Messages not sending

1. **Check access token**:
   ```bash
   curl "https://graph.facebook.com/v18.0/me?access_token=YOUR_TOKEN"
   ```
   Should return your business account info

2. **Verify phone number is registered**:
   - Must be added in API Setup
   - Or business verified for any number

3. **Check response**:
   ```bash
   curl -X POST "https://graph.facebook.com/v18.0/PHONE_NUMBER_ID/messages" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "messaging_product": "whatsapp",
       "to": "1234567890",
       "type": "text",
       "text": {"body": "test"}
     }'
   ```

### Signature verification fails

1. Check `WHATSAPP_APP_SECRET` is correct
2. Ensure signature header is `X-Hub-Signature-256`
3. Test with signature disabled (temporarily):
   - Comment out signature verification
   - Check if messages work

### Rate Limits

Free tier limits:
- 1,000 conversations/month
- 250 messages per conversation

For production:
- Upgrade to paid tier
- Monitor usage in Business Manager

## API Endpoints

### Webhook
- **GET** `/webhook/whatsapp` - Verification
- **POST** `/webhook/whatsapp` - Receive messages

### Send Messages
- **POST** `/api/whatsapp/send` - Send text message
- **POST** `/api/whatsapp/welcome` - Send welcome message

### Health Check
- **GET** `/health` - Check WhatsApp status

## Security Best Practices

1. **Never expose tokens**:
   - Use environment variables
   - Never commit to git
   - Rotate regularly

2. **Enable signature verification**:
   - Always verify `X-Hub-Signature-256`
   - Prevents unauthorized webhook calls

3. **Use HTTPS**:
   - Required for webhooks
   - Use valid SSL certificate

4. **Rate limiting**:
   - Implement rate limiting on your endpoints
   - Prevent abuse

5. **Logging**:
   - Log all webhook calls
   - Monitor for suspicious activity

## Resources

- [WhatsApp Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Get Started Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
- [Webhook Reference](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates)
- [API Reference](https://developers.facebook.com/docs/whatsapp/cloud-api/reference)

## Support

For issues:
1. Check Facebook Developer Console logs
2. Review Ask Catalyst application logs
3. Verify all environment variables
4. Test webhook with sample payloads

## Next Steps

1. ✅ Complete this setup
2. ✅ Test with your phone number
3. ⏳ Complete business verification
4. ⏳ Get official business number
5. ⏳ Create and approve message templates
6. ⏳ Launch to production!
