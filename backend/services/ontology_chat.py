"""
Ontology-aware chat service that detects ontology intents and generates responses.
Returns structured responses that the frontend can render as interactive UI.
"""
import re
from typing import Dict, Any, List, Optional


class OntologyIntent:
    """Detected ontology intent with extracted parameters."""
    def __init__(self, intent_type: str, params: Dict[str, Any], confidence: float = 1.0):
        self.intent_type = intent_type
        self.params = params
        self.confidence = confidence


class OntologyChatService:
    """Conversational interface for ontology management."""
    
    def __init__(self):
        self.conversation_state = {}  # Stores state per session
    
    def detect_ontology_intent(self, query: str, session_id: str = "default") -> Optional[OntologyIntent]:
        """
        Detect if the query is related to ontology management.
        Returns OntologyIntent if detected, None otherwise.
        """
        query_lower = query.lower().strip()
        
        # CREATE ONTOLOGY intents
        if any(word in query_lower for word in ["create ontology", "new ontology", "make an ontology", 
                                                  "build ontology", "build an ontology", "build a",
                                                  "want to build", "let's build", "start ontology",
                                                  "ontology for", "retail ontology", "create a"]):
            # Extract name from query
            name = self._extract_ontology_name(query)
            return OntologyIntent("create_ontology", {
                "name": name,
                "description": None,
                "needs_confirmation": True
            })
        
        # ADD TERMS intents
        if any(word in query_lower for word in ["add term", "add terms", "create term", "new term"]):
            return OntologyIntent("add_terms", {
                "use_ai": False,
                "prompt": None,
                "needs_confirmation": True
            })
        
        # SUGGEST TERMS with AI
        if any(word in query_lower for word in ["suggest terms", "propose terms", "generate terms", "ai terms"]):
            prompt = self._extract_suggestion_prompt(query)
            return OntologyIntent("suggest_terms", {
                "prompt": prompt or query,
                "count": 20,
                "needs_ai_call": True,
                "needs_confirmation": True
            })
        
        # ADD RELATIONS
        if any(word in query_lower for word in ["add relation", "add relations", "create relation", "link terms"]):
            return OntologyIntent("add_relations", {
                "needs_confirmation": True
            })
        
        # SHOW/VIEW ONTOLOGY
        if any(word in query_lower for word in ["show ontology", "view ontology", "display ontology", "what's in", "list terms"]):
            return OntologyIntent("view_ontology", {
                "view_type": "force_graph",  # default to graph
                "needs_confirmation": False
            })
        
        # PUBLISH VERSION
        if any(word in query_lower for word in ["publish", "save version", "create version", "version"]):
            version_msg = self._extract_version_message(query)
            return OntologyIntent("publish_version", {
                "message": version_msg,
                "needs_confirmation": True
            })
        
        # SWITCH ONTOLOGY
        if any(word in query_lower for word in ["switch to", "use ontology", "change ontology", "select ontology"]):
            return OntologyIntent("switch_ontology", {
                "needs_selection": True
            })
        
        # DIFF / CHANGES
        if any(word in query_lower for word in ["show changes", "what changed", "diff", "differences"]):
            return OntologyIntent("show_diff", {
                "needs_confirmation": False
            })
        
        return None
    
    def generate_response(self, intent: OntologyIntent, session_id: str = "default") -> Dict[str, Any]:
        """
        Generate a structured response that the frontend can render.
        
        Response format:
        {
            "type": "confirmation|selection|visualization|success",
            "message": "Human-readable message",
            "action": {...},  # Action to execute if confirmed
            "ui_elements": [...],  # UI components to render
            "metadata": {...}  # Additional context
        }
        """
        
        if intent.intent_type == "create_ontology":
            name = intent.params.get("name")
            if not name:
                # No name detected, ask for one
                return {
                    "type": "input_required",
                    "message": "📝 I'll help you create an ontology! What would you like to name it?\n\nFor example: \"Retail Support\", \"Customer Service\", \"Product Taxonomy\"",
                    "ui_elements": []
                }
            
            return {
                "type": "confirmation",
                "message": f"📝 I'll create an ontology called **{name}**. Is this correct?",
                "action": {
                    "type": "create_ontology",
                    "params": {
                        "org_id": "demo",
                        "name": name,
                        "description": intent.params.get("description")
                    }
                },
                "ui_elements": [
                    {"type": "button", "label": "Yes, Create", "action": "confirm"},
                    {"type": "button", "label": "Customize Name", "action": "edit_name"},
                    {"type": "button", "label": "Cancel", "action": "cancel"}
                ]
            }
        
        elif intent.intent_type == "suggest_terms":
            return {
                "type": "confirmation",
                "message": f"💡 I'll use AI to suggest terms for: **{intent.params['prompt']}**\n\nThis will generate {intent.params['count']} relevant terms. Continue?",
                "action": {
                    "type": "suggest_terms",
                    "params": {
                        "prompt": intent.params["prompt"],
                        "count": intent.params["count"]
                    }
                },
                "ui_elements": [
                    {"type": "button", "label": "Yes, Suggest Terms", "action": "confirm"},
                    {"type": "button", "label": "Change Count", "action": "edit_count"},
                    {"type": "button", "label": "Cancel", "action": "cancel"}
                ]
            }
        
        elif intent.intent_type == "add_terms":
            return {
                "type": "input_required",
                "message": "📝 I can help you add terms in two ways:\n\n1. **Manual Entry**: You provide the terms\n2. **AI Suggestion**: I suggest terms based on a topic\n\nWhich would you prefer?",
                "ui_elements": [
                    {"type": "button", "label": "Manual Entry", "action": "manual_terms"},
                    {"type": "button", "label": "AI Suggestion", "action": "ai_suggest"},
                    {"type": "button", "label": "Cancel", "action": "cancel"}
                ]
            }
        
        elif intent.intent_type == "view_ontology":
            # Need to check if ontology is selected
            current_ontology = self.conversation_state.get(session_id, {}).get("current_ontology")
            
            if not current_ontology:
                return {
                    "type": "selection",
                    "message": "📋 Which ontology would you like to view?",
                    "action": {
                        "type": "view_ontology",
                        "params": {}
                    },
                    "ui_elements": [
                        {"type": "dropdown", "id": "ontology_selector", "label": "Select Ontology", "source": "ontologies"}
                    ]
                }
            
            return {
                "type": "visualization",
                "message": f"📊 Viewing **{current_ontology.get('name')}**",
                "action": {
                    "type": "view_ontology",
                    "params": {
                        "ontology_id": current_ontology.get("id")
                    }
                },
                "ui_elements": [
                    {"type": "toggle", "options": ["Force Graph", "JSON View"], "default": "Force Graph"},
                    {"type": "ontology_viewer", "ontology_id": current_ontology.get("id")}
                ]
            }
        
        elif intent.intent_type == "publish_version":
            current_ontology = self.conversation_state.get(session_id, {}).get("current_ontology")
            
            if not current_ontology:
                return {
                    "type": "error",
                    "message": "❌ No ontology selected. Please select an ontology first.",
                    "ui_elements": []
                }
            
            return {
                "type": "confirmation",
                "message": f"📦 Ready to publish a new version of **{current_ontology.get('name')}**?\n\nThis will create an immutable snapshot with a unique digest.",
                "action": {
                    "type": "publish_version",
                    "params": {
                        "ontology_id": current_ontology.get("id"),
                        "change_summary": intent.params.get("message", "New version")
                    }
                },
                "ui_elements": [
                    {"type": "button", "label": "Yes, Publish", "action": "confirm"},
                    {"type": "button", "label": "Show Changes First", "action": "show_diff"},
                    {"type": "button", "label": "Cancel", "action": "cancel"}
                ]
            }
        
        elif intent.intent_type == "switch_ontology":
            return {
                "type": "selection",
                "message": "🔄 Which ontology would you like to work with?",
                "action": {
                    "type": "switch_ontology",
                    "params": {}
                },
                "ui_elements": [
                    {"type": "dropdown", "id": "ontology_selector", "label": "Select Ontology", "source": "ontologies"}
                ]
            }
        
        elif intent.intent_type == "show_diff":
            current_ontology = self.conversation_state.get(session_id, {}).get("current_ontology")
            
            if not current_ontology:
                return {
                    "type": "error",
                    "message": "❌ No ontology selected. Please select an ontology first.",
                    "ui_elements": []
                }
            
            return {
                "type": "visualization",
                "message": f"📊 Changes in **{current_ontology.get('name')}** (working vs published):",
                "action": {
                    "type": "show_diff",
                    "params": {
                        "ontology_id": current_ontology.get("id")
                    }
                },
                "ui_elements": [
                    {"type": "diff_viewer", "ontology_id": current_ontology.get("id")}
                ]
            }
        
        return {
            "type": "unknown",
            "message": "🤔 I'm not sure how to help with that. Try asking about creating, viewing, or managing ontologies.",
            "ui_elements": []
        }
    
    def _extract_ontology_name(self, query: str) -> str:
        """Extract ontology name from query."""
        query_lower = query.lower().strip()
        
        # Skip generic "want to create" phrases - no specific name mentioned
        if "want to" in query_lower or "help me" in query_lower:
            return None
        
        # Look for specific patterns with ontology names
        patterns = [
            r"(?:create|build|make)\s+(?:a\s+|an\s+)?([a-z]+(?:\s+[a-z]+)?)\s+ontology",  # "create retail support ontology"
            r"([a-z]+(?:\s+[a-z]+)?)\s+ontology",  # "retail ontology" 
            r"ontology\s+(?:called|named|for)\s+['\"]?([a-z\s]+)['\"]?",  # "ontology for retail"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                name = match.group(1).strip()
                # Filter out common filler words
                words = name.split()
                words = [w for w in words if w not in ["a", "an", "the", "new", "my", "our", "with", "ontology"]]
                if words and words[0] not in ["create", "build", "make"]:
                    return " ".join(w.title() for w in words)
        
        # If no match, return None to signal we should ask for a name
        return None
    
    def _extract_suggestion_prompt(self, query: str) -> Optional[str]:
        """Extract the topic/prompt for AI suggestions."""
        # Look for "for X" or "about X"
        patterns = [
            r"(?:for|about|on|regarding)\s+(.+)",
            r"suggest terms\s+(.+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_version_message(self, query: str) -> str:
        """Extract version message from query."""
        # Look for "as X" or "with message X"
        patterns = [
            r"as ['\"]?([^'\"]+)['\"]?",
            r"message ['\"]?([^'\"]+)['\"]?",
            r"called ['\"]?([^'\"]+)['\"]?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return match.group(1).strip()
        
        return "New version"
    
    def set_current_ontology(self, session_id: str, ontology_data: Dict[str, Any]):
        """Set the current working ontology for a session."""
        if session_id not in self.conversation_state:
            self.conversation_state[session_id] = {}
        self.conversation_state[session_id]["current_ontology"] = ontology_data
    
    def get_current_ontology(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current working ontology for a session."""
        return self.conversation_state.get(session_id, {}).get("current_ontology")

