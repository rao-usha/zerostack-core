"""
Field Mapper for Investor Data Ingestion

Auto-detects and maps source fields to target FO/LP schema fields.
"""
from typing import List, Dict, Optional, Any
import re

from .models import MappingSuggestion, TargetEntityType, FieldMapping


# ========================================
# Field Mapping Definitions
# ========================================

# Family Office field mappings
FO_FIELD_MAPPINGS: Dict[str, Dict[str, List[str]]] = {
    "family_offices": {
        "name": ["name", "office_name", "fo_name", "family_office", "family_office_name", "office"],
        "aum": ["aum", "assets_under_management", "total_aum", "assets", "aum_usd", "total_assets"],
        "aum_currency": ["aum_currency", "currency", "asset_currency"],
        "headquarters": ["headquarters", "hq", "location", "city", "hq_location", "hq_city", "office_location"],
        "family_name": ["family_name", "family", "principal_family", "founding_family"],
        "office_type": ["office_type", "type", "fo_type", "category"],
        "investment_focus": ["investment_focus", "focus", "investment_strategy", "focus_areas", "strategy"],
        "status": ["status", "state", "active_status"],
        "description": ["description", "desc", "about", "notes", "bio", "overview"],
        "founded_year": ["founded_year", "founded", "year_founded", "established", "inception_year"],
        "website": ["website", "web", "url", "site", "homepage"],
        "linkedin": ["linkedin", "linkedin_url", "linkedin_profile"],
        "investment_horizon": ["investment_horizon", "horizon", "holding_period", "time_horizon"],
        "min_investment": ["min_investment", "minimum_investment", "min_check", "minimum_check"],
        "max_investment": ["max_investment", "maximum_investment", "max_check", "maximum_check"],
    },
    "family_office_contacts": {
        "name": ["name", "contact_name", "full_name", "person_name", "contact"],
        "title": ["title", "job_title", "position", "role_title"],
        "email": ["email", "email_address", "e_mail", "contact_email"],
        "phone": ["phone", "phone_number", "telephone", "mobile", "contact_phone"],
        "role": ["role", "function", "department"],
        "is_primary": ["is_primary", "primary", "main_contact", "primary_contact"],
        "notes": ["notes", "comments", "additional_info"],
    },
    "family_office_interactions": {
        "interaction_type": ["interaction_type", "type", "meeting_type", "activity_type"],
        "interaction_date": ["interaction_date", "date", "meeting_date", "activity_date"],
        "subject": ["subject", "topic", "title", "meeting_subject"],
        "notes": ["notes", "description", "details", "meeting_notes"],
        "outcome": ["outcome", "result", "status", "action_items"],
        "follow_up_required": ["follow_up_required", "follow_up", "needs_follow_up"],
        "follow_up_date": ["follow_up_date", "next_action_date", "due_date"],
        "created_by": ["created_by", "recorded_by", "user", "author"],
    },
    "co_investments": {
        "deal_name": ["deal_name", "deal", "investment_name", "opportunity_name", "company"],
        "deal_type": ["deal_type", "type", "investment_type", "transaction_type"],
        "sector": ["sector", "industry", "vertical"],
        "investment_amount": ["investment_amount", "amount", "investment_size", "check_size"],
        "investment_currency": ["investment_currency", "currency"],
        "status": ["status", "deal_status", "state"],
        "close_date": ["close_date", "closing_date", "date", "investment_date"],
        "description": ["description", "notes", "details"],
        "lead_investor": ["lead_investor", "lead", "sponsor"],
        "co_investors": ["co_investors", "other_investors", "syndicate", "participants"],
    },
    "portfolio_companies": {
        "company_name": ["company_name", "name", "company", "portfolio_company"],
        "sector": ["sector", "industry", "vertical"],
        "location": ["location", "headquarters", "hq", "country", "city"],
        "investment_date": ["investment_date", "date", "closing_date"],
        "investment_amount": ["investment_amount", "amount", "investment_size"],
        "ownership_percentage": ["ownership_percentage", "ownership", "stake", "percentage"],
        "current_valuation": ["current_valuation", "valuation", "current_value", "fair_value"],
        "status": ["status", "state", "investment_status"],
        "description": ["description", "notes", "about"],
    },
    "investor_themes": {
        "theme_name": ["theme_name", "name", "theme", "focus_area"],
        "theme_category": ["theme_category", "category", "type"],
        "allocation_target": ["allocation_target", "target", "allocation", "target_percentage"],
        "priority": ["priority", "rank", "importance"],
        "description": ["description", "notes", "details"],
        "active": ["active", "is_active", "enabled"],
    },
    "impact_analysis": {
        "analysis_date": ["analysis_date", "date", "as_of_date", "report_date"],
        "esg_score": ["esg_score", "esg", "overall_score", "total_score"],
        "environmental_score": ["environmental_score", "environmental", "e_score", "env_score"],
        "social_score": ["social_score", "social", "s_score", "soc_score"],
        "governance_score": ["governance_score", "governance", "g_score", "gov_score"],
        "impact_focus_areas": ["impact_focus_areas", "focus_areas", "impact_areas"],
        "carbon_footprint": ["carbon_footprint", "carbon", "emissions", "co2"],
        "diversity_metrics": ["diversity_metrics", "diversity", "dei_metrics"],
        "reporting_framework": ["reporting_framework", "framework", "standard"],
        "notes": ["notes", "comments", "observations"],
    },
}

# LP field mappings
LP_FIELD_MAPPINGS: Dict[str, Dict[str, List[str]]] = {
    "lp_fund": {
        "fund_name": ["fund_name", "fund", "name", "lp_fund_name"],
        "lp_name": ["lp_name", "lp", "limited_partner", "investor_name", "investor"],
        "commitment": ["commitment", "committed_capital", "commitment_amount", "capital_commitment"],
        "commitment_currency": ["commitment_currency", "currency"],
        "vintage_year": ["vintage_year", "vintage", "year"],
        "strategy": ["strategy", "investment_strategy", "fund_strategy"],
        "fund_type": ["fund_type", "type", "vehicle_type"],
        "status": ["status", "state", "fund_status"],
        "description": ["description", "notes", "about"],
        "aum": ["aum", "assets_under_management", "total_aum"],
        "headquarters": ["headquarters", "hq", "location"],
        "website": ["website", "url", "web"],
    },
    "lp_key_contact": {
        "name": ["name", "contact_name", "full_name"],
        "title": ["title", "job_title", "position"],
        "email": ["email", "email_address"],
        "phone": ["phone", "phone_number", "telephone"],
        "role": ["role", "function"],
        "is_primary": ["is_primary", "primary"],
        "notes": ["notes", "comments"],
    },
    "lp_document": {
        "document_type": ["document_type", "type", "doc_type"],
        "document_name": ["document_name", "name", "filename", "title"],
        "document_date": ["document_date", "date", "as_of_date"],
        "source_url": ["source_url", "url", "link"],
    },
    "lp_asset_class_target_allocation": {
        "asset_class": ["asset_class", "class", "asset_type"],
        "target_allocation": ["target_allocation", "target", "allocation"],
        "current_allocation": ["current_allocation", "current", "actual_allocation"],
        "min_allocation": ["min_allocation", "minimum", "floor"],
        "max_allocation": ["max_allocation", "maximum", "ceiling"],
        "as_of_date": ["as_of_date", "date"],
    },
    "lp_manager_or_vehicle_exposure": {
        "manager_name": ["manager_name", "manager", "gp_name", "gp"],
        "vehicle_name": ["vehicle_name", "vehicle", "fund_name"],
        "exposure_amount": ["exposure_amount", "amount", "exposure"],
        "exposure_percentage": ["exposure_percentage", "percentage", "pct"],
        "asset_class": ["asset_class", "class"],
        "strategy": ["strategy"],
        "vintage_year": ["vintage_year", "vintage"],
        "as_of_date": ["as_of_date", "date"],
    },
}

# Entity type to table name mapping
ENTITY_TABLE_MAP: Dict[TargetEntityType, str] = {
    TargetEntityType.FAMILY_OFFICE: "family_offices",
    TargetEntityType.FO_CONTACT: "family_office_contacts",
    TargetEntityType.FO_INTERACTION: "family_office_interactions",
    TargetEntityType.CO_INVESTMENT: "co_investments",
    TargetEntityType.PORTFOLIO_COMPANY: "portfolio_companies",
    TargetEntityType.INVESTOR_THEME: "investor_themes",
    TargetEntityType.IMPACT_ANALYSIS: "impact_analysis",
    TargetEntityType.LP_FUND: "lp_fund",
    TargetEntityType.LP_CONTACT: "lp_key_contact",
    TargetEntityType.LP_DOCUMENT: "lp_document",
    TargetEntityType.LP_ALLOCATION: "lp_asset_class_target_allocation",
    TargetEntityType.LP_EXPOSURE: "lp_manager_or_vehicle_exposure",
}


class FieldMapper:
    """Auto-maps source fields to target schema fields."""

    @staticmethod
    def suggest_entity_type(columns: List[str]) -> Optional[TargetEntityType]:
        """
        Suggest the most likely target entity type based on column names.

        Args:
            columns: List of column names from the source file

        Returns:
            Suggested TargetEntityType or None
        """
        columns_lower = [c.lower().strip() for c in columns]

        # Score each entity type
        scores: Dict[TargetEntityType, int] = {}

        # Check FO tables
        for table_name, field_map in FO_FIELD_MAPPINGS.items():
            entity_type = _get_entity_type_for_table(table_name)
            if entity_type:
                score = FieldMapper._score_columns(columns_lower, field_map)
                scores[entity_type] = score

        # Check LP tables
        for table_name, field_map in LP_FIELD_MAPPINGS.items():
            entity_type = _get_entity_type_for_table(table_name)
            if entity_type:
                score = FieldMapper._score_columns(columns_lower, field_map)
                scores[entity_type] = score

        if not scores:
            return None

        # Return highest scoring entity type
        best_entity = max(scores, key=scores.get)
        if scores[best_entity] > 0:
            return best_entity

        return None

    @staticmethod
    def suggest_mappings(
        columns: List[str],
        target_entity: TargetEntityType
    ) -> List[MappingSuggestion]:
        """
        Suggest field mappings for the given columns and target entity.

        Args:
            columns: List of column names from source file
            target_entity: Target entity type

        Returns:
            List of mapping suggestions
        """
        suggestions = []
        table_name = ENTITY_TABLE_MAP.get(target_entity)

        if not table_name:
            return suggestions

        # Get the appropriate field mapping
        if table_name in FO_FIELD_MAPPINGS:
            field_map = FO_FIELD_MAPPINGS[table_name]
        elif table_name in LP_FIELD_MAPPINGS:
            field_map = LP_FIELD_MAPPINGS[table_name]
        else:
            return suggestions

        for col in columns:
            col_normalized = FieldMapper._normalize_name(col)

            best_match = None
            best_confidence = 0.0
            best_reasoning = None

            for target_field, aliases in field_map.items():
                # Check exact match with target field
                if col_normalized == FieldMapper._normalize_name(target_field):
                    best_match = target_field
                    best_confidence = 1.0
                    best_reasoning = "Exact match with target field name"
                    break

                # Check aliases
                for alias in aliases:
                    alias_normalized = FieldMapper._normalize_name(alias)

                    if col_normalized == alias_normalized:
                        confidence = 0.95
                        reasoning = f"Exact match with alias '{alias}'"
                    elif alias_normalized in col_normalized or col_normalized in alias_normalized:
                        confidence = 0.8
                        reasoning = f"Partial match with alias '{alias}'"
                    else:
                        # Fuzzy match
                        similarity = FieldMapper._similarity(col_normalized, alias_normalized)
                        if similarity > 0.7:
                            confidence = similarity * 0.7
                            reasoning = f"Similar to alias '{alias}'"
                        else:
                            continue

                    if confidence > best_confidence:
                        best_match = target_field
                        best_confidence = confidence
                        best_reasoning = reasoning

            if best_match and best_confidence >= 0.5:
                suggestions.append(MappingSuggestion(
                    source_field=col,
                    suggested_target=best_match,
                    confidence=round(best_confidence, 2),
                    reasoning=best_reasoning
                ))

        return suggestions

    @staticmethod
    def get_target_fields(target_entity: TargetEntityType) -> List[str]:
        """
        Get list of target fields for an entity type.

        Args:
            target_entity: Target entity type

        Returns:
            List of target field names
        """
        table_name = ENTITY_TABLE_MAP.get(target_entity)

        if not table_name:
            return []

        if table_name in FO_FIELD_MAPPINGS:
            return list(FO_FIELD_MAPPINGS[table_name].keys())
        elif table_name in LP_FIELD_MAPPINGS:
            return list(LP_FIELD_MAPPINGS[table_name].keys())

        return []

    @staticmethod
    def _score_columns(columns: List[str], field_map: Dict[str, List[str]]) -> int:
        """Score how well columns match a field mapping."""
        score = 0

        for col in columns:
            col_normalized = FieldMapper._normalize_name(col)

            for target_field, aliases in field_map.items():
                target_normalized = FieldMapper._normalize_name(target_field)

                if col_normalized == target_normalized:
                    score += 3
                    break

                for alias in aliases:
                    alias_normalized = FieldMapper._normalize_name(alias)
                    if col_normalized == alias_normalized:
                        score += 2
                        break
                    elif alias_normalized in col_normalized or col_normalized in alias_normalized:
                        score += 1
                        break

        return score

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize a field name for comparison."""
        # Convert to lowercase
        name = name.lower()
        # Replace common separators with underscore
        name = re.sub(r'[\s\-\.]', '_', name)
        # Remove non-alphanumeric characters except underscore
        name = re.sub(r'[^a-z0-9_]', '', name)
        # Collapse multiple underscores
        name = re.sub(r'_+', '_', name)
        return name.strip('_')

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """Calculate simple similarity between two strings."""
        if not a or not b:
            return 0.0

        # Use Jaccard similarity on character bigrams
        def bigrams(s):
            return set(s[i:i+2] for i in range(len(s)-1))

        bg_a = bigrams(a)
        bg_b = bigrams(b)

        if not bg_a or not bg_b:
            return 0.0

        intersection = len(bg_a & bg_b)
        union = len(bg_a | bg_b)

        return intersection / union if union > 0 else 0.0


def _get_entity_type_for_table(table_name: str) -> Optional[TargetEntityType]:
    """Get entity type for a table name."""
    for entity_type, tbl in ENTITY_TABLE_MAP.items():
        if tbl == table_name:
            return entity_type
    return None
