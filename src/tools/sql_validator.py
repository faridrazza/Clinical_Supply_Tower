"""
SQL Validator - Validates and auto-fixes SQL queries for data type issues.
"""
import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class SQLValidator:
    """Validates and fixes SQL queries for common data type issues."""
    
    # Common TEXT date column patterns
    TEXT_DATE_PATTERNS = [
        'expiration_date', 'expiry_date', 'created_date', 'modified_date',
        'delivery_date', 'order_date', 'request_date', 'ship_date',
        'manufacturing_date', 'goods_receipt_date', 'inspection_date',
        'approval_date', 'release_date', 'start_date', 'end_date',
        'actual_date', 'planned_date', 'scheduled_date', 'received_date',
        'shipped_date', 'accepted_date', 'rejected_date', 'confirmed_date',
        'issued_date', 'effective_date', 'validity_date', 'expiration_date_shelf_life',
        'date_of_manufacture', 'date_of_last_change', 'date_on_which_the_record_was_created',
        'destroy_after_date', 'first_goods_receipt_date', 'goods_receipt_date',
        'manufacturing_start_date', 'next_insp_date', 'packaging_start_date',
        'shelf_life_expiration_or_best_before_date', 'change_date', 'create_date',
        'next_inspection_date', 'inspection_start_date', 'end_date_of_the_inspection',
        'date_of_code_used_for_usage_decision', 'rqst_date', 'ip_timeline',
        'actual_delivery_date', 'requested_delivery_date', 'planned_delivery_date',
        'inbound_delivery_date', 'item_delivery_date', 'po_release_date',
        'purchase_document_date', 'scheduled_po_date', 'statistical_delivery_date',
        'posting_date', 'schedule_line_date', 'statistics_date', 'requisition_date',
        'approved_dates', 'target_date_for_results', 'lilly_receipt_date',
        'date_accepted', 'actual_ship_date', 'order_confirm_date', 'pod_activity_date',
        'released_date_depot', 'visit_date', 'availability_date_or_requirements_date',
        'start_time_of_the_order', 'period_end_date', 'period_start_date',
        'label_material_number_description_due_date', 'planned_end_date', 'actual_end_date',
        'date_from_which_the_plant_specific_material_status_is_valid', 'effective_out_date',
        'exemption_certificate_issue_date', 'maturation_time', 'shipping_processing_time',
        'shipping_setup_time', 'synchronization_time_stamp', 'takt_time', 'throughput_time',
        'validity_date_of_vendor_declaration', 'delivery_time', 'goods_rcpt_pr_time',
        'safety_time', 'total_repleishment_lead_time', 'enrollment_over_time_level',
        'date_when_excursion_was_reported', 'ud_change_date', 'ud_code_use_date',
        'qa_disposition_date', 'planned_enddate_qa_disposition_date', 'deliver_date',
        'planned_end_date', 'start_delivery_date', 'date_of_last_change',
        'time_of_creation', 'delivery_date_of_a_schedule_line', 'fac_cal_del_date',
        'goods_receipt_date', 'new_date', 'old_date', 'zdeldate'
    ]
    
    @staticmethod
    def validate_and_fix_date_casting(query: str, text_date_columns: List[str] = None) -> Tuple[str, List[str]]:
        """
        Validate SQL and auto-fix TEXT date column issues.
        
        Args:
            query: SQL query to validate
            text_date_columns: List of known TEXT date columns (optional)
            
        Returns:
            Tuple of (fixed_query, list_of_fixes_applied)
        """
        if not query:
            return query, []
        
        fixes = []
        fixed_query = query
        
        # Use provided columns or detect from query
        columns_to_check = text_date_columns or SQLValidator._detect_date_columns(query)
        
        for col in columns_to_check:
            # Fix 1: Date comparisons (col < CURRENT_DATE)
            pattern = rf'\b{re.escape(col)}\b\s*(<|>|<=|>=|=)\s*(CURRENT_DATE|CURRENT_TIMESTAMP|NOW\(\)|\'[\d\-]+\')'
            if re.search(pattern, fixed_query, re.IGNORECASE):
                replacement = rf'{col}::DATE \1 \2::DATE'
                fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
                fixes.append(f"Added ::DATE casting to comparison: {col}")
            
            # Fix 2: EXTRACT from date column
            pattern = rf'EXTRACT\s*\(\s*([A-Z]+)\s+FROM\s+{re.escape(col)}\b'
            if re.search(pattern, fixed_query, re.IGNORECASE):
                replacement = rf'EXTRACT(\1 FROM {col}::DATE'
                fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
                fixes.append(f"Added ::DATE casting to EXTRACT: {col}")
            
            # Fix 3: Date arithmetic (col - CURRENT_DATE)
            pattern = rf'\(\s*{re.escape(col)}\s*-\s*(CURRENT_DATE|CURRENT_TIMESTAMP|NOW\(\)|\'[\d\-]+\')'
            if re.search(pattern, fixed_query, re.IGNORECASE):
                replacement = rf'({col}::DATE - \1::DATE'
                fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
                fixes.append(f"Added ::DATE casting to arithmetic: {col}")
            
            # Fix 4: Date arithmetic (CURRENT_DATE - col)
            pattern = rf'\(\s*(CURRENT_DATE|CURRENT_TIMESTAMP|NOW\(\)|\'[\d\-]+\')\s*-\s*{re.escape(col)}\b'
            if re.search(pattern, fixed_query, re.IGNORECASE):
                replacement = rf'(\1::DATE - {col}::DATE'
                fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
                fixes.append(f"Added ::DATE casting to arithmetic: {col}")
            
            # Fix 5: INTERVAL arithmetic (col + INTERVAL)
            pattern = rf'{re.escape(col)}\b\s*\+\s*INTERVAL'
            if re.search(pattern, fixed_query, re.IGNORECASE):
                replacement = f'{col}::DATE + INTERVAL'
                fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
                fixes.append(f"Added ::DATE casting to INTERVAL arithmetic: {col}")
            
            # Fix 6: WHERE col BETWEEN dates
            pattern = rf'WHERE\s+{re.escape(col)}\b\s+BETWEEN'
            if re.search(pattern, fixed_query, re.IGNORECASE):
                replacement = f'WHERE {col}::DATE BETWEEN'
                fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
                fixes.append(f"Added ::DATE casting to BETWEEN: {col}")
            
            # Fix 7: ORDER BY date column
            pattern = rf'ORDER\s+BY\s+{re.escape(col)}\b'
            if re.search(pattern, fixed_query, re.IGNORECASE):
                # Only add casting if not already present
                if f'{col}::DATE' not in fixed_query:
                    replacement = f'ORDER BY {col}::DATE'
                    fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
                    fixes.append(f"Added ::DATE casting to ORDER BY: {col}")
        
        return fixed_query, fixes
    
    @staticmethod
    def _detect_date_columns(query: str) -> List[str]:
        """
        Detect potential TEXT date columns from SQL query.
        
        Args:
            query: SQL query
            
        Returns:
            List of detected date column names
        """
        detected = []
        
        # Find all column references in the query
        # Pattern: word characters that look like column names
        pattern = r'\b([a-z_][a-z0-9_]*)\b'
        matches = re.findall(pattern, query, re.IGNORECASE)
        
        # Check if any match known date column patterns
        for match in matches:
            match_lower = match.lower()
            for date_pattern in SQLValidator.TEXT_DATE_PATTERNS:
                if date_pattern in match_lower:
                    if match not in detected:
                        detected.append(match)
                    break
        
        return detected
    
    @staticmethod
    def validate_query_syntax(query: str) -> Tuple[bool, str]:
        """
        Basic SQL syntax validation.
        
        Args:
            query: SQL query
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query is empty"
        
        query_upper = query.upper().strip()
        
        # Check for required keywords
        if not any(query_upper.startswith(kw) for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']):
            return False, "Query must start with SELECT, INSERT, UPDATE, DELETE, or WITH"
        
        # Check for balanced parentheses
        if query.count('(') != query.count(')'):
            return False, "Unbalanced parentheses"
        
        # Check for balanced quotes
        single_quotes = query.count("'") - query.count("\\'")
        if single_quotes % 2 != 0:
            return False, "Unbalanced single quotes"
        
        return True, ""
    
    @staticmethod
    def get_validation_report(query: str, text_date_columns: List[str] = None) -> dict:
        """
        Get comprehensive validation report for a query.
        
        Args:
            query: SQL query
            text_date_columns: List of known TEXT date columns
            
        Returns:
            Dictionary with validation results
        """
        # Syntax validation
        is_valid, syntax_error = SQLValidator.validate_query_syntax(query)
        
        # Date casting validation
        fixed_query, fixes = SQLValidator.validate_and_fix_date_casting(query, text_date_columns)
        
        # Detect if query was modified
        was_modified = fixed_query != query
        
        return {
            "original_query": query,
            "fixed_query": fixed_query,
            "is_valid_syntax": is_valid,
            "syntax_error": syntax_error,
            "was_modified": was_modified,
            "fixes_applied": fixes,
            "detected_date_columns": SQLValidator._detect_date_columns(query),
            "recommendation": "Use fixed_query" if was_modified else "Query looks good"
        }
