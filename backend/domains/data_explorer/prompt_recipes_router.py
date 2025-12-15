"""API router for managing prompt recipes."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel

from db_session import get_session
from .db_models import PromptRecipe


# Pydantic models for API
class PromptRecipeCreate(BaseModel):
    """Create a new prompt recipe."""
    name: str
    action_type: str
    default_provider: Optional[str] = None
    default_model: Optional[str] = None
    system_message: str
    user_template: str
    recipe_metadata: Optional[Dict[str, Any]] = None


class PromptRecipeRead(BaseModel):
    """Read response for prompt recipe."""
    id: int
    name: str
    action_type: str
    default_provider: Optional[str]
    default_model: Optional[str]
    system_message: str
    user_template: str
    recipe_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptRecipeUpdate(BaseModel):
    """Update an existing prompt recipe."""
    name: Optional[str] = None
    default_provider: Optional[str] = None
    default_model: Optional[str] = None
    system_message: Optional[str] = None
    user_template: Optional[str] = None
    recipe_metadata: Optional[Dict[str, Any]] = None


# Router
router = APIRouter(
    prefix="/api/v1/data-explorer/prompt-recipes",
    tags=["Prompt Recipes"]
)


@router.get("/", response_model=List[PromptRecipeRead])
def list_prompt_recipes(
    action_type: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """List all prompt recipes, optionally filtered by action type."""
    query = select(PromptRecipe).order_by(PromptRecipe.action_type, PromptRecipe.name)
    
    if action_type:
        query = query.where(PromptRecipe.action_type == action_type)
    
    recipes = session.exec(query).all()
    return recipes


@router.post("/", response_model=PromptRecipeRead, status_code=201)
def create_prompt_recipe(
    payload: PromptRecipeCreate,
    session: Session = Depends(get_session),
):
    """Create a new prompt recipe."""
    recipe = PromptRecipe(**payload.dict())
    session.add(recipe)
    session.commit()
    session.refresh(recipe)
    return recipe


@router.get("/{recipe_id}", response_model=PromptRecipeRead)
def get_prompt_recipe(
    recipe_id: int,
    session: Session = Depends(get_session),
):
    """Get a specific prompt recipe by ID."""
    recipe = session.get(PromptRecipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Prompt recipe not found")
    return recipe


@router.patch("/{recipe_id}", response_model=PromptRecipeRead)
def update_prompt_recipe(
    recipe_id: int,
    payload: PromptRecipeUpdate,
    session: Session = Depends(get_session),
):
    """Update an existing prompt recipe."""
    recipe = session.get(PromptRecipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Prompt recipe not found")
    
    data = payload.dict(exclude_unset=True)
    
    # Handle is_default flag - ensure only one default per action_type
    if "recipe_metadata" in data and data["recipe_metadata"]:
        new_metadata = data["recipe_metadata"]
        if new_metadata.get("is_default") is True:
            # Clear is_default on all other recipes with same action_type
            other_recipes = session.exec(
                select(PromptRecipe).where(
                    PromptRecipe.action_type == recipe.action_type,
                    PromptRecipe.id != recipe_id
                )
            ).all()
            
            for other in other_recipes:
                if other.recipe_metadata and other.recipe_metadata.get("is_default"):
                    other.recipe_metadata["is_default"] = False
                    session.add(other)
    
    for k, v in data.items():
        setattr(recipe, k, v)
    
    recipe.updated_at = datetime.utcnow()
    session.add(recipe)
    session.commit()
    session.refresh(recipe)
    return recipe


@router.post("/{recipe_id}/clone", response_model=PromptRecipeRead, status_code=201)
def clone_prompt_recipe(
    recipe_id: int,
    session: Session = Depends(get_session),
):
    """Clone an existing recipe."""
    original = session.get(PromptRecipe, recipe_id)
    if not original:
        raise HTTPException(status_code=404, detail="Prompt recipe not found")
    
    # Create clone with modified metadata
    clone_metadata = original.recipe_metadata.copy() if original.recipe_metadata else {}
    clone_metadata["is_default"] = False
    clone_metadata["source"] = "user"
    clone_metadata["cloned_from"] = recipe_id
    
    cloned = PromptRecipe(
        name=f"{original.name} (copy)",
        action_type=original.action_type,
        default_provider=original.default_provider,
        default_model=original.default_model,
        system_message=original.system_message,
        user_template=original.user_template,
        recipe_metadata=clone_metadata
    )
    
    session.add(cloned)
    session.commit()
    session.refresh(cloned)
    return cloned


@router.delete("/{recipe_id}")
def delete_prompt_recipe(
    recipe_id: int,
    force: bool = False,
    session: Session = Depends(get_session),
):
    """Delete a prompt recipe."""
    recipe = session.get(PromptRecipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Prompt recipe not found")
    
    # Optional: protect seed recipes
    if not force and recipe.recipe_metadata and recipe.recipe_metadata.get("source") == "seed":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete seed recipe without force=true flag"
        )
    
    session.delete(recipe)
    session.commit()
    return {"ok": True, "message": f"Deleted recipe {recipe_id}"}

