"""
Schema registry for documenting table structures and relationships.
AUTO-GENERATED from actual database schema - DO NOT EDIT MANUALLY
"""
from typing import Dict, List, Any


# Table schema definitions with business context
TABLE_SCHEMAS = {
    "affiliate_warehouse_inventory": {
        "business_purpose": "Table affiliate_warehouse_inventory - 10 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "study_code", "type": "VARCHAR", "description": "study_code"},
            {"name": "lot_number", "type": "VARCHAR", "description": "lot_number"},
            {"name": "wh_id", "type": "VARCHAR", "description": "wh_id"},
            {"name": "wh_lpn_number", "type": "VARCHAR", "description": "wh_lpn_number"},
            {"name": "package_desc", "type": "VARCHAR", "description": "package_desc"}
        ],
    },

    "allocated_materials_to_orders": {
        "business_purpose": "Table allocated_materials_to_orders - 30 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "order_id", "type": "VARCHAR", "description": "order_id"},
            {"name": "material_component", "type": "VARCHAR", "description": "material_component"},
            {"name": "material_component_batch", "type": "VARCHAR", "description": "material_component_batch"},
            {"name": "order_quantity", "type": "INTEGER", "description": "order_quantity"},
            {"name": "fing_batch", "type": "VARCHAR", "description": "fing_batch"}
        ],
    },

    "available_inventory_report": {
        "business_purpose": "Table available_inventory_report - 14 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "trial_name", "type": "VARCHAR", "description": "trial_name"},
            {"name": "location", "type": "VARCHAR", "description": "location"},
            {"name": "investigator", "type": "VARCHAR", "description": "investigator"},
            {"name": "package_type_description", "type": "VARCHAR", "description": "package_type_description"},
            {"name": "lot", "type": "VARCHAR", "description": "lot"}
        ],
    },

    "batch_geneology": {
        "business_purpose": "Table batch_geneology - 26 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "batch_number", "type": "VARCHAR", "description": "batch_number"},
            {"name": "batch_use", "type": "VARCHAR", "description": "batch_use"},
            {"name": "bw:_document_item_number", "type": "INTEGER", "description": "bw:_document_item_number"},
            {"name": "id", "type": "INTEGER", "description": "id"},
            {"name": "inspection_lot_number", "type": "VARCHAR", "description": "inspection_lot_number"}
        ],
    },

    "batch_master": {
        "business_purpose": "Table batch_master - 42 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "adjusted_expiration_date", "type": "VARCHAR", "description": "adjusted_expiration_date"},
            {"name": "batch_in_restricted_use_stock", "type": "VARCHAR", "description": "batch_in_restricted_use_stock"},
            {"name": "batch_number", "type": "VARCHAR", "description": "batch_number"},
            {"name": "batch_use", "type": "VARCHAR", "description": "batch_use"},
            {"name": "date_of_manufacture", "type": "VARCHAR", "description": "date_of_manufacture"}
        ],
    },

    "bom_details": {
        "business_purpose": "Table bom_details - 31 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "alternative_bom_id", "type": "INTEGER", "description": "alternative_bom_id"},
            {"name": "alternative_bom_text", "type": "VARCHAR", "description": "alternative_bom_text"},
            {"name": "batch_id", "type": "VARCHAR", "description": "batch_id"},
            {"name": "bill_of_material", "type": "VARCHAR", "description": "bill_of_material"},
            {"name": "bom_component_id", "type": "VARCHAR", "description": "bom_component_id"}
        ],
    },

    "complete_warehouse_inventory": {
        "business_purpose": "Table complete_warehouse_inventory - 14 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "lpn", "type": "VARCHAR", "description": "lpn"},
            {"name": "location_id", "type": "VARCHAR", "description": "location_id"},
            {"name": "class", "type": "VARCHAR", "description": "class"},
            {"name": "lot_number", "type": "VARCHAR", "description": "lot_number"}
        ],
    },

    "country_level_enrollment_report": {
        "business_purpose": "Table country_level_enrollment_report - 7 columns",
        "workflow": ["A"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "country_name", "type": "VARCHAR", "description": "country_name"},
            {"name": "enrollment_level", "type": "VARCHAR", "description": "enrollment_level"},
            {"name": "total_enrolled_forecast", "type": "INTEGER", "description": "total_enrolled_forecast"},
            {"name": "total_enrolled_planned", "type": "INTEGER", "description": "total_enrolled_planned"}
        ],
    },

    "distribution_order_report": {
        "business_purpose": "Table distribution_order_report - 8 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "site_id", "type": "VARCHAR", "description": "site_id"},
            {"name": "order_number", "type": "VARCHAR", "description": "order_number"},
            {"name": "ivrs_number", "type": "VARCHAR", "description": "ivrs_number"},
            {"name": "status", "type": "VARCHAR", "description": "status"}
        ],
    },

    "enrollment_rate_report": {
        "business_purpose": "Table enrollment_rate_report - 5 columns",
        "workflow": ["A"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "country", "type": "VARCHAR", "description": "country"},
            {"name": "site", "type": "VARCHAR", "description": "site"},
            {"name": "year", "type": "INTEGER", "description": "year"},
            {"name": "months_jan_feb_dec", "type": "VARCHAR", "description": "months_jan_feb_dec"}
        ],
    },

    "excursion_detail_report": {
        "business_purpose": "Table excursion_detail_report - 17 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "excursion_id_/_allowable_hours_change_event_id", "type": "VARCHAR", "description": "excursion_id_/_allowable_hours_change_event_id"},
            {"name": "excursion_type", "type": "VARCHAR", "description": "excursion_type"},
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "shipment_number_/_out_bound_delivery_number", "type": "VARCHAR", "description": "shipment_number_/_out_bound_delivery_number"},
            {"name": "lot_number", "type": "VARCHAR", "description": "lot_number"}
        ],
    },

    "global_gateway_inventory_report": {
        "business_purpose": "Table global_gateway_inventory_report - 10 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "protocol", "type": "VARCHAR", "description": "protocol"},
            {"name": "part_id", "type": "VARCHAR", "description": "part_id"},
            {"name": "client_part_id", "type": "VARCHAR", "description": "client_part_id"},
            {"name": "description_unblinded", "type": "VARCHAR", "description": "description_unblinded"},
            {"name": "facility", "type": "VARCHAR", "description": "facility"}
        ],
    },

    "inspection_lot": {
        "business_purpose": "Table inspection_lot - 14 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "order_number", "type": "VARCHAR", "description": "order_number"},
            {"name": "batch_number", "type": "VARCHAR", "description": "batch_number"},
            {"name": "material_number", "type": "VARCHAR", "description": "material_number"},
            {"name": "material_type", "type": "VARCHAR", "description": "material_type"}
        ],
    },

    "inventory_detail_report": {
        "business_purpose": "Table inventory_detail_report - 9 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "study_id", "type": "VARCHAR", "description": "study_id"},
            {"name": "lot_number", "type": "VARCHAR", "description": "lot_number"},
            {"name": "package_number", "type": "VARCHAR", "description": "package_number"},
            {"name": "package_desc", "type": "VARCHAR", "description": "package_desc"},
            {"name": "rqst_date", "type": "VARCHAR", "description": "rqst_date"}
        ],
    },

    "ip_shipping_timelines_report": {
        "business_purpose": "Table ip_shipping_timelines_report - 3 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "ip_helper", "type": "VARCHAR", "description": "ip_helper"},
            {"name": "ip_timeline", "type": "VARCHAR", "description": "ip_timeline"},
            {"name": "country_name", "type": "VARCHAR", "description": "country_name"}
        ],
    },

    "lot_status_report": {
        "business_purpose": "Table lot_status_report - 9 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "warehouse/affiliate", "type": "VARCHAR", "description": "warehouse/affiliate"},
            {"name": "site_number", "type": "VARCHAR", "description": "site_number"},
            {"name": "country", "type": "VARCHAR", "description": "country"},
            {"name": "package_description", "type": "VARCHAR", "description": "package_description"}
        ],
    },

    "manufacturing_orders": {
        "business_purpose": "Table manufacturing_orders - 52 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "order_id", "type": "VARCHAR", "description": "order_id"},
            {"name": "order_type", "type": "VARCHAR", "description": "order_type"},
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "order_status", "type": "VARCHAR", "description": "order_status"},
            {"name": "fing_batch", "type": "VARCHAR", "description": "fing_batch"}
        ],
    },

    "material_country_requirements": {
        "business_purpose": "Table material_country_requirements - 12 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "client", "type": "VARCHAR", "description": "client"},
            {"name": "countries", "type": "VARCHAR", "description": "countries"},
            {"name": "created_on", "type": "VARCHAR", "description": "created_on"},
            {"name": "ct_compound", "type": "VARCHAR", "description": "ct_compound"},
            {"name": "ct_label_group", "type": "VARCHAR", "description": "ct_label_group"}
        ],
    },

    "material_master": {
        "business_purpose": "Table material_master - 130 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "material_number", "type": "VARCHAR", "description": "material_number"},
            {"name": "material_description", "type": "VARCHAR", "description": "material_description"},
            {"name": "material_type", "type": "VARCHAR", "description": "material_type"},
            {"name": "mrp_controller", "type": "VARCHAR", "description": "mrp_controller"}
        ],
    },

    "material_requirements": {
        "business_purpose": "Table material_requirements - 28 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "plant_id", "type": "VARCHAR", "description": "plant_id"},
            {"name": "planning_plant", "type": "VARCHAR", "description": "planning_plant"},
            {"name": "material_id", "type": "VARCHAR", "description": "material_id"},
            {"name": "material", "type": "VARCHAR", "description": "material"}
        ],
    },

    "material_specification": {
        "business_purpose": "Table material_specification - 27 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "cc_characteristic_value_number", "type": "INTEGER", "description": "cc_characteristic_value_number"},
            {"name": "cc_characteristic_value_text", "type": "VARCHAR", "description": "cc_characteristic_value_text"},
            {"name": "characteristic_description", "type": "VARCHAR", "description": "characteristic_description"},
            {"name": "characteristic_format", "type": "VARCHAR", "description": "characteristic_format"},
            {"name": "characteristic_id", "type": "VARCHAR", "description": "characteristic_id"}
        ],
    },

    "materials": {
        "business_purpose": "Table materials - 35 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "gross_weight_unit_kilogram", "type": "DECIMAL", "description": "gross_weight_unit_kilogram"},
            {"name": "goods_rcpt_pr_time", "type": "VARCHAR", "description": "goods_rcpt_pr_time"},
            {"name": "net_weight_of_item", "type": "DECIMAL", "description": "net_weight_of_item"},
            {"name": "delivery_time", "type": "VARCHAR", "description": "delivery_time"},
            {"name": "total_repleishment_lead_time", "type": "VARCHAR", "description": "total_repleishment_lead_time"}
        ],
    },

    "materials_per_study": {
        "business_purpose": "Table materials_per_study - 13 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "changed_by", "type": "VARCHAR", "description": "changed_by"},
            {"name": "country_key", "type": "VARCHAR", "description": "country_key"},
            {"name": "last_changed_on", "type": "VARCHAR", "description": "last_changed_on"},
            {"name": "material", "type": "VARCHAR", "description": "material"},
            {"name": "material_type", "type": "VARCHAR", "description": "material_type"}
        ],
    },

    "metrics_over_time_report": {
        "business_purpose": "Table metrics_over_time_report - 13 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "study_alias", "type": "VARCHAR", "description": "study_alias"},
            {"name": "country_name", "type": "VARCHAR", "description": "country_name"},
            {"name": "site_reference_number", "type": "VARCHAR", "description": "site_reference_number"},
            {"name": "enrollment_over_time_level", "type": "VARCHAR", "description": "enrollment_over_time_level"},
            {"name": "period_frequency", "type": "VARCHAR", "description": "period_frequency"}
        ],
    },

    "nmrf": {
        "business_purpose": "Table nmrf - 16 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "material_number", "type": "VARCHAR", "description": "material_number"},
            {"name": "bom_status", "type": "VARCHAR", "description": "bom_status"},
            {"name": "label_material_status", "type": "VARCHAR", "description": "label_material_status"},
            {"name": "ly_number", "type": "VARCHAR", "description": "ly_number"},
            {"name": "created_date", "type": "VARCHAR", "description": "created_date"}
        ],
    },

    "order_phases": {
        "business_purpose": "Table order_phases - 9 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "order_num", "type": "VARCHAR", "description": "order_num"},
            {"name": "operation_num", "type": "INTEGER", "description": "operation_num"},
            {"name": "operation_description", "type": "VARCHAR", "description": "operation_description"},
            {"name": "plant_id", "type": "VARCHAR", "description": "plant_id"}
        ],
    },

    "outstanding_site_shipment_status_report": {
        "business_purpose": "Table outstanding_site_shipment_status_report - 8 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "site_number", "type": "VARCHAR", "description": "site_number"},
            {"name": "country", "type": "VARCHAR", "description": "country"},
            {"name": "shipment_#", "type": "VARCHAR", "description": "shipment_#"},
            {"name": "package_description", "type": "VARCHAR", "description": "package_description"}
        ],
    },

    "patient_status_and_treatment_report": {
        "business_purpose": "Table patient_status_and_treatment_report - 7 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "country", "type": "VARCHAR", "description": "country"},
            {"name": "site", "type": "VARCHAR", "description": "site"},
            {"name": "visit", "type": "VARCHAR", "description": "visit"},
            {"name": "visit_date", "type": "VARCHAR", "description": "visit_date"}
        ],
    },

    "planned_order_recipe": {
        "business_purpose": "Table planned_order_recipe - 12 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "recipe_group", "type": "VARCHAR", "description": "recipe_group"},
            {"name": "recipe", "type": "VARCHAR", "description": "recipe"},
            {"name": "recipe_days", "type": "INTEGER", "description": "recipe_days"},
            {"name": "phase", "type": "VARCHAR", "description": "phase"},
            {"name": "phase_text", "type": "VARCHAR", "description": "phase_text"}
        ],
    },

    "planned_orders": {
        "business_purpose": "Table planned_orders - 23 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "availability_date_or_requirements_date", "type": "VARCHAR", "description": "availability_date_or_requirements_date"},
            {"name": "category_of_stock/receipt/requirement/forecast", "type": "VARCHAR", "description": "category_of_stock/receipt/requirement/forecast"},
            {"name": "category_type", "type": "VARCHAR", "description": "category_type"},
            {"name": "counter", "type": "INTEGER", "description": "counter"},
            {"name": "country/reg", "type": "VARCHAR", "description": "country/reg"}
        ],
    },

    "purchase_order_kpi": {
        "business_purpose": "Table purchase_order_kpi - 52 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "old_qty", "type": "INTEGER", "description": "old_qty"},
            {"name": "new_qty", "type": "INTEGER", "description": "new_qty"},
            {"name": "purchase_document_date", "type": "VARCHAR", "description": "purchase_document_date"},
            {"name": "purchasing_document_type", "type": "VARCHAR", "description": "purchasing_document_type"},
            {"name": "material", "type": "VARCHAR", "description": "material"}
        ],
    },

    "purchase_order_quantities": {
        "business_purpose": "Table purchase_order_quantities - 57 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "base_unit_of_measure", "type": "VARCHAR", "description": "base_unit_of_measure"},
            {"name": "calendar_month", "type": "INTEGER", "description": "calendar_month"},
            {"name": "calendar_week", "type": "INTEGER", "description": "calendar_week"},
            {"name": "country", "type": "VARCHAR", "description": "country"},
            {"name": "currency_gr_value_pstg_date", "type": "DECIMAL", "description": "currency_gr_value_pstg_date"}
        ],
    },

    "purchase_requirement": {
        "business_purpose": "Table purchase_requirement - 19 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "actual_delivery_date", "type": "VARCHAR", "description": "actual_delivery_date"},
            {"name": "item_number_of_purchase_requisition", "type": "INTEGER", "description": "item_number_of_purchase_requisition"},
            {"name": "item_number_of_purchasing_document", "type": "INTEGER", "description": "item_number_of_purchasing_document"},
            {"name": "material", "type": "VARCHAR", "description": "material"},
            {"name": "mrp_controller", "type": "VARCHAR", "description": "mrp_controller"}
        ],
    },

    "qdocs": {
        "business_purpose": "Table qdocs - 8 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "title", "type": "VARCHAR", "description": "title"},
            {"name": "material_name", "type": "VARCHAR", "description": "material_name"},
            {"name": "material_description", "type": "VARCHAR", "description": "material_description"},
            {"name": "ly_id", "type": "VARCHAR", "description": "ly_id"},
            {"name": "ly_number", "type": "VARCHAR", "description": "ly_number"}
        ],
    },

    "re_evaluation": {
        "business_purpose": "Table re_evaluation - 12 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "id", "type": "VARCHAR", "description": "id"},
            {"name": "created", "type": "VARCHAR", "description": "created"},
            {"name": "request_type_molecule_planner_to_complete", "type": "VARCHAR", "description": "request_type_molecule_planner_to_complete"},
            {"name": "sample_status_ndp_material_coordinator_to_complete", "type": "VARCHAR", "description": "sample_status_ndp_material_coordinator_to_complete"},
            {"name": "ly_number_molecule_planner_to_complete", "type": "VARCHAR", "description": "ly_number_molecule_planner_to_complete"}
        ],
    },

    "rim": {
        "business_purpose": "Table rim - 12 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "name_v", "type": "VARCHAR", "description": "name_v"},
            {"name": "filename_v", "type": "VARCHAR", "description": "filename_v"},
            {"name": "health_authority_division_c", "type": "VARCHAR", "description": "health_authority_division_c"},
            {"name": "type_v", "type": "VARCHAR", "description": "type_v"},
            {"name": "status_v", "type": "VARCHAR", "description": "status_v"}
        ],
    },

    "shipment_status_report": {
        "business_purpose": "Table shipment_status_report - 12 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "status", "type": "VARCHAR", "description": "status"},
            {"name": "shipment", "type": "VARCHAR", "description": "shipment"},
            {"name": "lpn#", "type": "VARCHAR", "description": "lpn#"},
            {"name": "lpn_status", "type": "VARCHAR", "description": "lpn_status"},
            {"name": "package_count", "type": "INTEGER", "description": "package_count"}
        ],
    },

    "shipment_summary_report": {
        "business_purpose": "Table shipment_summary_report - 17 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "order_number", "type": "VARCHAR", "description": "order_number"},
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "iwrs_number", "type": "VARCHAR", "description": "iwrs_number"},
            {"name": "site_number", "type": "VARCHAR", "description": "site_number"},
            {"name": "ship_to_country_code", "type": "VARCHAR", "description": "ship_to_country_code"}
        ],
    },

    "study_level_enrollment_report": {
        "business_purpose": "Table study_level_enrollment_report - 6 columns",
        "workflow": ["A"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "enrollment_level", "type": "VARCHAR", "description": "enrollment_level"},
            {"name": "total_enrolled_forecast", "type": "INTEGER", "description": "total_enrolled_forecast"},
            {"name": "total_enrolled_planned", "type": "INTEGER", "description": "total_enrolled_planned"},
            {"name": "total_enrolled_actual", "type": "INTEGER", "description": "total_enrolled_actual"}
        ],
    },

    "warehouse_and_site_shipment_tracking_report": {
        "business_purpose": "Table warehouse_and_site_shipment_tracking_report - 27 columns",
        "workflow": ["B"],
        "key_columns": [
            {"name": "order_number", "type": "VARCHAR", "description": "order_number"},
            {"name": "trial_alias", "type": "VARCHAR", "description": "trial_alias"},
            {"name": "country_name", "type": "VARCHAR", "description": "country_name"},
            {"name": "actual_qty", "type": "INTEGER", "description": "actual_qty"},
            {"name": "carrier_code", "type": "VARCHAR", "description": "carrier_code"}
        ],
    },

}


def get_table_schema(table_name: str) -> Dict[str, Any]:
    """Get schema definition for a table."""
    return TABLE_SCHEMAS.get(table_name, {})


def get_tables_for_workflow(workflow: str) -> List[str]:
    """Get list of tables relevant for a specific workflow."""
    tables = []
    for table_name, schema in TABLE_SCHEMAS.items():
        if workflow in schema.get("workflow", []):
            tables.append(table_name)
    return tables


def get_all_table_names() -> List[str]:
    """Get list of all documented table names."""
    return list(TABLE_SCHEMAS.keys())


def format_schema_for_agent(table_name: str) -> str:
    """Format schema information for agent consumption."""
    schema = get_table_schema(table_name)
    
    if not schema:
        return f"Schema not found for table: {table_name}"
    
    output = [
        f"Table Name: {table_name}",
        f"Business Purpose: {schema['business_purpose']}",
        "",
        "Key Columns:"
    ]
    
    for col in schema['key_columns']:
        output.append(f"  - {col['name']} ({col['type']}): {col['description']}")
    
    return "\n".join(output)