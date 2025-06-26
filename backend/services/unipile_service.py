# backend/services/unipile_service.py

import httpx
import os
import datetime
from typing import Dict, List, Optional, Any
import asyncio


class UnipileService:
    def __init__(self):
        self.api_key = os.getenv("UNIPILE_API_KEY")
        self.base_url = os.getenv("UNIPILE_BASE_URL")
        # Extract DSN without /api/v1 for api_url parameter
        self.dsn_base = self.base_url.replace("/api/v1", "") if self.base_url else None

        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "accept": "application/json"
        }

        # Debug info
        print(f"🔧 Unipile Service Config:")
        print(f"   API Key: {'✅ Set' if self.api_key else '❌ Missing'}")
        print(f"   Base URL: {self.base_url}")
        print(f"   DSN Base: {self.dsn_base}")

    async def create_hosted_auth_link(self, providers: List[str], user_id: str) -> str:
        """Create Unipile hosted auth link for providers - matches working script"""

        print(f"\n🚀 Creating hosted auth:")
        print(f"   Providers: {providers}")
        print(f"   User ID: {user_id}")

        # Validate configuration
        if not self.api_key or not self.base_url or not self.dsn_base:
            print("❌ Missing Unipile configuration")
            return f"{os.getenv('FRONTEND_URL')}/auth/success?mock=true&provider={providers[0].lower()}"

        try:
            # Format expiry date exactly like working script (ISO 8601 UTC with .000Z)
            expires_on = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

            # Payload matching your working script exactly
            payload = {
                "type": "create",
                "providers": providers,  # ["GOOGLE"] or ["LINKEDIN"]
                "api_url": self.dsn_base,  # https://api14.unipile.com:14422 (without /api/v1)
                "expiresOn": expires_on
            }

            print(f"📤 Request Details:")
            print(f"   URL: {self.base_url}/hosted/accounts/link")
            print(f"   Payload: {payload}")

            # Make request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/hosted/accounts/link",
                    headers=self.headers,
                    json=payload
                )

                print(f"📥 Response:")
                print(f"   Status: {response.status_code}")
                print(f"   Body: {response.text}")

                response.raise_for_status()
                data = response.json()

                auth_url = data.get("url")
                if auth_url:
                    print(f"✅ Success! Real Unipile URL: {auth_url}")
                    return auth_url
                else:
                    print(f"❌ No URL in response: {data}")
                    return f"{os.getenv('FRONTEND_URL')}/auth/success?mock=true&provider={providers[0].lower()}"

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
            return f"{os.getenv('FRONTEND_URL')}/auth/success?mock=true&provider={providers[0].lower()}"
        except Exception as e:
            print(f"❌ Exception: {type(e).__name__}: {e}")
            return f"{os.getenv('FRONTEND_URL')}/auth/success?mock=true&provider={providers[0].lower()}"

    async def create_hosted_auth_link_with_callbacks(self, providers: List[str], user_id: str) -> str:
        """Create hosted auth link WITH callback URLs for production use"""

        if not self.api_key or not self.base_url or not self.dsn_base:
            print("❌ Missing Unipile configuration")
            return f"{os.getenv('FRONTEND_URL')}/auth/success?mock=true&provider={providers[0].lower()}"

        try:
            expires_on = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

            # 🔧 FIX: Include provider in success URL
            provider_name = "gmail" if providers[0] == "GOOGLE" else "linkedin"
            success_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/auth/success?provider={provider_name}"
            failure_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/auth/error?provider={provider_name}"

            backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
            webhook_url = f"{backend_url}/api/webhooks/unipile"

            print(f"🔗 Using success URL: {success_url}")
            print(f"🔗 Using webhook URL: {webhook_url}")

            # Extended payload with callback URLs
            payload = {
                "type": "create",
                "providers": providers,
                "api_url": self.dsn_base,
                "expiresOn": expires_on,
                "success_redirect_url": success_url,
                "failure_redirect_url": failure_url,
                "notify_url": webhook_url,
                "name": user_id
            }

            print(f"🚀 Creating hosted auth with callbacks for {providers}")
            print(f"   Success URL: {success_url}")
            print(f"   Payload: {payload}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/hosted/accounts/link",
                    headers=self.headers,
                    json=payload
                )

                print(f"📥 Unipile Response: {response.status_code} - {response.text}")

                response.raise_for_status()
                data = response.json()
                auth_url = data.get("url")

                if auth_url:
                    print(f"✅ Success with callbacks! URL: {auth_url}")
                    return auth_url
                else:
                    # Fallback to basic version without callbacks
                    print("⚠️ Callbacks failed, trying basic version...")
                    return await self.create_hosted_auth_link(providers, user_id)

        except Exception as e:
            print(f"❌ Callbacks failed: {e}")
            # Fallback to basic version without callbacks
            return await self.create_hosted_auth_link(providers, user_id)

    async def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """Get account information from Unipile"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/accounts/{account_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting account info: {e}")
            # Return mock account info for development
            return {
                "id": account_id,
                "provider": "GOOGLE" if "google" in account_id.lower() else "LINKEDIN",
                "email": "user@gmail.com" if "google" in account_id.lower() else None,
                "name": "Test User",
                "status": "OK"
            }

    async def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all connected accounts"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/accounts",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                return data.get("items", [])  # Unipile returns {"object":"AccountList","items":[],"cursor":null}
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []

    async def fetch_all_messages(self, account_id: str, callback=None) -> List[Dict[str, Any]]:
        """Fetch all messages from an account with pagination"""
        all_messages = []
        cursor = None

        try:
            while True:
                print(f"📧 Fetching messages batch (cursor: {cursor})")

                batch = await self.fetch_messages_batch(account_id, cursor=cursor)
                messages = batch.get("items", [])  # Unipile uses "items" array

                if not messages:
                    break

                all_messages.extend(messages)

                # Call progress callback if provided
                if callback:
                    await callback(len(all_messages), batch.get("total_count", len(all_messages)))

                # Check if there are more messages
                cursor = batch.get("cursor")  # Next page cursor
                if not cursor:
                    break

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.2)

            print(f"📧 Total messages fetched: {len(all_messages)}")
            return all_messages

        except Exception as e:
            print(f"❌ Error fetching all messages: {e}")
            return []

    async def fetch_messages_batch(self, account_id: str, limit: int = 50, cursor: Optional[str] = None) -> Dict[
        str, Any]:
        """Fetch a batch of messages"""
        try:
            print(f"Accounts {await self.get_all_accounts()}")
            params = {"limit": limit}
            if cursor:
                params["cursor"] = cursor

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.base_url}/accounts/{account_id}/messages",
                    headers=self.headers,
                    params=params
                )

                print(f"📥 Unipile messages API response: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"📧 Batch: {len(data.get('items', []))} messages")
                    return data
                else:
                    print(f"❌ API Error: {response.status_code} - {response.text}")
                    return {"items": []}

        except Exception as e:
            print(f"❌ Error fetching message batch: {e}")
            return {"items": []}

    def parse_unipile_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Unipile message format to our standard format"""
        try:
            # Extract sender info
            sender_info = raw_message.get("from", {})
            sender_email = ""
            sender_name = ""

            if isinstance(sender_info, list) and sender_info:
                sender_email = sender_info[0].get("address", "")
                sender_name = sender_info[0].get("name", "")
            elif isinstance(sender_info, dict):
                sender_email = sender_info.get("address", "")
                sender_name = sender_info.get("name", "")

            # Extract recipient info
            recipient_info = raw_message.get("to", [])
            recipient_email = ""
            if recipient_info and isinstance(recipient_info, list):
                recipient_email = recipient_info[0].get("address", "")

            # Extract content
            content = raw_message.get("text_body", "")
            if not content:
                content = raw_message.get("html_body", "")
            if not content:
                content = raw_message.get("body", "")

            # Extract timestamp
            timestamp = raw_message.get("date", raw_message.get("timestamp", datetime.now().isoformat()))

            # Convert to our standard format
            parsed_message = {
                "id": raw_message.get("id", ""),
                "channel": "email",
                "sender": sender_email,
                "sender_name": sender_name,
                "recipient": recipient_email,
                "subject": raw_message.get("subject", ""),
                "content": content,
                "timestamp": timestamp,
                "thread_id": raw_message.get("thread_id", raw_message.get("conversation_id")),
                "raw_data": raw_message  # Keep original for debugging
            }

            return parsed_message

        except Exception as e:
            print(f"❌ Error parsing message: {e}")
            return {
                "channel": "email",
                "sender": "unknown@email.com",
                "content": "Error parsing message",
                "timestamp": datetime.now().isoformat()
            }


# Initialize service instance
unipile_service = UnipileService()