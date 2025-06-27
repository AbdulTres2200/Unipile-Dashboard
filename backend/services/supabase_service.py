import os
from supabase import create_client, Client
from typing import List, Dict, Any, Optional
from datetime import datetime
from rapidfuzz import fuzz, process

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


    # def find_or_create_person(self, email: str = None, name: str = None) -> str:
    #     """Find existing person or create new one - handles both email and LinkedIn"""
    #     try:
    #         # For email contacts
    #         if email and "@" in email:
    #             # Try to find existing person by email
    #             result = self.supabase.table("people").select("id").eq("email", email).execute()
    #
    #             if result.data:
    #                 person_id = result.data[0]["id"]
    #                 print(f"👤 Found existing person: {email}")
    #                 return person_id
    #
    #             # Create new person with email
    #             if not name:
    #                 name = email.split('@')[0].replace('.', ' ').title()
    #
    #             result = self.supabase.table("people").insert({
    #                 "name": name,
    #                 "email": email
    #             }).execute()
    #
    #             person_id = result.data[0]["id"]
    #             print(f"👤 Created new email person: {name} ({email})")
    #             return person_id
    #
    #         # For LinkedIn contacts (no email)
    #         elif name:
    #             # Try to find existing person by name
    #             result = self.supabase.table("people").select("id").eq("name", name).eq("email", None).execute()
    #
    #             if result.data:
    #                 person_id = result.data[0]["id"]
    #                 print(f"👤 Found existing LinkedIn person: {name}")
    #                 return person_id
    #
    #             # Create new LinkedIn person (no email)
    #             result = self.supabase.table("people").insert({
    #                 "name": name,
    #                 "email": None
    #             }).execute()
    #
    #             person_id = result.data[0]["id"]
    #             print(f"👤 Created new LinkedIn person: {name}")
    #             return person_id
    #
    #         else:
    #             raise Exception("Must provide either email or name")
    #
    #     except Exception as e:
    #         print(f"❌ Error with person: {e}")
    #         raise e

    # Add these methods to your existing supabase_service.py class

    def find_or_create_person(self, email: str = None, name: str = None) -> str:
        """Find existing person or create new one, handling merged_person_id"""
        try:
            # 1. Try to find by email
            if email and "@" in email:
                result = self.supabase.table("people").select("id", "merged_person_id").eq("email", email).execute()

                if result.data:
                    person = result.data[0]
                    merged_id = person["merged_person_id"] or person["id"]
                    print(f"👤 Found person by email: {email} → merged_id: {merged_id}")
                    return merged_id

            # 2. Try to find by name if email didn't match
            if name:
                result = self.supabase.table("people").select("id", "merged_person_id").eq("name", name).execute()

                if result.data:
                    known_person = result.data[0]
                    known_id = known_person["merged_person_id"] or known_person["id"]

                    # Create new person linked to known merged_person_id
                    insert_result = self.supabase.table("people").insert({
                        "name": name,
                        "email": email,
                        "merged_person_id": known_id
                    }).execute()

                    print(f"👤 Linked new person to existing name match: {name} → merged_id: {known_id}")
                    return known_id

            # 3. No match — create a new person and self-link merged_person_id
            if not name and email:
                name = email.split('@')[0].replace('.', ' ').title()

            new_result = self.supabase.table("people").insert({
                "name": name,
                "email": email
            }).execute()

            new_id = new_result.data[0]["id"]

            # Set their own merged_person_id
            self.supabase.table("people").update({
                "merged_person_id": new_id
            }).eq("id", new_id).execute()

            print(f"👤 Created new standalone person: {name or email} → merged_id: {new_id}")
            return new_id

        except Exception as e:
            print(f"❌ Error in find_or_create_person: {e}")
            raise e

    # def get_all_people_with_stats(self):
    #     """Get all people with message counts and latest message info"""
    #     try:
    #         # Get all people first
    #         people_result = self.supabase.table('people').select('*').execute()
    #         people = []
    #
    #         for person in people_result.data or []:
    #             # Get message stats for this person
    #             messages_result = self.supabase.table('messages') \
    #                 .select('id, channel, timestamp') \
    #                 .eq('person_id', person['id']) \
    #                 .execute()
    #
    #             messages = messages_result.data or []
    #
    #             # Calculate stats
    #             message_count = len(messages)
    #             channels = list(set([m['channel'] for m in messages])) if messages else []
    #             last_message_date = max([m['timestamp'] for m in messages]) if messages else None
    #
    #             person_data = {
    #                 'id': person['id'],
    #                 'name': person['name'],
    #                 'email': person.get('email'),
    #                 'message_count': message_count,
    #                 'last_message_date': last_message_date,
    #                 'channels': channels
    #             }
    #             people.append(person_data)
    #
    #         # Sort by last message date (most recent first)
    #         people.sort(key=lambda x: x['last_message_date'] or '', reverse=True)
    #
    #         print(f"✅ Retrieved {len(people)} people with stats")
    #         return people
    #
    #     except Exception as e:
    #         print(f"❌ Error getting people with stats: {e}")
    #         return []
    # Replace your existing get_all_people_with_stats method in supabase_service.py with this:

    def get_all_people_with_stats(self):
        """Get all people grouped by name (with fuzzy matching) with message counts"""
        try:
            # Get all people first
            people_result = self.supabase.table('people').select('*').execute()

            # Group people by similar names using fuzzy matching
            grouped_people = {}
            name_to_group = {}  # Maps names to their group key

            for person in people_result.data or []:
                name = person['name'].strip()
                email = person.get('email', '')

                # Extract name from email if person name is generic
                email_name = ""
                if email and "@" in email:
                    email_name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()

                # Find if this person matches any existing group
                matched_group = None

                # Check against existing groups
                for group_name in grouped_people.keys():
                    # Direct name match
                    if fuzz.ratio(name.lower(), group_name.lower()) > 85:
                        matched_group = group_name
                        break

                    # Check if name matches email-derived name
                    if email_name and fuzz.ratio(email_name.lower(), group_name.lower()) > 85:
                        matched_group = group_name
                        break

                    # Check if any email in the group matches this person's name
                    for group_email in grouped_people[group_name]['emails']:
                        if group_email:
                            group_email_name = group_email.split('@')[0].replace('.', ' ').replace('_', ' ')
                            if fuzz.ratio(name.lower(), group_email_name.lower()) > 85:
                                matched_group = group_name
                                break

                if matched_group:
                    # Add to existing group
                    grouped_people[matched_group]['person_ids'].append(person['id'])
                    if email and email not in grouped_people[matched_group]['emails']:
                        grouped_people[matched_group]['emails'].append(email)
                        # Update email if main entry doesn't have one
                        if not grouped_people[matched_group]['email']:
                            grouped_people[matched_group]['email'] = email
                else:
                    # Create new group - use the better name (not "You" or generic)
                    display_name = name
                    if name.lower() == "you" and email_name:
                        display_name = email_name

                    grouped_people[display_name] = {
                        'id': person['id'],
                        'name': display_name,
                        'email': email,
                        'person_ids': [person['id']],
                        'emails': [email] if email else [],
                        'message_count': 0,
                        'last_message_date': None,
                        'channels': set()
                    }
                    name_to_group[name] = display_name

            # Now get message stats for each grouped person
            people = []

            for group_name, person_data in grouped_people.items():
                # Get messages for ALL person IDs in this group
                messages_result = self.supabase.table('messages') \
                    .select('id, channel, timestamp') \
                    .in_('person_id', person_data['person_ids']) \
                    .execute()

                messages = messages_result.data or []

                # Calculate stats
                message_count = len(messages)
                channels = list(set([m['channel'] for m in messages])) if messages else []
                last_message_date = max([m['timestamp'] for m in messages]) if messages else None

                people.append({
                    'id': person_data['id'],
                    'name': person_data['name'],
                    'email': person_data['email'],
                    'emails': person_data['emails'],
                    'person_ids': person_data['person_ids'],
                    'message_count': message_count,
                    'last_message_date': last_message_date,
                    'channels': channels
                })

            # Sort by last message date (most recent first)
            people.sort(key=lambda x: x['last_message_date'] or '', reverse=True)

            print(f"✅ Grouped {len(people_result.data)} people into {len(people)} unique contacts")
            return people

        except Exception as e:
            print(f"❌ Error getting grouped people with stats: {e}")
            return []
    # def get_messages_by_person(self, person_id: str):
    #     """Get all messages for a specific person"""
    #     try:
    #         result = self.supabase.table('messages') \
    #             .select('*') \
    #             .eq('person_id', person_id) \
    #             .order('timestamp', desc=True) \
    #             .execute()
    #
    #         messages = result.data or []
    #         print(f"✅ Retrieved {len(messages)} messages for person {person_id}")
    #         return messages
    #
    #     except Exception as e:
    #         print(f"❌ Error getting messages for person {person_id}: {e}")
    #         return []
    def get_messages_by_person(self, person_id: str):
        """Get all messages for a person and their similar names"""
        try:
            from rapidfuzz import fuzz

            # Get the main person's info
            person_result = self.supabase.table('people') \
                .select('name, email') \
                .eq('id', person_id) \
                .execute()

            if not person_result.data:
                print(f"❌ Person {person_id} not found")
                return []

            main_person = person_result.data[0]
            main_name = main_person['name'].strip().lower()
            main_email = main_person.get('email', '')

            # Extract name from email
            email_name = ""
            if main_email and "@" in main_email:
                email_name = main_email.split('@')[0].replace('.', ' ').replace('_', ' ').lower()

            # Get all people and find similar ones
            all_people = self.supabase.table('people').select('id, name, email').execute()
            similar_person_ids = [person_id]  # Include the original person

            for person in all_people.data or []:
                if person['id'] == person_id:
                    continue

                person_name = person['name'].strip().lower()
                person_email = person.get('email', '')

                # Check name similarity
                if fuzz.ratio(main_name, person_name) > 85:
                    similar_person_ids.append(person['id'])
                    continue

                # Check if main name matches person's email
                if person_email and "@" in person_email:
                    person_email_name = person_email.split('@')[0].replace('.', ' ').replace('_', ' ').lower()
                    if fuzz.ratio(main_name, person_email_name) > 85:
                        similar_person_ids.append(person['id'])
                        continue

                # Check if person name matches main email
                if email_name and fuzz.ratio(person_name, email_name) > 85:
                    similar_person_ids.append(person['id'])
                    continue

            print(f"📧 Found {len(similar_person_ids)} related person records for {main_person['name']}")

            # Get messages for all similar person IDs
            result = self.supabase.table('messages') \
                .select('*') \
                .in_('person_id', similar_person_ids) \
                .order('timestamp', desc=True) \
                .execute()

            messages = result.data or []
            print(f"✅ Retrieved {len(messages)} messages across all related contacts")
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