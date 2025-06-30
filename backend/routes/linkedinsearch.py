from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import dotenv
from services.unipile_linkedin_service import UnipileClient
import requests

router = APIRouter()

dotenv.load_dotenv()  # Ensure .env is loaded for local dev

class PeopleSearchRequest(BaseModel):
    filters: Dict[str, str]  # Now expects string values, not lists/IDs
    max_results: Optional[int] = 40
    count: Optional[int] = 50
    include_details: Optional[bool] = False

class ParamIdResponse(BaseModel):
    id: Optional[str]
    found: bool
    message: str

@router.post("/linkedin/people-search")
def linkedin_people_search(req: PeopleSearchRequest):
    """Search for people on LinkedIn using UnipileClient classic_people_search. Accepts human-readable filter strings."""
    try:
        client = UnipileClient()
        max_results = req.max_results if req.max_results is not None else 40
        count = req.count if req.count is not None else 50
        include_details = req.include_details if req.include_details is not None else False
        filters = req.filters or {}
        search_filters = {}
        
        # Map human-readable filters to LinkedIn IDs or process them
        if "location" in filters and filters["location"]:
            locations = [loc.strip() for loc in filters["location"].split(",")]
            location_ids = []
            for loc in locations:
                loc_id = client.get_param_id("LOCATION", loc)
                if loc_id:
                    location_ids.append(loc_id)
            if location_ids:
                search_filters["location"] = location_ids
        
        if "industry" in filters and filters["industry"]:
            industries = [ind.strip() for ind in filters["industry"].split(",")]
            industry_ids = []
            for ind in industries:
                industry_id = client.get_param_id("INDUSTRY", ind)
                if industry_id:
                    industry_ids.append(industry_id)
            if industry_ids:
                search_filters["industry"] = industry_ids
        
        if "company" in filters and filters["company"]:
            companies = [comp.strip() for comp in filters["company"].split(",")]
            company_ids = []
            for comp in companies:
                company_id = client.get_param_id("COMPANY", comp)
                if company_id:
                    company_ids.append(company_id)
            if company_ids:
                search_filters["company"] = company_ids
        
        if "past_company" in filters and filters["past_company"]:
            past_companies = [comp.strip() for comp in filters["past_company"].split(",")]
            past_company_ids = []
            for comp in past_companies:
                company_id = client.get_param_id("COMPANY", comp)
                if company_id:
                    past_company_ids.append(company_id)
            if past_company_ids:
                search_filters["past_company"] = past_company_ids
        
        if "school" in filters and filters["school"]:
            schools = [school.strip() for school in filters["school"].split(",")]
            school_ids = []
            for school in schools:
                school_id = client.get_param_id("SCHOOL", school)
                if school_id:
                    school_ids.append(school_id)
            if school_ids:
                search_filters["school"] = school_ids
        
        if "service" in filters and filters["service"]:
            services = [service.strip() for service in filters["service"].split(",")]
            service_ids = []
            for service in services:
                service_id = client.get_param_id("SERVICE", service)
                if service_id:
                    service_ids.append(service_id)
            if service_ids:
                search_filters["service"] = service_ids
        
        # Direct string/array filters (no ID lookup needed)
        if "keywords" in filters and filters["keywords"]:
            search_filters["keywords"] = filters["keywords"]
        
        if "profile_language" in filters and filters["profile_language"]:
            languages = [lang.strip() for lang in filters["profile_language"].split(",")]
            search_filters["profile_language"] = languages
        
        if "network_distance" in filters and filters["network_distance"]:
            distances = [int(dist.strip()) for dist in filters["network_distance"].split(",") if dist.strip().isdigit()]
            if distances:
                search_filters["network_distance"] = distances
        
        if "connections_of" in filters and filters["connections_of"]:
            connections = [conn.strip() for conn in filters["connections_of"].split(",")]
            search_filters["connections_of"] = connections
        
        if "followers_of" in filters and filters["followers_of"]:
            followers = [foll.strip() for foll in filters["followers_of"].split(",")]
            search_filters["followers_of"] = followers
        
        if "open_to" in filters and filters["open_to"]:
            open_to_options = [opt.strip() for opt in filters["open_to"].split(",")]
            search_filters["open_to"] = open_to_options
        
        # Advanced keywords (if provided as a single field with structured format)
        if "advanced_keywords" in filters and filters["advanced_keywords"]:
            # Expecting format like "first_name:John,last_name:Doe,title:Engineer"
            advanced = {}
            pairs = filters["advanced_keywords"].split(",")
            for pair in pairs:
                if ":" in pair:
                    key, value = pair.split(":", 1)
                    advanced[key.strip()] = value.strip()
            if advanced:
                search_filters["advanced_keywords"] = advanced
        
        print(f"🔍 Final search filters: {search_filters}")
        
        results = client.classic_people_search(
            search_filters, 
            max_results=max_results, 
            count=count, 
            include_details=include_details
        )
        
        return {"success": True, "results": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LinkedIn people search failed: {str(e)}")

@router.get("/linkedin/param-id", response_model=ParamIdResponse)
def get_param_id(param_type: str, keyword: str):
    """Get a LinkedIn parameter ID (e.g., for location, industry, company) using UnipileClient."""
    try:
        client = UnipileClient()
        pid = client.get_param_id(param_type, keyword)
        if pid:
            return ParamIdResponse(id=pid, found=True, message="Parameter ID found.")
        else:
            return ParamIdResponse(id=None, found=False, message="No parameter ID found for given type/keyword.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get parameter ID: {str(e)}")

@router.get("/linkedin/test-detailed-search")
def test_detailed_search():
    """Test endpoint to see what detailed profiles look like"""
    try:
        client = UnipileClient()
        
        # Simple test search with details
        search_filters = {"keywords": "Python Developer"}
        results = client.classic_people_search(
            search_filters, 
            max_results=3, 
            count=10, 
            include_details=True
        )
        
        return {
            "success": True, 
            "results": results, 
            "count": len(results),
            "sample_keys": list(results[0].keys()) if results else []
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@router.get("/linkedin/test-profile-fixed/{identifier}")
def test_profile_fixed(identifier: str):
    """Test the fixed profile details endpoint"""
    try:
        client = UnipileClient()
        
        # Test the corrected URL
        resp = requests.get(
            f"{client.base_url}/users/{identifier}",  # Fixed URL
            headers=client.headers,
            params={"account_id": client.account_id},
            timeout=30
        )
        
        return {
            "success": True,
            "identifier": identifier,
            "url_used": resp.url,
            "status_code": resp.status_code,
            "response_size": len(resp.text),
            "profile_data": resp.json() if resp.status_code == 200 else {},
            "error_message": resp.text if resp.status_code != 200 else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile test failed: {str(e)}")

@router.get("/linkedin/test-multiple-profiles")
def test_multiple_profiles():
    """Test multiple profiles to see data variations"""
    try:
        client = UnipileClient()
        
        # Test with different profile identifiers from your search results
        test_profiles = [
            "muhammad-taha-dev1",
            "lubna-naseer-chrm", 
            "zayab-ansari-33947a121",
            "esha-ahsan-98798629a"
        ]
        
        results = {}
        
        for identifier in test_profiles:
            try:
                resp = requests.get(
                    f"{client.base_url}/users/{identifier}",
                    headers=client.headers,
                    params={"account_id": client.account_id},
                    timeout=30
                )
                
                if resp.status_code == 200:
                    profile_data = resp.json()
                    results[identifier] = {
                        "status": "success",
                        "available_fields": list(profile_data.keys()),
                        "has_work_experience": "work_experience" in profile_data and len(profile_data.get("work_experience", [])) > 0,
                        "has_education": "education" in profile_data and len(profile_data.get("education", [])) > 0,
                        "has_skills": "skills" in profile_data and len(profile_data.get("skills", [])) > 0,
                        "work_experience_count": len(profile_data.get("work_experience", [])),
                        "education_count": len(profile_data.get("education", [])),
                        "skills_count": len(profile_data.get("skills", [])),
                        "sample_data": {
                            "work_experience": profile_data.get("work_experience", [])[:1] if profile_data.get("work_experience") else [],
                            "education": profile_data.get("education", [])[:1] if profile_data.get("education") else [],
                            "skills": profile_data.get("skills", [])[:3] if profile_data.get("skills") else []
                        }
                    }
                else:
                    results[identifier] = {"status": "error", "code": resp.status_code, "message": resp.text}
                    
            except Exception as e:
                results[identifier] = {"status": "exception", "error": str(e)}
        
        return {"test_results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-profile test failed: {str(e)}")