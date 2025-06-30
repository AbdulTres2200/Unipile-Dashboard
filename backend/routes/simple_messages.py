from fastapi import APIRouter, HTTPException
from services.complete_import_service import complete_import_service
from services.supabase_service import supabase_service
import requests

router = APIRouter()


@router.post("/import/start/{account_id}")
async def start_import(account_id: str):
    """Start importing messages for an account"""
    try:
        # Get account info
        from routes.auth import load_accounts
        accounts = load_accounts()
        print(f"📂 Available accounts: {list(accounts.keys())}")

        if account_id not in accounts:
            raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

        account = accounts[account_id]
        provider = account["provider"]

        print(f"🚀 Starting import for {provider} account: {account_id}")

        # Call import with the correct provider
        import_id = await complete_import_service.import_all_messages(account_id, provider)

        return {
            "success": True,
            "import_id": import_id,
            "message": f"Import started for {provider} account"
        }

    except Exception as e:
        print(f"❌ Import error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/import/status/{import_id}")
async def get_import_status(import_id: str):
    """Get import status"""
    status = supabase_service.get_import_status(import_id)

    if not status:
        raise HTTPException(status_code=404, detail="Import not found")

    return status


@router.get("/people")
async def get_people():
    """Get all people"""
    try:
        people = supabase_service.get_all_people_with_stats()
        return {"people": people, "total": len(people)}
    except Exception as e:
        print(f"❌ Error getting people: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/people/{person_id}/messages")
async def get_person_messages(person_id: str):
    """Get messages for a person"""
    try:
        messages = supabase_service.get_messages_by_person(person_id)
        return {"messages": messages, "total": len(messages)}
    except Exception as e:
        print(f"❌ Error getting person messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages")
async def get_recent_messages(limit: int = 20):
    """Get recent messages"""
    try:
        messages = supabase_service.get_recent_messages(limit)
        return {"messages": messages, "total": len(messages)}
    except Exception as e:
        print(f"❌ Error getting recent messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))