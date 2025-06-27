# UPDATE YOUR EXISTING webhook.py file with this enhanced version

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

router = APIRouter()


class UnipileWebhook(BaseModel):
    account_id: str
    status: Optional[str] = None
    provider: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    # Add message fields
    event_type: Optional[str] = None
    message: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, Any]]] = None


# Update your webhook handler in webhooks.py

@router.post("/unipile")
async def handle_unipile_webhook(request: Request):
    """Handle webhook notifications from Unipile"""
    try:
        # Get raw request body
        body = await request.body()
        data = json.loads(body) if body else {}

        print(f"📥 Unipile webhook received: {data}")

        # Check what type of event this is
        event = data.get("event", "").lower()

        # Handle email received events
        if event == "mail_received":
            return await handle_email_webhook(data)

        # Handle messaging events
        elif event == "message_received":
            return await handle_message_webhook(data)

        # Handle account events (if any)
        elif data.get("account_id") and data.get("status"):
            # This is an account status webhook
            from services.unipile_service import unipile_service
            from routes.auth import store_connected_account

            account_id = data.get("account_id")
            account_info = await unipile_service.get_account_info(account_id)
            await store_connected_account(account_info, "default_user")

            return {
                "success": True,
                "message": f"Account {account_id} status updated"
            }

        else:
            print(f"⚠️ Unknown webhook event: {event}")
            return {
                "success": True,
                "message": f"Unknown event: {event}"
            }

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=400, detail=f"Webhook processing failed: {str(e)}")


async def handle_email_webhook(data: Dict[str, Any]):
    """Handle email received webhook"""
    from services.supabase_service import supabase_service
    from services.complete_import_service import complete_import_service

    try:
        account_id = data.get("account_id")
        email_id = data.get("email_id")

        print(f"📧 Processing email webhook for account {account_id}")

        # Extract email data
        from_attendee = data.get("from_attendee", {})
        sender_email = from_attendee.get("identifier", "")
        sender_name = from_attendee.get("display_name", "")

        to_attendees = data.get("to_attendees", [])
        recipient_email = to_attendees[0].get("identifier", "") if to_attendees else ""

        # Create message object
        message = {
            "channel": "email",
            "sender": sender_email,
            "recipient": recipient_email,
            "subject": data.get("subject", ""),
            "content": data.get("body_plain", "") or data.get("body", ""),
            "timestamp": data.get("date", datetime.now().isoformat()),
            "external_id": email_id,
            "thread_id": data.get("thread_id", "")
        }

        # Find or create person
        person_id = supabase_service.find_or_create_person(
            email=sender_email,
            name=sender_name or complete_import_service._extract_name_from_email(sender_email)
        )

        # Store message
        supabase_service.store_message(message, person_id, account_id)

        print(f"✅ Stored email from {sender_email}: {data.get('subject', 'No subject')}")

        return {
            "success": True,
            "message": "Email stored successfully",
            "email_id": email_id,
            "sender": sender_email
        }

    except Exception as e:
        print(f"❌ Error handling email webhook: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Update your handle_message_webhook function in webhooks.py:

async def handle_message_webhook(data: Dict[str, Any]):
    """Handle messaging (LinkedIn) webhook"""
    from services.supabase_service import supabase_service

    try:
        account_id = data.get("account_id")
        print(f"💬 Processing message webhook for account {account_id}")

        # LinkedIn sends data differently - message is a string, not object
        message_content = data.get("message", "")
        sender_info = data.get("sender", {})

        # Extract sender name
        if isinstance(sender_info, dict):
            sender_name = sender_info.get("attendee_name", "LinkedIn User")
        else:
            sender_name = "LinkedIn User"

        # Create message object
        message = {
            "channel": "linkedin",
            "sender": sender_name,
            "recipient": "You",
            "subject": data.get("subject", ""),
            "content": message_content,  # This is now a string
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "external_id": data.get("message_id", ""),
            "thread_id": data.get("chat_id", "")
        }

        # Find or create person
        person_id = supabase_service.find_or_create_person(
            email=None,
            name=sender_name
        )

        # Store message
        supabase_service.store_message(message, person_id, account_id)

        print(f"✅ Stored LinkedIn message from {sender_name}: {message_content[:50]}...")

        return {
            "success": True,
            "message": "LinkedIn message stored successfully",
            "sender": sender_name
        }

    except Exception as e:
        print(f"❌ Error handling message webhook: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


async def handle_new_message_simple(data: Dict[str, Any]):
    """Handle new message webhook - reuse existing parsing logic"""
    from services.complete_import_service import complete_import_service
    from services.supabase_service import supabase_service
    from routes.auth import load_accounts

    try:
        account_id = data.get("account_id")
        if not account_id:
            return {"success": False, "error": "Missing account_id"}

        # Get account info to determine provider
        accounts = load_accounts()
        account = accounts.get(account_id)
        if not account:
            print(f"⚠️ Unknown account {account_id}, skipping")
            return {"success": True, "message": "Unknown account"}

        provider = account.get("provider", "").upper()

        # Extract message(s) from webhook
        message_data = data.get("message", data.get("messages", data))
        messages = message_data if isinstance(message_data, list) else [message_data]

        stored_count = 0

        for raw_msg in messages:
            try:
                # Parse message based on provider
                if provider == "GOOGLE":
                    # Reuse existing email parsing logic
                    sender = raw_msg.get("from_attendee", {}).get("identifier", "")
                    recipient = raw_msg.get("to_attendees", [{}])[0].get("identifier", "") if raw_msg.get(
                        "to_attendees") else ""
                    content = raw_msg.get("body_plain", "") or raw_msg.get("body", "")

                    if not sender or "@" not in sender:
                        continue

                    message = {
                        "channel": "email",
                        "sender": sender,
                        "recipient": recipient,
                        "subject": raw_msg.get("subject", ""),
                        "content": content[:1000],
                        "timestamp": raw_msg.get("timestamp", datetime.now().isoformat()),
                        "external_id": raw_msg.get("id", ""),
                        "thread_id": raw_msg.get("thread_id", "")
                    }

                    # Find or create person
                    person_id = supabase_service.find_or_create_person(
                        email=sender,
                        name=complete_import_service._extract_name_from_email(sender)
                    )

                elif provider == "LINKEDIN":
                    # Reuse existing LinkedIn parsing logic
                    is_sender = raw_msg.get("is_sender", 0)
                    sender = "You" if is_sender == 1 else raw_msg.get("sender_name", "LinkedIn Contact")

                    content = ""
                    for field in ["text", "subject", "body", "content", "message"]:
                        if raw_msg.get(field):
                            content = str(raw_msg.get(field))
                            break

                    if not content:
                        continue

                    message = {
                        "channel": "linkedin",
                        "sender": sender,
                        "recipient": "You" if sender != "You" else "LinkedIn Contact",
                        "subject": raw_msg.get("subject", ""),
                        "content": content,
                        "timestamp": raw_msg.get("timestamp", datetime.now().isoformat()),
                        "external_id": raw_msg.get("id", ""),
                        "thread_id": raw_msg.get("chat_id", "")
                    }

                    # Find or create person
                    person_id = supabase_service.find_or_create_person(
                        email=None,
                        name=sender
                    )
                else:
                    print(f"⚠️ Unknown provider {provider}")
                    continue

                # Store the message
                supabase_service.store_message(message, person_id, account_id)
                stored_count += 1
                print(f"💬 Stored new {message['channel']} message from {sender}")

            except Exception as e:
                print(f"❌ Error processing message: {e}")
                continue

        return {
            "success": True,
            "message": f"Stored {stored_count} new messages",
            "account_id": account_id
        }

    except Exception as e:
        print(f"❌ Error handling new message: {e}")
        return {"success": False, "error": str(e)}


async def configure_webhooks_for_account(account_id: str):
    """Configure webhooks for an account after connection"""
    try:
        import httpx
        from services.unipile_service import unipile_service

        backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        webhook_url = f"{backend_url}/api/webhooks/unipile"

        # Simple webhook configuration
        payload = {
            "account_id": account_id,
            "url": webhook_url,
            "events": ["message.new", "email.new", "chat.new"]  # Subscribe to new message events
        }

        print(f"🔔 Configuring webhooks for {account_id}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{unipile_service.base_url}/webhooks",
                headers=unipile_service.headers,
                json=payload
            )

            if response.status_code in [200, 201]:
                print(f"✅ Webhooks configured for {account_id}")
                return True
            else:
                print(f"⚠️ Webhook config failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Error configuring webhooks: {e}")
        return False


@router.get("/test")
async def test_webhook():
    """Test endpoint to verify webhook setup"""
    return {
        "message": "Webhook endpoint is working",
        "url": "/api/webhooks/unipile"
    }


@router.get("/check-webhooks/{account_id}")
async def check_account_webhooks(account_id: str):
    """Check if webhooks are configured for an account"""
    from services.unipile_service import unipile_service
    import httpx

    try:
        # Check if webhooks exist for this account
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get webhooks for the account
            response = await client.get(
                f"{unipile_service.base_url}/accounts/{account_id}/webhooks",
                headers=unipile_service.headers
            )

            if response.status_code == 200:
                webhooks = response.json().get("items", [])

                # Also check global webhooks
                global_response = await client.get(
                    f"{unipile_service.base_url}/webhooks",
                    headers=unipile_service.headers
                )

                global_webhooks = []
                if global_response.status_code == 200:
                    all_webhooks = global_response.json().get("items", [])
                    global_webhooks = [w for w in all_webhooks if w.get("account_id") == account_id]

                return {
                    "account_id": account_id,
                    "account_webhooks": webhooks,
                    "global_webhooks": global_webhooks,
                    "webhook_configured": len(webhooks) > 0 or len(global_webhooks) > 0,
                    "webhook_count": len(webhooks) + len(global_webhooks)
                }
            else:
                return {
                    "error": f"Failed to get webhooks: {response.status_code}",
                    "details": response.text
                }

    except Exception as e:
        return {"error": str(e)}


@router.post("/configure-webhook/{account_id}")
async def configure_webhook_for_account(account_id: str):
    """Configure webhook for a specific account using Unipile's correct format"""
    from services.unipile_service import unipile_service
    import httpx
    import os

    backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
    webhook_url = f"{backend_url}/api/unipile"

    print(f"🔧 Configuring webhooks for account: {account_id}")
    print(f"   Webhook URL: {webhook_url}")

    results = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Configure EMAIL webhook
            email_webhook = {
                "request_url": webhook_url,
                "source": "email",  # Required field
                "events": ["mail_received"],  # Use Unipile's exact event names
                "account_ids": [account_id],  # Target specific account
                "format": "json",
                "enabled": True
            }

            print("📧 Creating email webhook...")
            email_response = await client.post(
                f"{unipile_service.base_url}/webhooks",
                headers=unipile_service.headers,
                json=email_webhook
            )

            results.append({
                "type": "email",
                "status": email_response.status_code,
                "success": email_response.status_code in [200, 201],
                "response": email_response.json() if email_response.status_code in [200, 201] else email_response.text
            })

            # 2. Configure MESSAGING webhook (for LinkedIn)
            messaging_webhook = {
                "request_url": webhook_url,
                "source": "messaging",  # Required field
                "events": ["message_received"],  # Use Unipile's exact event names
                "account_ids": [account_id],  # Target specific account
                "format": "json",
                "enabled": True
            }

            print("💬 Creating messaging webhook...")
            messaging_response = await client.post(
                f"{unipile_service.base_url}/webhooks",
                headers=unipile_service.headers,
                json=messaging_webhook
            )

            results.append({
                "type": "messaging",
                "status": messaging_response.status_code,
                "success": messaging_response.status_code in [200, 201],
                "response": messaging_response.json() if messaging_response.status_code in [200,
                                                                                            201] else messaging_response.text
            })

            # Check if at least one webhook was created successfully
            any_success = any(r["success"] for r in results)

            return {
                "success": any_success,
                "webhook_url": webhook_url,
                "results": results,
                "message": "Webhooks configured" if any_success else "Failed to configure webhooks"
            }

    except Exception as e:
        print(f"❌ Error configuring webhook: {e}")
        return {
            "success": False,
            "error": str(e),
            "webhook_url": webhook_url
        }


@router.post("/configure-all-webhooks")
async def configure_all_account_webhooks():
    """Configure webhooks for all accounts"""
    from routes.auth import load_accounts

    accounts = load_accounts()
    results = []

    for account_id, account_info in accounts.items():
        print(f"🔧 Configuring webhooks for {account_info.get('provider')} account: {account_id}")
        result = await configure_webhook_for_account(account_id)
        results.append({
            "account_id": account_id,
            "provider": account_info.get('provider'),
            "email": account_info.get('email'),
            "result": result
        })

    return {
        "total_accounts": len(accounts),
        "results": results
    }


@router.delete("/delete-webhook/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """Delete a specific webhook"""
    from services.unipile_service import unipile_service
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{unipile_service.base_url}/webhooks/{webhook_id}",
                headers=unipile_service.headers
            )

            return {
                "success": response.status_code in [200, 204],
                "status": response.status_code,
                "message": "Webhook deleted" if response.status_code in [200, 204] else response.text
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/clear-and-reconfigure/{account_id}")
async def clear_and_reconfigure_webhooks(account_id: str):
    """Clear all webhooks for an account and reconfigure"""
    from services.unipile_service import unipile_service
    import httpx

    try:
        # First, get all webhooks
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{unipile_service.base_url}/webhooks",
                headers=unipile_service.headers
            )

            if response.status_code == 200:
                all_webhooks = response.json().get("items", [])

                # Delete webhooks for this account
                deleted = 0
                for webhook in all_webhooks:
                    if account_id in webhook.get("account_ids", []):
                        delete_response = await client.delete(
                            f"{unipile_service.base_url}/webhooks/{webhook['id']}",
                            headers=unipile_service.headers
                        )
                        if delete_response.status_code in [200, 204]:
                            deleted += 1

                # Now reconfigure
                config_result = await configure_webhook_for_account(account_id)

                return {
                    "deleted_webhooks": deleted,
                    "configuration_result": config_result
                }
            else:
                return {"error": "Failed to get webhooks"}

    except Exception as e:
        return {"error": str(e)}