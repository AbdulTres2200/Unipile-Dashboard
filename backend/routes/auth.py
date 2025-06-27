# backend/routes/auth.py

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
import os
import json
import datetime
from typing import List, Dict, Any

router = APIRouter()

# File-based storage for development
STORAGE_FILE = "connected_accounts.json"


def load_accounts() -> Dict[str, Any]:
    """Load accounts from file"""
    try:
        if os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, 'r') as f:
                data = json.load(f)
                print(f"📂 Loaded {len(data)} accounts from {STORAGE_FILE}")
                return data
        print(f"📂 No existing file found, starting with empty accounts")
        return {}
    except Exception as e:
        print(f"❌ Error loading accounts: {e}")
        return {}


def save_accounts(accounts: Dict[str, Any]):
    """Save accounts to file"""
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(accounts, f, indent=2)
        print(f"✅ Saved {len(accounts)} accounts to {STORAGE_FILE}")
    except Exception as e:
        print(f"❌ Error saving accounts: {e}")


class HostedAuthRequest(BaseModel):
    provider: str  # 'gmail' or 'linkedin'
    user_id: str = "default_user"


@router.post("/hosted-auth/create")
async def create_hosted_auth(request: HostedAuthRequest):
    """Create Unipile hosted auth link for a provider"""
    try:
        from services.unipile_service import unipile_service

        # Map frontend provider names to Unipile provider names
        provider_map = {
            "gmail": "GOOGLE",
            "linkedin": "LINKEDIN"
        }

        unipile_provider = provider_map.get(request.provider.lower())
        if not unipile_provider:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")

        print(f"🎯 Creating hosted auth for {request.provider} -> {unipile_provider}")

        # Try with callbacks first, fallback to basic if needed
        try:
            auth_url = await unipile_service.create_hosted_auth_link_with_callbacks(
                providers=[unipile_provider],
                user_id=request.user_id
            )
        except Exception as e:
            print(f"⚠️ Callback version failed, using basic: {e}")
            auth_url = await unipile_service.create_hosted_auth_link(
                providers=[unipile_provider],
                user_id=request.user_id
            )

        # Check if we got a real Unipile URL or mock URL
        is_real_url = "account.unipile.com" in auth_url

        # 🎯 SIMPLE FIX: If it's a mock URL, create a quick test account instead
        if not is_real_url:
            print(f"🚀 Creating quick test account for {request.provider}")

            account_info = {
                "id": f"quick_{request.provider}_{datetime.datetime.now().strftime('%H%M%S')}",
                "provider": unipile_provider,
                "email": f"user@{request.provider.lower()}.com" if request.provider.lower() == "gmail" else None,
                "name": f"Test User ({request.provider})",
                "status": "OK"
            }

            await store_connected_account(account_info, request.user_id)

            return {
                "success": True,
                "auth_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/auth/success?provider={request.provider}&test=true",
                "provider": request.provider,
                "is_real": False,
                "message": f"✅ Test account created for {request.provider}",
                "account_created": True
            }

        return {
            "success": True,
            "auth_url": auth_url,
            "provider": request.provider,
            "is_real": is_real_url,
            "message": f"✅ Real Unipile URL created for {request.provider}" if is_real_url else f"⚠️ Mock URL (check configuration)"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create auth link: {str(e)}")


@router.get("/accounts")
async def get_connected_accounts():
    """Get all connected accounts"""
    accounts = load_accounts()
    return {
        "accounts": list(accounts.values()),
        "total": len(accounts)
    }


@router.get("/accounts/status")
async def get_connection_status():
    """Get connection status for each provider"""
    accounts = load_accounts()
    account_list = list(accounts.values())

    gmail_accounts = [acc for acc in account_list if acc["provider"].upper() == "GOOGLE"]
    linkedin_accounts = [acc for acc in account_list if acc["provider"].upper() == "LINKEDIN"]

    print(f"📊 Status check: {len(gmail_accounts)} Gmail, {len(linkedin_accounts)} LinkedIn accounts")

    return {
        "gmail": {
            "connected": len(gmail_accounts) > 0,
            "accounts": gmail_accounts
        },
        "linkedin": {
            "connected": len(linkedin_accounts) > 0,
            "accounts": linkedin_accounts
        },
        "both_connected": len(gmail_accounts) > 0 and len(linkedin_accounts) > 0,
        "total_accounts": len(account_list)
    }


@router.delete("/accounts/{account_id}")
async def disconnect_account(account_id: str):
    """Disconnect an account"""
    accounts = load_accounts()
    if account_id in accounts:
        provider = accounts[account_id]["provider"]
        del accounts[account_id]
        save_accounts(accounts)
        print(f"🗑️ Disconnected {provider} account: {account_id}")
        return {
            "success": True,
            "message": f"{provider} account disconnected"
        }
    else:
        raise HTTPException(status_code=404, detail="Account not found")


@router.get("/test-unipile")
async def test_unipile_connection():
    """Test Unipile service configuration"""
    try:
        from services.unipile_service import unipile_service

        # Test basic API access
        accounts = await unipile_service.get_all_accounts()

        return {
            "success": True,
            "message": "Unipile API accessible",
            "accounts_count": len(accounts),
            "accounts": accounts,
            "config": {
                "api_key_set": bool(unipile_service.api_key),
                "base_url": unipile_service.base_url,
                "dsn_base": unipile_service.dsn_base
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Unipile API connection failed"
        }


# Mock account creation for testing
@router.post("/mock/create-account")
async def create_mock_account(provider: str):
    """Create a mock connected account for testing"""
    mock_account = {
        "id": f"mock_{provider}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "provider": "GOOGLE" if provider.lower() == "gmail" else "LINKEDIN",
        "email": f"user@{provider.lower()}.com" if provider.lower() == "gmail" else None,
        "name": f"Test User ({provider})",
        "status": "OK"
    }

    # Use the store function to ensure consistency
    await store_connected_account(mock_account, "default_user")

    return {
        "success": True,
        "message": f"Mock {provider} account created",
        "account": mock_account
    }


@router.post("/mock/populate")
async def populate_mock_data():
    """Populate with mock data for testing"""

    # Create mock Gmail account
    gmail_account = {
        "id": "mock_gmail_123",
        "provider": "GOOGLE",
        "email": "user@gmail.com",
        "name": "Test Gmail User",
        "status": "OK"
    }

    # Create mock LinkedIn account
    linkedin_account = {
        "id": "mock_linkedin_456",
        "provider": "LINKEDIN",
        "email": None,
        "name": "Test LinkedIn User",
        "status": "OK"
    }

    # Store both accounts
    await store_connected_account(gmail_account, "default_user")
    await store_connected_account(linkedin_account, "default_user")

    return {
        "success": True,
        "message": "Mock data created",
        "accounts": [gmail_account, linkedin_account]
    }


@router.post("/manual/oauth-success")
async def manual_oauth_success(request: Request):
    """Handle manual OAuth success - fetch latest real account from Unipile"""
    body = await request.json()
    provider = body.get("provider", "gmail")

    try:
        from services.unipile_service import unipile_service

        # 🚀 SIMPLE SOLUTION: Fetch all accounts and get the latest one for this provider
        print(f"🔍 Fetching latest {provider} account from Unipile...")

        unipile_accounts = await unipile_service.get_all_accounts()
        print(f"📥 Found {len(unipile_accounts)} total accounts in Unipile")

        # 🔧 FIX: Use correct field names from Unipile API
        # Filter by type (not provider)
        if provider.lower() == "gmail":
            account_type = "GOOGLE_OAUTH"
            provider_name = "GOOGLE"
        elif provider.lower() == "linkedin":
            account_type = "LINKEDIN"
            provider_name = "LINKEDIN"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

        matching_accounts = [acc for acc in unipile_accounts if acc.get("type") == account_type]

        if matching_accounts:
            # Get the latest account (last in list, sorted by created_at)
            latest_account = matching_accounts[-1]

            # Extract email from connection_params for Google accounts
            email = None
            if account_type == "GOOGLE_OAUTH":
                email = latest_account.get("connection_params", {}).get("mail", {}).get("username")

            account_info = {
                "id": latest_account["id"],  # 🎯 REAL UNIPILE ACCOUNT ID
                "provider": provider_name,  # Normalize to GOOGLE/LINKEDIN
                "email": email or latest_account.get("name"),  # Use email from connection_params or name
                "name": latest_account.get("name", f"User ({provider})"),
                "status": "OK",  # Default to OK
                "type": latest_account.get("type"),  # Store original type
                "unipile_data": latest_account  # Store original data
            }

            print(f"✅ Using latest {provider} account: {latest_account['id']} ({latest_account.get('name')})")

        else:
            # No real accounts found - create mock for development
            print(f"⚠️ No {provider} accounts found in Unipile")
            print(f"Available account types: {list(set([acc.get('type') for acc in unipile_accounts]))}")

            account_info = {
                "id": f"mock_{provider}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "provider": provider_name,
                "email": f"user@{provider.lower()}.com" if provider.lower() == "gmail" else None,
                "name": f"Mock User ({provider})",
                "status": "OK",
                "unipile_data": None
            }

        await store_connected_account(account_info, "default_user")

        return {
            "success": True,
            "account": account_info,
            "is_real_account": "unipile_data" in account_info and account_info["unipile_data"] is not None,
            "debug": {
                "total_accounts": len(unipile_accounts),
                "matching_accounts": len(matching_accounts) if matching_accounts else 0,
                "account_types": list(set([acc.get('type') for acc in unipile_accounts]))
            }
        }

    except Exception as e:
        print(f"❌ Error fetching from Unipile: {e}")

        # Fallback to mock account if Unipile API fails
        account_info = {
            "id": f"fallback_{provider}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "provider": "GOOGLE" if provider.lower() == "gmail" else "LINKEDIN",
            "email": f"user@{provider.lower()}.com" if provider.lower() == "gmail" else None,
            "name": f"Fallback User ({provider})",
            "status": "OK",
            "unipile_data": None
        }

        await store_connected_account(account_info, "default_user")
        # await import_all_real_messages(account_info["id"], account_info["provider"])
        return {"success": True, "account": account_info, "is_real_account": False}


@router.post("/sync-accounts")
async def sync_accounts_with_unipile():
    """Sync local accounts with real Unipile accounts"""
    try:
        from services.unipile_service import unipile_service

        print("🔄 Starting account sync with Unipile...")

        # Get all accounts from Unipile
        unipile_accounts = await unipile_service.get_all_accounts()
        print(f"📥 Raw Unipile response: {len(unipile_accounts)} accounts")

        if not unipile_accounts:
            return {
                "success": False,
                "message": "No accounts found in Unipile. Make sure accounts are connected via Unipile dashboard.",
                "debug": {
                    "api_key_set": bool(unipile_service.api_key),
                    "base_url": unipile_service.base_url
                }
            }

        # Load existing local accounts
        local_accounts = load_accounts()
        print(f"📂 Current local accounts: {len(local_accounts)}")

        # Clear and rebuild with real account IDs
        new_accounts = {}

        for unipile_account in unipile_accounts:
            account_id = unipile_account["id"]
            account_type = unipile_account.get("type")

            # 🔧 FIX: Map account types correctly
            if account_type == "GOOGLE_OAUTH":
                provider = "GOOGLE"
                email = unipile_account.get("connection_params", {}).get("mail", {}).get("username")
            elif account_type == "LINKEDIN":
                provider = "LINKEDIN"
                email = None
            elif account_type == "WHATSAPP":
                provider = "WHATSAPP"
                email = None
            else:
                provider = account_type or "UNKNOWN"
                email = None

            account_info = {
                "id": account_id,  # Real Unipile ID
                "provider": provider,
                "email": email or unipile_account.get("name"),
                "name": unipile_account.get("name", "Unknown User"),
                "status": "OK",  # Default status
                "type": account_type,  # Store original type
                "user_id": "default_user",
                "connected_at": datetime.datetime.now().isoformat(),
                "unipile_data": unipile_account
            }

            new_accounts[account_id] = account_info
            print(f"✅ Synced account: {provider} - {account_id} ({unipile_account.get('name')})")

        # Save the updated accounts
        save_accounts(new_accounts)

        return {
            "success": True,
            "message": f"Synced {len(new_accounts)} accounts with real Unipile IDs",
            "accounts": list(new_accounts.values()),
            "debug": {
                "old_accounts_count": len(local_accounts),
                "new_accounts_count": len(new_accounts),
                "account_types": list(set([acc.get("type") for acc in unipile_accounts]))
            }
        }

    except Exception as e:
        print(f"❌ Error syncing accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync accounts: {str(e)}")

        unipile_accounts = await unipile_service.get_all_accounts()
        print(f"🔄 Found {len(unipile_accounts)} accounts from Unipile")

        # Load existing local accounts
        local_accounts = load_accounts()

        # Clear and rebuild with real account IDs
        new_accounts = {}

        for unipile_account in unipile_accounts:
            account_id = unipile_account["id"]

            account_info = {
                "id": account_id,  # Real Unipile ID
                "provider": unipile_account["provider"],
                "email": unipile_account.get("email"),
                "name": unipile_account.get("name", "Unknown User"),
                "status": unipile_account.get("status", "OK"),
                "user_id": "default_user",
                "connected_at": datetime.datetime.now().isoformat(),
                "unipile_data": unipile_account
            }

            new_accounts[account_id] = account_info
            print(f"✅ Synced account: {unipile_account['provider']} - {account_id}")

        # Save the updated accounts
        save_accounts(new_accounts)

        return {
            "success": True,
            "message": f"Synced {len(new_accounts)} accounts with real Unipile IDs",
            "accounts": list(new_accounts.values())
        }

    except Exception as e:
        print(f"❌ Error syncing accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync accounts: {str(e)}")


async def store_connected_account(account_data: dict, user_id: str):
    from services.complete_import_service import complete_import_service
    """Store account information after successful connection"""
    print(f"💾 Storing account: {account_data}")

    try:
        # Load existing accounts
        accounts = load_accounts()
        account_id = account_data["id"]

        # Create complete account info
        account_info = {
            "id": account_id,
            "provider": account_data["provider"],
            "email": account_data.get("email"),
            "name": account_data.get("name", "Unknown"),
            "status": account_data.get("status", "OK"),
            "user_id": user_id,
            "connected_at": datetime.datetime.now().isoformat(),
            "unipile_data": account_data.get("unipile_data")  # Store original Unipile data
        }

        # Store in memory dict
        accounts[account_id] = account_info

        # Save to file
        save_accounts(accounts)

        print(f"✅ Account stored successfully: {account_data['provider']} - {account_id}")

        # 🚀 IMPORT ALL REAL MESSAGES IMMEDIATELY
        await complete_import_service.import_all_messages(account_id, account_data["provider"])

        return account_info

    except Exception as e:
        print(f"❌ Error storing account: {e}")
        raise e


async def import_all_real_messages(account_id: str, provider: str):
    """Import ALL real messages immediately"""
    try:
        from services.complete_import_service import complete_import_service

        print(f"🚀 IMPORTING ALL REAL {provider} MESSAGES for {account_id}")

        # Import all messages now
        import_id = await complete_import_service.import_all_messages(account_id, provider)

        print(f"✅ Message import completed: {import_id}")

    except Exception as e:
        print(f"❌ Failed to import messages: {e}")


@router.post("/connect/{provider}")
async def connect_provider_account(provider: str):
    """Connect the latest account for a provider from Unipile"""
    try:
        from services.unipile_service import unipile_service

        # Validate provider
        valid_providers = ["gmail", "linkedin"]
        if provider.lower() not in valid_providers:
            raise HTTPException(status_code=400, detail=f"Invalid provider. Must be one of: {valid_providers}")

        print(f"🔗 Connecting latest {provider} account from Unipile...")

        # Get all accounts from Unipile
        unipile_accounts = await unipile_service.get_all_accounts()
        print(f"📥 Found {len(unipile_accounts)} total accounts")

        # 🔧 FIX: Use correct field names
        if provider.lower() == "gmail":
            account_type = "GOOGLE_OAUTH"
            provider_name = "GOOGLE"
        else:  # linkedin
            account_type = "LINKEDIN"
            provider_name = "LINKEDIN"

        matching_accounts = [acc for acc in unipile_accounts if acc.get("type") == account_type]

        if not matching_accounts:
            return {
                "success": False,
                "message": f"No {provider} accounts found in Unipile. Please connect one via Unipile dashboard first.",
                "debug": {
                    "total_accounts": len(unipile_accounts),
                    "available_types": list(set([acc.get("type") for acc in unipile_accounts])),
                    "looking_for_type": account_type
                }
            }

        # Use the latest account (last in the list, sorted by created_at)
        latest_account = matching_accounts[-1]

        # Extract email properly for Google accounts
        email = None
        if account_type == "GOOGLE_OAUTH":
            email = latest_account.get("connection_params", {}).get("mail", {}).get("username")

        account_info = {
            "id": latest_account["id"],  # Real Unipile ID
            "provider": provider_name,  # Normalize to GOOGLE/LINKEDIN
            "email": email or latest_account.get("name"),
            "name": latest_account.get("name", f"User ({provider})"),
            "status": "OK",
            "type": latest_account.get("type"),
            "unipile_data": latest_account
        }

        # Store the account
        await store_connected_account(account_info, "default_user")

        return {
            "success": True,
            "message": f"Connected latest {provider} account: {latest_account['id']}",
            "account": account_info,
            "debug": {
                "account_name": latest_account.get("name"),
                "created_at": latest_account.get("created_at"),
                "total_matching": len(matching_accounts)
            }
        }

    except Exception as e:
        print(f"❌ Error connecting {provider}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect {provider}: {str(e)}")


# Webhook endpoint for Unipile notifications
@router.post("/webhooks/unipile")
async def unipile_webhook(request: Request):
    """Handle Unipile webhook notifications when accounts are connected"""
    try:
        body = await request.json()
        print(f"🔔 Received Unipile webhook: {body}")

        # Handle account connection webhook
        if body.get("type") == "account.created" or body.get("object") == "Account":
            account_data = body.get("data", body)

            # Store the real account with its actual Unipile ID
            account_info = {
                "id": account_data["id"],  # Real Unipile account ID
                "provider": account_data["provider"],
                "email": account_data.get("email"),
                "name": account_data.get("name", "Unknown User"),
                "status": account_data.get("status", "OK"),
                "unipile_data": account_data
            }

            await store_connected_account(account_info, "default_user")

            print(f"✅ Webhook: Stored real account {account_data['id']}")

            return {
                "success": True,
                "message": "Account stored from webhook",
                "account_id": account_data["id"]
            }

        return {"success": True, "message": "Webhook received"}

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"success": False, "error": str(e)}


# Placeholder for message import (implement in next step)
async def start_message_import(account_id: str, provider: str):
    """Start importing messages for connected account"""
    print(f"🚀 Starting immediate import for {provider} account: {account_id}")
    # We'll implement the actual import logic in the next step
    pass