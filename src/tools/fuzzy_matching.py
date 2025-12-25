"""
Fuzzy matching utilities for handling ambiguous entity names.
"""
import re
from typing import List, Dict, Tuple, Optional
from fuzzywuzzy import fuzz, process
import logging

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """Handles fuzzy matching for entity names."""
    
    def __init__(self):
        """Initialize fuzzy matcher with lookup tables."""
        self.entity_cache: Dict[str, Dict[str, List[str]]] = {
            "trials": {},
            "batches": {},
            "materials": {},
            "countries": {},
            "sites": {}
        }
    
    @staticmethod
    def normalize_string(s: str) -> str:
        """
        Normalize string by removing special characters and converting to lowercase.
        
        Args:
            s: Input string
            
        Returns:
            Normalized string
        """
        # Remove special characters but keep alphanumeric
        normalized = re.sub(r'[^a-zA-Z0-9]', '', s.lower())
        return normalized
    
    def find_matches(
        self,
        query: str,
        candidates: List[str],
        threshold: int = 60
    ) -> List[Tuple[str, int]]:
        """
        Find fuzzy matches for a query string.
        
        Args:
            query: Query string to match
            candidates: List of candidate strings
            threshold: Minimum similarity score (0-100)
            
        Returns:
            List of (match, score) tuples sorted by score
        """
        if not candidates:
            return []
        
        # Get matches using fuzzywuzzy
        matches = process.extract(
            query,
            candidates,
            scorer=fuzz.token_sort_ratio,
            limit=10
        )
        
        # Filter by threshold and return
        filtered_matches = [(match, score) for match, score in matches if score >= threshold]
        return filtered_matches
    
    def resolve_entity(
        self,
        query: str,
        candidates: List[str],
        entity_type: str = "entity"
    ) -> Dict[str, Any]:
        """
        Resolve ambiguous entity name with confidence scoring.
        
        Args:
            query: User's query string
            candidates: List of possible matches from database
            entity_type: Type of entity (for logging/messaging)
            
        Returns:
            Dictionary with resolution result
        """
        # Step 1: Exact match (case-insensitive)
        for candidate in candidates:
            if query.lower() == candidate.lower():
                return {
                    "match_type": "exact",
                    "matched_value": candidate,
                    "confidence": 100,
                    "alternatives": [],
                    "action": "use_automatically"
                }
        
        # Step 2: Normalized match
        normalized_query = self.normalize_string(query)
        for candidate in candidates:
            if normalized_query == self.normalize_string(candidate):
                return {
                    "match_type": "normalized",
                    "matched_value": candidate,
                    "confidence": 95,
                    "alternatives": [],
                    "action": "use_automatically"
                }
        
        # Step 3: Fuzzy matching
        matches = self.find_matches(query, candidates)
        
        if not matches:
            return {
                "match_type": "no_match",
                "matched_value": None,
                "confidence": 0,
                "alternatives": [],
                "action": "request_clarification",
                "message": f"No matches found for {entity_type} '{query}'"
            }
        
        best_match, best_score = matches[0]
        
        # High confidence (>80): Use automatically
        if best_score > 80:
            return {
                "match_type": "fuzzy_high",
                "matched_value": best_match,
                "confidence": best_score,
                "alternatives": [m[0] for m in matches[1:4]],
                "action": "use_automatically",
                "message": f"Matched '{query}' to '{best_match}' (confidence: {best_score}%)"
            }
        
        # Medium confidence (60-80): Ask user
        elif best_score >= 60:
            return {
                "match_type": "fuzzy_medium",
                "matched_value": best_match,
                "confidence": best_score,
                "alternatives": [m[0] for m in matches[:3]],
                "action": "ask_user",
                "message": f"Did you mean '{best_match}'? Other options: {', '.join([m[0] for m in matches[1:3]])}"
            }
        
        # Low confidence (<60): Show options
        else:
            return {
                "match_type": "fuzzy_low",
                "matched_value": None,
                "confidence": best_score,
                "alternatives": [m[0] for m in matches[:5]],
                "action": "show_options",
                "message": f"Multiple possible matches for '{query}': {', '.join([m[0] for m in matches[:5]])}"
            }
    
    def build_lookup_table(
        self,
        entity_type: str,
        canonical_names: List[str],
        variations: Optional[Dict[str, List[str]]] = None
    ):
        """
        Build lookup table for entity name variations.
        
        Args:
            entity_type: Type of entity (trials, batches, etc.)
            canonical_names: List of canonical entity names
            variations: Optional dict mapping canonical names to variations
        """
        if entity_type not in self.entity_cache:
            self.entity_cache[entity_type] = {}
        
        for name in canonical_names:
            self.entity_cache[entity_type][name] = [name]
            
            if variations and name in variations:
                self.entity_cache[entity_type][name].extend(variations[name])
    
    def get_canonical_name(
        self,
        entity_type: str,
        query: str
    ) -> Optional[str]:
        """
        Get canonical name for an entity variation.
        
        Args:
            entity_type: Type of entity
            query: Query string
            
        Returns:
            Canonical name if found, None otherwise
        """
        if entity_type not in self.entity_cache:
            return None
        
        for canonical, variations in self.entity_cache[entity_type].items():
            if query in variations or query.lower() in [v.lower() for v in variations]:
                return canonical
        
        return None


# Global fuzzy matcher instance
fuzzy_matcher = FuzzyMatcher()


def resolve_trial_name(query: str, candidates: List[str]) -> Dict[str, Any]:
    """Resolve ambiguous trial name."""
    return fuzzy_matcher.resolve_entity(query, candidates, "trial")


def resolve_batch_id(query: str, candidates: List[str]) -> Dict[str, Any]:
    """Resolve ambiguous batch ID."""
    return fuzzy_matcher.resolve_entity(query, candidates, "batch")


def resolve_material_id(query: str, candidates: List[str]) -> Dict[str, Any]:
    """Resolve ambiguous material ID."""
    return fuzzy_matcher.resolve_entity(query, candidates, "material")


def resolve_country_name(query: str, candidates: List[str]) -> Dict[str, Any]:
    """Resolve ambiguous country name."""
    return fuzzy_matcher.resolve_entity(query, candidates, "country")
