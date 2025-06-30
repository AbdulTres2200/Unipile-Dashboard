import os
import requests
from urllib.parse import urljoin

class UnipileClient:
    def __init__(self):
        self.api_key = os.getenv("UNIPILE_API_KEY")
        self.base_url = os.getenv("UNIPILE_BASE_URL").rstrip('/')
        self.account_id = os.getenv("ACCOUNT_ID")
        self.headers = {
            "X-API-KEY": self.api_key,
            "accept": "application/json",
            "content-type": "application/json"
        }

    def get_param_id(self, param_type: str, keyword: str) -> str | None:
        resp = requests.get(
            f"{self.base_url}/linkedin/search/parameters",
            headers=self.headers,
            params={
                "account_id": self.account_id,
                "type": param_type,
                "keywords": keyword,
                "limit": 1
            },
            timeout=10
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if items:
            p = items[0]
            print(f"🔎 Found {param_type}={keyword} → {p['title']} (ID={p['id']})")
            return p["id"]
        return None

    def get_profile_details(self, identifier: str) -> dict:
        """Get detailed profile information using the correct Unipile API endpoint"""
        try:
            # Fix the URL - don't add /api/v1 again since base_url already has it
            resp = requests.get(
                f"{self.base_url}/users/{identifier}",  # Changed from /api/v1/users/
                headers=self.headers,
                params={"account_id": self.account_id},
                timeout=30
            )
            
            print(f"🔍 Profile API URL: {resp.url}")
            print(f"🔍 Profile API response status: {resp.status_code}")
            
            if resp.status_code == 200:
                profile_data = resp.json()
                print(f"🔍 Profile keys: {list(profile_data.keys())}")
                return profile_data
            else:
                print(f"❌ Profile API error: {resp.status_code} - {resp.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Failed to get profile details for {identifier}: {e}")
            return {}

    def classic_people_search(self, filters: dict, max_results: int = 40, count: int = 50, include_details: bool = False) -> list:
        results = []
        cursor = None

        payload = {"api": "classic", "category": "people", "count": count}
        payload.update(filters)

        while len(results) < max_results:
            if cursor:
                payload["cursor"] = cursor

            resp = requests.post(
                f"{self.base_url}/linkedin/search?account_id={self.account_id}",
                headers=self.headers,
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            
            batch = data.get("items") or data.get("elements") or []
            slice_count = min(max_results - len(results), len(batch))
            results.extend(batch[:slice_count])
            cursor = data.get("cursor")
            if not cursor:
                break

        # Fetch detailed profiles if requested
        if include_details:
            print(f"🔍 Fetching detailed profiles for {len(results)} people...")
            detailed_results = []
            
            for i, person in enumerate(results):
                print(f"🔍 Processing {i+1}/{len(results)}: {person['name']}")
                
                # Try different identifier formats
                identifiers_to_try = [
                    person.get('public_identifier'),
                    person.get('id'),
                    person.get('member_urn')
                ]
                
                profile_details = {}
                for identifier in identifiers_to_try:
                    if identifier:
                        profile_details = self.get_profile_details(identifier)
                        if profile_details:  # If we got data, break
                            break
                
                # Merge search result with detailed profile
                if profile_details:
                    merged_profile = {**profile_details, **person}
                    detailed_results.append(merged_profile)
                    print(f"✅ Got detailed profile for {person['name']}")
                else:
                    detailed_results.append(person)
                    print(f"⚠️ Using basic profile for {person['name']}")
                    
            return detailed_results
        
        return results

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    client = UnipileClient()

    # Test detailed profile fetch
    print("🧪 Testing profile details...")
    test_profile = client.get_profile_details("muhammad-taha-dev1")
    print(f"Test profile keys: {list(test_profile.keys()) if test_profile else 'No data'}")