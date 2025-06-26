from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

router = APIRouter()


class UnipileWebhook(BaseModel):
    account_id: str
    status: str
    provider: str
    user_id: Optional[str] = None  # This is the 'name' we sent in the auth request
    email: Optional[str] = None
    name: Optional[str] = None


@router.post("/unipile")
async def handle_unipile_webhook(request: Request):
    """Handle webhook notifications from Unipile"""
    try:
        # Get raw request body
        body = await request.body()
        data = json.loads(body) if body else {}

        print(f"📥 Unipile webhook received: {data}")

        # Extract account information
        account_id = data.get("account_id")
        status = data.get("status", "OK")
        user_id = data.get("name", "default_user")  # Internal user ID we sent

        if not account_id:
            raise HTTPException(status_code=400, detail="Missing account_id in webhook")

        # If account connected successfully, fetch details and store
        if status == "OK":
            from services.unipile_service import unipile_service
            from routes.auth import store_connected_account  # Import the storage function

            # Get full account information from Unipile
            account_info = await unipile_service.get_account_info(account_id)

            # Store the connected account - THIS IS WHERE ACCOUNTS GET SAVED
            await store_connected_account(account_info, user_id)

            return {
                "success": True,
                "message": f"✅ Account {account_id} connected and stored!",
                "account_id": account_id
            }
        else:
            print(f"⚠️ Account {account_id} status: {status}")
            return {
                "success": True,
                "message": f"Account status updated: {status}"
            }

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=400, detail=f"Webhook processing failed: {str(e)}")


@router.get("/test")
async def test_webhook():
    """Test endpoint to verify webhook setup"""
    return {
        "message": "Webhook endpoint is working",
        "url": "/api/webhooks/unipile"
    }