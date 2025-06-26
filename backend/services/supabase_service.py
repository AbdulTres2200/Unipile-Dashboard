import os
from supabase import create_client, Client
from typing import List, Dict, Any, Optional
from datetime import datetime


class SupabaseService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise Exception("Missing Supabase credentials")

        self.supabase: Client = create_client(url, key)
        print("✅ Supabase client initialized")

    def get_all_people(self) -> List[Dict[str, Any]]:
        """Get all people with message counts"""
        try:
            # Get people with message counts using SQL
            result = self.supabase.rpc("get_people_with_message_counts").execute()
            return result.data
        except Exception as e:
            print(f"❌ Error getting people: {e}")
            # Fallback to simple query
            result = self.supabase.table("people").select("*").execute()
            return result.data

    # Message operations
    def store_message(self, message_data: Dict[str, Any], person_id: str, account_id: str) -> str:
        """Store a single message"""
        try:
            result = self.supabase.table("messages").insert({
                "person_id": person_id,
                "account_id": account_id,
                "channel": message_data.get("channel", "email"),
                "sender": message_data.get("sender", ""),
                "recipient": message_data.get("recipient", ""),
                "subject": message_data.get("subject", ""),
                "content": message_data.get("content", ""),
                "timestamp": message_data.get("timestamp", datetime.now().isoformat())
            }).execute()

            message_id = result.data[0]["id"]
            print(f"💬 Stored message: {message_data.get('subject', 'No subject')}")
            return message_id

        except Exception as e:
            print(f"❌ Error storing message: {e}")
            raise e

    # Import status operations
    def create_import_status(self, account_id: str) -> str:
        """Create import status record"""
        try:
            result = self.supabase.table("import_status").insert({
                "account_id": account_id,
                "status": "starting"
            }).execute()

            import_id = result.data[0]["id"]
            print(f"📊 Created import status: {import_id}")
            return import_id

        except Exception as e:
            print(f"❌ Error creating import status: {e}")
            raise e

    def update_import_status(self, import_id: str, status: str, total: int = None, processed: int = None):
        """Update import status"""
        try:
            update_data = {"status": status}

            if total is not None:
                update_data["total_messages"] = total

            if processed is not None:
                update_data["processed_messages"] = processed

            if status == "completed":
                update_data["completed_at"] = datetime.now().isoformat()

            self.supabase.table("import_status").update(update_data).eq("id", import_id).execute()
            print(f"📊 Updated import {import_id}: {status}")

        except Exception as e:
            print(f"❌ Error updating import status: {e}")

    def get_import_status(self, import_id: str) -> Optional[Dict[str, Any]]:
        """Get import status"""
        try:
            result = self.supabase.table("import_status").select("*").eq("id", import_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Error getting import status: {e}")
            return None


    def find_or_create_person(self, email: str = None, name: str = None) -> str:
        """Find existing person or create new one - handles both email and LinkedIn"""
        try:
            # For email contacts
            if email and "@" in email:
                # Try to find existing person by email
                result = self.supabase.table("people").select("id").eq("email", email).execute()

                if result.data:
                    person_id = result.data[0]["id"]
                    print(f"👤 Found existing person: {email}")
                    return person_id

                # Create new person with email
                if not name:
                    name = email.split('@')[0].replace('.', ' ').title()

                result = self.supabase.table("people").insert({
                    "name": name,
                    "email": email
                }).execute()

                person_id = result.data[0]["id"]
                print(f"👤 Created new email person: {name} ({email})")
                return person_id

            # For LinkedIn contacts (no email)
            elif name:
                # Try to find existing person by name
                result = self.supabase.table("people").select("id").eq("name", name).eq("email", None).execute()

                if result.data:
                    person_id = result.data[0]["id"]
                    print(f"👤 Found existing LinkedIn person: {name}")
                    return person_id

                # Create new LinkedIn person (no email)
                result = self.supabase.table("people").insert({
                    "name": name,
                    "email": None
                }).execute()

                person_id = result.data[0]["id"]
                print(f"👤 Created new LinkedIn person: {name}")
                return person_id

            else:
                raise Exception("Must provide either email or name")

        except Exception as e:
            print(f"❌ Error with person: {e}")
            raise e

        # Add these methods to your existing supabase_service.py

        def get_all_people_with_stats(self):
            """Get all people with message counts and latest message info"""
            try:
                # Query people with aggregated message stats
                query = """
                SELECT 
                    p.id,
                    p.name,
                    p.email,
                    COUNT(m.id) as message_count,
                    MAX(m.timestamp) as last_message_date,
                    ARRAY_AGG(DISTINCT m.channel) as channels
                FROM people p
                LEFT JOIN messages m ON p.id = m.person_id
                GROUP BY p.id, p.name, p.email
                ORDER BY last_message_date DESC NULLS LAST
                """

                result = self.supabase.rpc('get_people_with_stats').execute()

                if result.data:
                    return result.data
                else:
                    # Fallback: simple query
                    people_result = self.supabase.table('people').select('*').execute()
                    people = []

                    for person in people_result.data:
                        # Get message count for this person
                        messages_result = self.supabase.table('messages') \
                            .select('id, channel, timestamp') \
                            .eq('person_id', person['id']) \
                            .execute()

                        messages = messages_result.data or []

                        person_data = {
                            'id': person['id'],
                            'name': person['name'],
                            'email': person.get('email'),
                            'message_count': len(messages),
                            'last_message_date': max([m['timestamp'] for m in messages]) if messages else None,
                            'channels': list(set([m['channel'] for m in messages])) if messages else []
                        }
                        people.append(person_data)

                    # Sort by last message date
                    people.sort(key=lambda x: x['last_message_date'] or '', reverse=True)
                    return people

            except Exception as e:
                print(f"❌ Error getting people with stats: {e}")
                return []


    # Add these methods to your existing supabase_service.py class

    def get_all_people_with_stats(self):
        """Get all people with message counts and latest message info"""
        try:
            # Get all people first
            people_result = self.supabase.table('people').select('*').execute()
            people = []

            for person in people_result.data or []:
                # Get message stats for this person
                messages_result = self.supabase.table('messages') \
                    .select('id, channel, timestamp') \
                    .eq('person_id', person['id']) \
                    .execute()

                messages = messages_result.data or []

                # Calculate stats
                message_count = len(messages)
                channels = list(set([m['channel'] for m in messages])) if messages else []
                last_message_date = max([m['timestamp'] for m in messages]) if messages else None

                person_data = {
                    'id': person['id'],
                    'name': person['name'],
                    'email': person.get('email'),
                    'message_count': message_count,
                    'last_message_date': last_message_date,
                    'channels': channels
                }
                people.append(person_data)

            # Sort by last message date (most recent first)
            people.sort(key=lambda x: x['last_message_date'] or '', reverse=True)

            print(f"✅ Retrieved {len(people)} people with stats")
            return people

        except Exception as e:
            print(f"❌ Error getting people with stats: {e}")
            return []

    def get_messages_by_person(self, person_id: str):
        """Get all messages for a specific person"""
        try:
            result = self.supabase.table('messages') \
                .select('*') \
                .eq('person_id', person_id) \
                .order('timestamp', desc=True) \
                .execute()

            messages = result.data or []
            print(f"✅ Retrieved {len(messages)} messages for person {person_id}")
            return messages

        except Exception as e:
            print(f"❌ Error getting messages for person {person_id}: {e}")
            return []

    def get_recent_messages(self, limit: int = 50):
        """Get recent messages across all accounts"""
        try:
            result = self.supabase.table('messages') \
                .select('*, people(name, email)') \
                .order('timestamp', desc=True) \
                .limit(limit) \
                .execute()

            messages = []
            for msg in result.data or []:
                message_data = {
                    'id': msg['id'],
                    'channel': msg['channel'],
                    'sender': msg['sender'],
                    'recipient': msg['recipient'],
                    'subject': msg.get('subject'),
                    'content': msg['content'],
                    'timestamp': msg['timestamp'],
                    'thread_id': msg.get('thread_id'),
                    'person_name': msg['people']['name'] if msg.get('people') else None,
                    'person_email': msg['people']['email'] if msg.get('people') else None
                }
                messages.append(message_data)

            print(f"✅ Retrieved {len(messages)} recent messages")
            return messages

        except Exception as e:
            print(f"❌ Error getting recent messages: {e}")
            return []

    def get_message_stats(self):
        """Get overall message statistics"""
        try:
            # Get total counts
            people_result = self.supabase.table('people').select('id', count='exact').execute()
            people_count = people_result.count or 0

            messages_result = self.supabase.table('messages').select('id', count='exact').execute()
            messages_count = messages_result.count or 0

            # Get channel breakdown
            channel_stats = self.supabase.table('messages') \
                .select('channel') \
                .execute()

            channels = {}
            for msg in channel_stats.data or []:
                channel = msg['channel']
                channels[channel] = channels.get(channel, 0) + 1

            stats = {
                'total_people': people_count,
                'total_messages': messages_count,
                'channels': channels
            }

            print(f"✅ Retrieved stats: {stats}")
            return stats

        except Exception as e:
            print(f"❌ Error getting message stats: {e}")
            return {
                'total_people': 0,
                'total_messages': 0,
                'channels': {}
            }



# Global instance
supabase_service = SupabaseService()