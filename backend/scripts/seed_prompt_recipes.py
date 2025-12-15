"""
Seed script for default prompt recipes.

Run this once to populate the database with the 6 specialized analysis prompts.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from db_session import engine
from domains.data_explorer.db_models import PromptRecipe
from domains.data_explorer.analysis_prompts import AnalysisPromptTemplates


def seed_prompt_recipes():
    """Seed the database with default prompt recipes."""
    
    # Get all analysis types and their prompts
    analysis_types = AnalysisPromptTemplates.ANALYSIS_TYPES
    
    default_recipes = []
    
    for action_type, metadata in analysis_types.items():
        system_message = AnalysisPromptTemplates.get_system_message(action_type)
        user_template = AnalysisPromptTemplates.get_user_template(action_type)
        
        recipe_data = {
            "name": f"{metadata['name']} - Default v1",
            "action_type": action_type,
            "default_provider": "openai",
            "default_model": "gpt-4o",
            "system_message": system_message,
            "user_template": user_template,
            "recipe_metadata": {
                "version": "1.0",
                "description": metadata['description'],
                "icon": metadata['icon'],
                "is_default": True,
                "created_by": "system"
            }
        }
        
        default_recipes.append(recipe_data)
    
    # Insert recipes into database
    with Session(engine) as session:
        for recipe_data in default_recipes:
            # Check if recipe already exists
            existing = session.exec(
                select(PromptRecipe).where(
                    PromptRecipe.name == recipe_data["name"],
                    PromptRecipe.action_type == recipe_data["action_type"]
                )
            ).first()
            
            if existing:
                print(f"✓ Recipe already exists: {recipe_data['name']}")
                continue
            
            # Create new recipe
            recipe = PromptRecipe(**recipe_data)
            session.add(recipe)
            print(f"+ Created recipe: {recipe_data['name']}")
        
        session.commit()
        print(f"\n✅ Seeded {len(default_recipes)} prompt recipes successfully!")


if __name__ == "__main__":
    print("🌱 Seeding default prompt recipes...\n")
    try:
        seed_prompt_recipes()
    except Exception as e:
        print(f"❌ Error seeding recipes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

