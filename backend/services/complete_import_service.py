import asyncio
from typing import List, Dict, Any
from datetime import datetime
from services.supabase_service import supabase_service
from services.unipile_service import unipile_service


class CompleteImportService:
    def __init__(self):
        self.db = supabase_service

    async def import_all_messages(self, account_id: str, provider: str) -> str:
        print(f"✨ Starting COMPLETE import for {provider} account: {account_id}")
        try:
            import_id = self.db.create_import_status(account_id)
            await self._import_messages(import_id, account_id, provider)
            return import_id
        except Exception as e:
            print(f"❌ Complete import failed: {e}")
            raise e

    async def _import_messages(self, import_id: str, account_id: str, provider: str):
        try:
            self.db.update_import_status(import_id, "fetching")

            if provider.upper() == "GOOGLE":
                messages = await self._get_gmail_messages(account_id)
            elif provider.upper() == "LINKEDIN":
                messages = await self._get_linkedin_messages(account_id)
            else:
                raise Exception(f"Unsupported provider: {provider}")

            print(f"📊 Got {len(messages)} messages from {provider}")

            if not messages:
                self.db.update_import_status(import_id, "completed", total=0, processed=0)
                print("⚠️ No messages found")
                return

            await self._store_all_messages(import_id, messages, account_id)

        except Exception as e:
            print(f"❌ Import failed: {e}")
            self.db.update_import_status(import_id, "failed")
            raise e

    async def _get_gmail_messages(self, account_id: str) -> List[Dict[str, Any]]:
        """Get ALL Gmail messages from Unipile"""
        print(f"📧 Fetching ALL Gmail messages for {account_id}")

        try:
            # Check if account exists first
            try:
                account_info = await unipile_service.get_account_info(account_id)
                print(f"✅ Gmail account found: {account_info.get('name', 'Unknown')}")
            except Exception as e:
                print(f"❌ Gmail account {account_id} not found in Unipile: {e}")
                return []

            # Fetch Gmail emails using emails endpoint
            emails = await self._fetch_gmail_emails(account_id)

            if not emails:
                print("❌ No Gmail emails found")
                return []

            print(f"📧 Processing {len(emails)} Gmail emails")

            # Parse each email
            parsed_messages = []
            for raw_email in emails:
                try:
                    # Extract Gmail email data
                    sender = self._extract_email_sender(raw_email)
                    recipient = self._extract_email_recipient(raw_email)

                    if not sender or "@" not in sender:
                        continue

                    message = {
                        "channel": "email",
                        "sender": sender,
                        "recipient": recipient,
                        "subject": raw_email.get("subject", ""),
                        "content": self._extract_email_content(raw_email),
                        "timestamp": self._extract_timestamp(raw_email),
                        "external_id": raw_email.get("id", ""),
                        "thread_id": raw_email.get("thread_id", "")
                    }

                    parsed_messages.append(message)

                except Exception as e:
                    print(f"❌ Error parsing Gmail email: {e}")
                    continue

            print(f"✅ Parsed {len(parsed_messages)} Gmail messages")
            return parsed_messages

        except Exception as e:
            print(f"❌ Gmail fetch error: {e}")
            return []

    async def _fetch_gmail_emails(self, account_id: str) -> List[Dict[str, Any]]:
        """Fetch emails using the emails endpoint"""
        try:
            import httpx

            headers = {
                "X-API-KEY": unipile_service.api_key,
                "Content-Type": "application/json",
                "accept": "application/json"
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{unipile_service.base_url}/emails",
                    headers=headers,
                    params={"account_id": account_id, "limit": 100}
                )

                print(f"📥 Gmail emails API response: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    return data.get("items", [])
                else:
                    print(f"❌ Gmail emails API error: {response.text}")
                    return []

        except Exception as e:
            print(f"❌ Error fetching Gmail emails: {e}")
            return []


    async def _get_linkedin_messages(self, account_id: str) -> List[Dict[str, Any]]:
        print(f"💼 Fetching ALL LinkedIn messages for {account_id}")
        try:
            all_messages = await self._fetch_linkedin_chats_and_messages(account_id)
            if not all_messages:
                print("❌ No LinkedIn messages found")
                return []

            print(f"💼 Processing {len(all_messages)} LinkedIn messages")
            parsed_messages = []
            print(f"Type of all_messages: {type(all_messages)}")
            print(f"🔍 Preview: {str(all_messages)[:500]}")

            for raw_msg in all_messages:
                print('yessssssssss')
                try:
                    print(f"   📬 Parsing LinkedIn message: {raw_msg.get('id', 'Unknown ID')}")
                    sender = self._extract_linkedin_sender(raw_msg)
                    print(f"   📬 Processing message from: {sender}")
                    content = self._extract_linkedin_content(raw_msg)

                    if not content.strip():
                        print(f"⚠️ Skipping message with no content")
                        continue

                    message = {
                        "channel": "linkedin",
                        "sender": sender,
                        "recipient": "You" if sender != "You" else "LinkedIn Contact",
                        "subject": raw_msg.get("subject", ""),
                        "content": content.strip(),
                        "timestamp": self._extract_timestamp(raw_msg),
                        "external_id": raw_msg.get("id", ""),
                        "thread_id": raw_msg.get("chat_id", "")
                    }

                    parsed_messages.append(message)
                    print(f"   ✅ Parsed: {sender} -> {content[:50]}...")

                except Exception as e:
                    print(f"❌ Error parsing LinkedIn message: {e}")
                    continue

            print(f"✅ Successfully parsed {len(parsed_messages)} LinkedIn messages")
            return parsed_messages

        except Exception as e:
            print(f"❌ LinkedIn fetch error: {e}")
            return []

    async def _fetch_linkedin_chats_and_messages(self, account_id: str) -> List[Dict[str, Any]]:
        import httpx
        headers = {
            "X-API-KEY": unipile_service.api_key,
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        all_messages = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            cursor = None
            all_chats = []

            while True:
                params = {"account_id": account_id, "limit": 20}
                if cursor:
                    params["cursor"] = cursor

                response = await client.get(f"{unipile_service.base_url}/chats", headers=headers, params=params)
                if response.status_code != 200:
                    print(f"❌ Chats API error: {response.text}")
                    break

                data = response.json()
                chats = data.get("items", [])
                cursor = data.get("cursor")

                if not chats:
                    break

                all_chats.extend(chats)
                if len(all_chats) >= 20 or not cursor:
                    break

                await asyncio.sleep(0.1)

            print(f"💬 Found {len(all_chats)} chats")

            for i, chat in enumerate(all_chats):
                chat_id = chat.get("id")
                if not chat_id:
                    continue
                try:
                    res = await client.get(f"{unipile_service.base_url}/chats/{chat_id}/messages", headers=headers, params={"limit": 100})
                    if res.status_code == 200:
                        chat_msgs = res.json().get("items", [])
                        for msg in chat_msgs:
                            msg["chat_id"] = chat_id
                            msg["chat_info"] = chat
                        all_messages.extend(chat_msgs)
                        print(all_messages)
                        # input('All messages fetched, press Enter to continue...')
                        print(f"   ✅ Got {len(chat_msgs)} messages from chat {i+1}/{len(all_chats)}")
                    else:
                        print(f"   ❌ Failed to get messages: {res.status_code}")
                except Exception as e:
                    print(f"❌ Chat {chat_id} error: {e}")
                    continue

        return all_messages

    def _extract_linkedin_sender(self, raw_msg: Dict[str, Any]) -> str:
        is_sender = raw_msg.get("is_sender", 0)
        if is_sender == 1:
            return "You"

        chat_info = raw_msg.get("chat_info", {})
        attendees = chat_info.get("attendees", [])
        sender_id = raw_msg.get("sender_id", "")

        for attendee in attendees:
            if attendee.get("id") != sender_id:
                return attendee.get("name", attendee.get("displayName", "LinkedIn Contact")).strip()

        return "LinkedIn Contact"

    def _extract_linkedin_sender(self, raw_msg: Dict[str, Any]) -> str:
        is_sender = raw_msg.get("is_sender", 0)
        sender_id = raw_msg.get("sender_id", "")

        if is_sender == 1:
            return "You"

        # Search for matching attendee
        attendees = raw_msg.get("chat_info", {}).get("attendees", [])
        for attendee in attendees:
            if attendee.get("id") == sender_id:
                name = attendee.get("name") or attendee.get("displayName")
                if name and name.strip():
                    return name.strip()
                else:
                    return f"LinkedIn Contact ({sender_id[-6:]})"  # Short fallback

        return f"LinkedIn Contact ({sender_id[-6:]})"

    def _extract_linkedin_content(self, raw_msg: Dict[str, Any]) -> str:
        for field in ["text", "subject", "body", "content", "message", "summary"]:
            value = raw_msg.get(field)
            if value and isinstance(value, str) and value.strip():
                return value.strip()
        if raw_msg.get("attachments"):
            return "[Attachment]"
        return ""

    def _extract_timestamp(self, raw_msg: Dict[str, Any]) -> str:
        timestamp = raw_msg.get("timestamp") or raw_msg.get("date") or raw_msg.get("createdAt")
        return timestamp or datetime.now().isoformat()

    def _extract_name_from_email(self, email: str) -> str:
        if "@" in email:
            name_part = email.split("@")[0]
            return name_part.replace(".", " ").replace("_", " ").title()
        return email

    def _extract_timestamp(self, raw_msg: Dict[str, Any]) -> str:
        """Extract message timestamp - works for both email and LinkedIn"""
        timestamp = raw_msg.get("timestamp", raw_msg.get("date", raw_msg.get("createdAt")))
        if not timestamp:
            timestamp = datetime.now().isoformat()
        return timestamp


    def _extract_email_sender(self, raw_msg: Dict[str, Any]) -> str:
        """Extract sender email from new Gmail format"""
        return raw_msg.get("from_attendee", {}).get("identifier", "")

    def _extract_email_recipient(self, raw_msg: Dict[str, Any]) -> str:
        """Extract recipient email from new Gmail format"""
        recipients = raw_msg.get("to_attendees", [])
        if recipients and isinstance(recipients, list):
            return recipients[0].get("identifier", "")
        return ""

    def _extract_email_content(self, raw_msg: Dict[str, Any]) -> str:
        """Extract email content from new Gmail format"""
        content = raw_msg.get("body_plain", "") or raw_msg.get("body", "")
        return content[:1000]

    async def _store_all_messages(self, import_id: str, messages: List[Dict[str, Any]], account_id: str):
        total = len(messages)
        self.db.update_import_status(import_id, "processing", total=total)
        stored = 0
        skipped = 0
        people = set()

        for i, msg in enumerate(messages):
            try:
                sender = msg["sender"].strip()
                content = msg["content"].strip()
                # if not content:
                #     print(f"⚠️ Skipping message with empty content from {sender}")
                #     skipped += 1
                #     continue

                if msg["channel"] == "email" and "@" in sender:
                    pid = self.db.find_or_create_person(email=sender, name=self._extract_name_from_email(sender))
                else:
                    pid = self.db.find_or_create_person(email=None, name=sender)

                self.db.store_message(msg, pid, account_id)
                people.add(pid)
                stored += 1

                if stored % 10 == 0:
                    self.db.update_import_status(import_id, "processing", processed=stored)

            except Exception as e:
                print(f"❌ Error storing message {i}: {e}")
                skipped += 1
                continue

        self.db.update_import_status(import_id, "completed", processed=stored)
        print(f"✅ IMPORT COMPLETE: {stored} stored, {skipped} skipped, {len(people)} people")


# Global instance
complete_import_service = CompleteImportService()