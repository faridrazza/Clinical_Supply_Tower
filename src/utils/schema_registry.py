"""
Schema registry for documenting table structures and relationships.
Enhanced with rich metadata for improved semantic search in ChromaDB.
"""
from typing import Dict, List, Any


# Table schema definitions with rich business context for semantic search
TABLE_SCHEMAS = {
    "affiliate_warehouse_inventory": {
        "business_purpose": "Tracks inventory levels at affiliate warehouse locations including lot numbers, package descriptions, and warehouse identifiers for clinical trial supplies",
        "keywords": ["warehouse", "inventory", "stock", "affiliate", "lot", "package", "storage", "depot"],
        "sample_queries": ["What inventory is at the affiliate warehouse?", "Show warehouse stock levels", "Affiliate depot inventory"],
        "related_entities": ["lot_number", "warehouse", "package"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "study_code", "type": "VARCHAR", "description": "Clinical study identifier"},
            {"name": "lot_number", "type": "VARCHAR", "description": "Batch/lot number for tracking"},
            {"name": "wh_id", "type": "VARCHAR", "description": "Warehouse identifier"},
            {"name": "wh_lpn_number", "type": "VARCHAR", "description": "License plate number in warehouse"},
            {"name": "package_desc", "type": "VARCHAR", "description": "Package description"}
        ],
    },

    "allocated_materials_to_orders": {
        "business_purpose": "Maps materials and batches allocated to specific orders including quantities, order status, stock levels, and material components for clinical trial distribution and inventory tracking",
        "keywords": ["allocation", "order", "material", "batch", "quantity", "assigned", "distribution", "component", "stock", "stock level", "current stock", "inventory", "MAT-"],
        "sample_queries": ["What materials are allocated to this order?", "Show order allocations", "Which batch is assigned to order?", "What is the current stock level for material?", "Stock level for MAT-", "Material inventory"],
        "related_entities": ["order_id", "material", "batch", "quantity", "stock"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "order_id", "type": "VARCHAR", "description": "Order identifier"},
            {"name": "material_component", "type": "VARCHAR", "description": "Material component ID (MAT-XXXXX)"},
            {"name": "material_component_batch", "type": "VARCHAR", "description": "Batch number of material"},
            {"name": "order_quantity", "type": "INTEGER", "description": "Quantity/stock allocated to order"},
            {"name": "fing_batch", "type": "VARCHAR", "description": "Finished goods batch"}
        ],
    },

    "available_inventory_report": {
        "business_purpose": "Reports available clinical trial inventory by location, investigator, and lot/batch with package counts, expiry dates, and quantity metrics for supply planning",
        "keywords": ["available", "inventory", "stock", "packages", "location", "investigator", "supply", "quantity", "lot", "batch", "expiry", "details"],
        "sample_queries": ["What inventory is available?", "Show available stock", "Current inventory levels", "Show me details for batch", "Batch details", "Lot information"],
        "related_entities": ["trial", "location", "lot", "batch", "packages", "expiry"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_name", "type": "VARCHAR", "description": "Clinical trial name"},
            {"name": "location", "type": "VARCHAR", "description": "Geographic location"},
            {"name": "investigator", "type": "VARCHAR", "description": "Principal investigator"},
            {"name": "package_type_description", "type": "VARCHAR", "description": "Type of package"},
            {"name": "lot", "type": "VARCHAR", "description": "Lot/batch number"}
        ],
    },

    "batch_geneology": {
        "business_purpose": "Tracks batch genealogy and lineage showing parent-child relationships between batches for traceability and quality control",
        "keywords": ["batch", "genealogy", "lineage", "traceability", "parent", "child", "history", "origin"],
        "sample_queries": ["What is the batch genealogy?", "Show batch lineage", "Trace batch origin"],
        "related_entities": ["batch_number", "inspection_lot"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "batch_number", "type": "VARCHAR", "description": "Batch identifier"},
            {"name": "batch_use", "type": "VARCHAR", "description": "Intended use of batch"},
            {"name": "bw:_document_item_number", "type": "INTEGER", "description": "Document item reference"},
            {"name": "id", "type": "INTEGER", "description": "Record identifier"},
            {"name": "inspection_lot_number", "type": "VARCHAR", "description": "Quality inspection lot"}
        ],
    },

    "batch_master": {
        "business_purpose": "Master data for all batches including expiration dates, manufacturing dates, batch status, and restricted use flags for inventory management",
        "keywords": ["batch", "master", "expiration", "expiry", "manufacture", "status", "restricted", "shelf-life"],
        "sample_queries": ["When does this batch expire?", "Show batch details", "Batch expiration date", "Is batch restricted?"],
        "related_entities": ["batch_number", "expiration_date", "manufacture_date"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "adjusted_expiration_date", "type": "VARCHAR", "description": "Adjusted expiry date after extension"},
            {"name": "batch_in_restricted_use_stock", "type": "VARCHAR", "description": "Restricted use flag"},
            {"name": "batch_number", "type": "VARCHAR", "description": "Batch identifier"},
            {"name": "batch_use", "type": "VARCHAR", "description": "Batch usage type"},
            {"name": "date_of_manufacture", "type": "VARCHAR", "description": "Manufacturing date"}
        ],
    },

    "bom_details": {
        "business_purpose": "Bill of Materials details showing component relationships, quantities, and assembly structure for clinical trial product manufacturing",
        "keywords": ["bom", "bill of materials", "component", "assembly", "recipe", "manufacturing", "structure"],
        "sample_queries": ["What are the BOM components?", "Show bill of materials", "Material composition"],
        "related_entities": ["batch_id", "bom_component"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "alternative_bom_id", "type": "INTEGER", "description": "Alternative BOM identifier"},
            {"name": "alternative_bom_text", "type": "VARCHAR", "description": "Alternative BOM description"},
            {"name": "batch_id", "type": "VARCHAR", "description": "Associated batch"},
            {"name": "bill_of_material", "type": "VARCHAR", "description": "BOM identifier"},
            {"name": "bom_component_id", "type": "VARCHAR", "description": "Component identifier"}
        ],
    },

    "complete_warehouse_inventory": {
        "business_purpose": "Complete inventory snapshot across all warehouses showing LPN, location, lot numbers, and classification for full visibility",
        "keywords": ["warehouse", "inventory", "complete", "full", "stock", "lpn", "location", "storage"],
        "sample_queries": ["Show complete warehouse inventory", "Full inventory report", "All warehouse stock"],
        "related_entities": ["trial_alias", "lpn", "lot_number", "location"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "lpn", "type": "VARCHAR", "description": "License plate number"},
            {"name": "location_id", "type": "VARCHAR", "description": "Storage location"},
            {"name": "class", "type": "VARCHAR", "description": "Inventory classification"},
            {"name": "lot_number", "type": "VARCHAR", "description": "Lot/batch number"}
        ],
    },

    "country_level_enrollment_report": {
        "business_purpose": "Reports patient enrollment statistics by country including forecast, planned, and actual enrollment numbers with monthly enrollment rates for demand planning",
        "keywords": ["enrollment", "country", "patients", "forecast", "planned", "actual", "rate", "recruitment", "participants"],
        "sample_queries": ["What is the enrollment rate for this country?", "Show country enrollment", "Patient recruitment by country", "Enrollment forecast"],
        "related_entities": ["trial_alias", "country", "enrollment"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "country_name", "type": "VARCHAR", "description": "Country name"},
            {"name": "enrollment_level", "type": "VARCHAR", "description": "Enrollment aggregation level"},
            {"name": "total_enrolled_forecast", "type": "INTEGER", "description": "Forecasted enrollment"},
            {"name": "total_enrolled_planned", "type": "INTEGER", "description": "Planned enrollment"}
        ],
    },

    "distribution_order_report": {
        "business_purpose": "Tracks distribution orders for clinical supplies including order status, site assignments, and delivery tracking for logistics management",
        "keywords": ["distribution", "order", "delivery", "site", "status", "shipment", "logistics", "completed", "released"],
        "sample_queries": ["Show distribution orders", "Order status for trial", "Delivery orders", "Completed orders"],
        "related_entities": ["trial_alias", "site_id", "order_number", "status"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "site_id", "type": "VARCHAR", "description": "Clinical site identifier"},
            {"name": "order_number", "type": "VARCHAR", "description": "Distribution order number"},
            {"name": "ivrs_number", "type": "VARCHAR", "description": "IVRS reference number"},
            {"name": "status", "type": "VARCHAR", "description": "Order status (Completed, Released, etc.)"}
        ],
    },

    "enrollment_rate_report": {
        "business_purpose": "Detailed enrollment rate metrics by trial, country, and site showing monthly patient recruitment rates for supply demand forecasting",
        "keywords": ["enrollment", "rate", "monthly", "recruitment", "patients", "site", "country", "forecast", "demand"],
        "sample_queries": ["What is the enrollment rate?", "Monthly enrollment", "Patient recruitment rate", "Site enrollment"],
        "related_entities": ["trial_alias", "country", "site", "enrollment_rate"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "country", "type": "VARCHAR", "description": "Country name"},
            {"name": "site", "type": "VARCHAR", "description": "Clinical site"},
            {"name": "year", "type": "INTEGER", "description": "Calendar year"},
            {"name": "months_jan_feb_dec", "type": "VARCHAR", "description": "Monthly enrollment data"}
        ],
    },

    "excursion_detail_report": {
        "business_purpose": "Records temperature excursions and deviations during shipment including excursion type, duration, and affected lots for quality management",
        "keywords": ["excursion", "temperature", "deviation", "quality", "shipment", "cold chain", "violation"],
        "sample_queries": ["Show temperature excursions", "Excursion details", "Cold chain violations"],
        "related_entities": ["trial_alias", "shipment", "lot_number", "excursion"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "excursion_id_/_allowable_hours_change_event_id", "type": "VARCHAR", "description": "Excursion identifier"},
            {"name": "excursion_type", "type": "VARCHAR", "description": "Type of excursion"},
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "shipment_number_/_out_bound_delivery_number", "type": "VARCHAR", "description": "Shipment reference"},
            {"name": "lot_number", "type": "VARCHAR", "description": "Affected lot number"}
        ],
    },

    "global_gateway_inventory_report": {
        "business_purpose": "Global gateway depot inventory showing protocol-level stock, part IDs, and facility locations for international distribution planning",
        "keywords": ["global", "gateway", "depot", "inventory", "international", "facility", "protocol"],
        "sample_queries": ["Global gateway inventory", "International depot stock", "Gateway facility inventory"],
        "related_entities": ["protocol", "part_id", "facility"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "protocol", "type": "VARCHAR", "description": "Study protocol"},
            {"name": "part_id", "type": "VARCHAR", "description": "Part identifier"},
            {"name": "client_part_id", "type": "VARCHAR", "description": "Client part reference"},
            {"name": "description_unblinded", "type": "VARCHAR", "description": "Unblinded description"},
            {"name": "facility", "type": "VARCHAR", "description": "Gateway facility"}
        ],
    },

    "inspection_lot": {
        "business_purpose": "Quality inspection lot records linking batches to trials, orders, and material types for quality assurance tracking",
        "keywords": ["inspection", "quality", "lot", "batch", "QA", "material", "testing"],
        "sample_queries": ["Show inspection lots", "Quality inspection for batch", "Batch inspection status"],
        "related_entities": ["trial_alias", "batch_number", "material_number"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "order_number", "type": "VARCHAR", "description": "Associated order"},
            {"name": "batch_number", "type": "VARCHAR", "description": "Batch being inspected"},
            {"name": "material_number", "type": "VARCHAR", "description": "Material identifier"},
            {"name": "material_type", "type": "VARCHAR", "description": "Type of material"}
        ],
    },

    "inventory_detail_report": {
        "business_purpose": "Detailed inventory report by study showing lot numbers, package details, and request dates for operational inventory management",
        "keywords": ["inventory", "detail", "stock", "package", "lot", "study"],
        "sample_queries": ["Inventory details", "Package inventory", "Study inventory report"],
        "related_entities": ["study_id", "lot_number", "package"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "study_id", "type": "VARCHAR", "description": "Study identifier"},
            {"name": "lot_number", "type": "VARCHAR", "description": "Lot/batch number"},
            {"name": "package_number", "type": "VARCHAR", "description": "Package identifier"},
            {"name": "package_desc", "type": "VARCHAR", "description": "Package description"},
            {"name": "rqst_date", "type": "VARCHAR", "description": "Request date"}
        ],
    },

    "ip_shipping_timelines_report": {
        "business_purpose": "Investigational product shipping timelines by country showing door-to-door delivery times for logistics planning and feasibility assessment",
        "keywords": ["shipping", "timeline", "delivery", "logistics", "transport", "days", "country", "door-to-door", "lead time"],
        "sample_queries": ["What is the shipping timeline to this country?", "Delivery time", "How long to ship?", "Transport timeline"],
        "related_entities": ["country_name", "shipping_timeline"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "ip_helper", "type": "VARCHAR", "description": "IP logistics helper"},
            {"name": "ip_timeline", "type": "VARCHAR", "description": "Shipping timeline in days"},
            {"name": "country_name", "type": "VARCHAR", "description": "Destination country"}
        ],
    },

    "lot_status_report": {
        "business_purpose": "Lot status tracking by warehouse, site, and country showing package descriptions and current status for inventory visibility",
        "keywords": ["lot", "status", "warehouse", "site", "country", "package", "tracking"],
        "sample_queries": ["Lot status", "Where is this lot?", "Lot location and status"],
        "related_entities": ["trial_alias", "lot", "warehouse", "country"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "warehouse/affiliate", "type": "VARCHAR", "description": "Warehouse or affiliate"},
            {"name": "site_number", "type": "VARCHAR", "description": "Site identifier"},
            {"name": "country", "type": "VARCHAR", "description": "Country location"},
            {"name": "package_description", "type": "VARCHAR", "description": "Package description"}
        ],
    },

    "manufacturing_orders": {
        "business_purpose": "Manufacturing order records including order type, status, batch assignments, and trial linkage for production planning and tracking",
        "keywords": ["manufacturing", "production", "order", "batch", "status", "plant", "make"],
        "sample_queries": ["Show manufacturing orders", "Production orders", "Manufacturing status"],
        "related_entities": ["order_id", "trial_alias", "batch", "status"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "order_id", "type": "VARCHAR", "description": "Manufacturing order ID"},
            {"name": "order_type", "type": "VARCHAR", "description": "Type of order"},
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "order_status", "type": "VARCHAR", "description": "Current order status"},
            {"name": "fing_batch", "type": "VARCHAR", "description": "Finished goods batch"}
        ],
    },

    "material_country_requirements": {
        "business_purpose": "Regulatory requirements for materials by country including approval status, label groups, and compound specifications for country-specific compliance and clinical supply approval",
        "keywords": ["country", "requirements", "regulatory", "approval", "approved", "compliance", "label", "compound", "clinical supply", "Japan", "Germany", "USA"],
        "sample_queries": ["Is clinical supply approved for this country?", "Country approval status", "Regulatory requirements by country", "Is material approved for Japan?", "Country compliance"],
        "related_entities": ["countries", "material", "compound", "approval"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "client", "type": "VARCHAR", "description": "Client/sponsor"},
            {"name": "countries", "type": "VARCHAR", "description": "Country name for approval"},
            {"name": "created_on", "type": "VARCHAR", "description": "Record creation date"},
            {"name": "ct_compound", "type": "VARCHAR", "description": "Clinical trial compound"},
            {"name": "ct_label_group", "type": "VARCHAR", "description": "Label group classification"}
        ],
    },

    "material_master": {
        "business_purpose": "Master data for all materials including descriptions, types, MRP controllers, and trial associations for material management",
        "keywords": ["material", "master", "description", "type", "MRP", "product"],
        "sample_queries": ["Material details", "What is this material?", "Material master data"],
        "related_entities": ["trial_alias", "material_number", "material_type"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "material_number", "type": "VARCHAR", "description": "Material ID"},
            {"name": "material_description", "type": "VARCHAR", "description": "Material description"},
            {"name": "material_type", "type": "VARCHAR", "description": "Type classification"},
            {"name": "mrp_controller", "type": "VARCHAR", "description": "MRP controller"}
        ],
    },

    "material_requirements": {
        "business_purpose": "Material requirements planning data by trial and plant for supply planning and procurement",
        "keywords": ["material", "requirements", "planning", "MRP", "demand", "supply"],
        "sample_queries": ["Material requirements", "What materials are needed?", "MRP requirements"],
        "related_entities": ["trial_alias", "material_id", "plant"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "plant_id", "type": "VARCHAR", "description": "Plant identifier"},
            {"name": "planning_plant", "type": "VARCHAR", "description": "Planning plant"},
            {"name": "material_id", "type": "VARCHAR", "description": "Material identifier"},
            {"name": "material", "type": "VARCHAR", "description": "Material name"}
        ],
    },

    "material_specification": {
        "business_purpose": "Material specifications and characteristics including quality parameters and testing requirements",
        "keywords": ["specification", "characteristics", "quality", "parameters", "testing", "specs"],
        "sample_queries": ["Material specifications", "Quality specs", "Material characteristics"],
        "related_entities": ["characteristic", "material"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "cc_characteristic_value_number", "type": "INTEGER", "description": "Characteristic value number"},
            {"name": "cc_characteristic_value_text", "type": "VARCHAR", "description": "Characteristic value text"},
            {"name": "characteristic_description", "type": "VARCHAR", "description": "Description of characteristic"},
            {"name": "characteristic_format", "type": "VARCHAR", "description": "Format specification"},
            {"name": "characteristic_id", "type": "VARCHAR", "description": "Characteristic identifier"}
        ],
    },

    "materials": {
        "business_purpose": "Material properties including weights, delivery times, and lead times for logistics and planning calculations",
        "keywords": ["material", "weight", "delivery", "lead time", "properties"],
        "sample_queries": ["Material properties", "Delivery time for material", "Material lead time"],
        "related_entities": ["material", "delivery_time"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "gross_weight_unit_kilogram", "type": "DECIMAL", "description": "Gross weight in kg"},
            {"name": "goods_rcpt_pr_time", "type": "VARCHAR", "description": "Goods receipt processing time"},
            {"name": "net_weight_of_item", "type": "DECIMAL", "description": "Net weight"},
            {"name": "delivery_time", "type": "VARCHAR", "description": "Standard delivery time"},
            {"name": "total_repleishment_lead_time", "type": "VARCHAR", "description": "Total replenishment lead time"}
        ],
    },

    "materials_per_study": {
        "business_purpose": "Materials assigned to specific studies by country showing material types and change history",
        "keywords": ["material", "study", "country", "assignment", "trial"],
        "sample_queries": ["Materials for this study", "Study material list", "What materials are in this trial?"],
        "related_entities": ["material", "country", "study"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "changed_by", "type": "VARCHAR", "description": "Last changed by user"},
            {"name": "country_key", "type": "VARCHAR", "description": "Country code"},
            {"name": "last_changed_on", "type": "VARCHAR", "description": "Last change date"},
            {"name": "material", "type": "VARCHAR", "description": "Material identifier"},
            {"name": "material_type", "type": "VARCHAR", "description": "Material type"}
        ],
    },

    "metrics_over_time_report": {
        "business_purpose": "Time-series metrics for enrollment and other KPIs by study, country, and site with period frequency for trend analysis",
        "keywords": ["metrics", "time", "trend", "enrollment", "KPI", "period", "quarterly", "monthly"],
        "sample_queries": ["Enrollment metrics over time", "Trend analysis", "Quarterly metrics"],
        "related_entities": ["study_alias", "country_name", "site"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "study_alias", "type": "VARCHAR", "description": "Study identifier"},
            {"name": "country_name", "type": "VARCHAR", "description": "Country name"},
            {"name": "site_reference_number", "type": "VARCHAR", "description": "Site reference"},
            {"name": "enrollment_over_time_level", "type": "VARCHAR", "description": "Enrollment level"},
            {"name": "period_frequency", "type": "VARCHAR", "description": "Reporting frequency"}
        ],
    },

    "nmrf": {
        "business_purpose": "New Material Request Form tracking including BOM status, label material status, and creation dates for new material onboarding",
        "keywords": ["NMRF", "new material", "request", "BOM", "label", "onboarding"],
        "sample_queries": ["NMRF status", "New material requests", "Material onboarding status"],
        "related_entities": ["material_number", "ly_number"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "material_number", "type": "VARCHAR", "description": "Material identifier"},
            {"name": "bom_status", "type": "VARCHAR", "description": "Bill of materials status"},
            {"name": "label_material_status", "type": "VARCHAR", "description": "Label material status"},
            {"name": "ly_number", "type": "VARCHAR", "description": "LY reference number"},
            {"name": "created_date", "type": "VARCHAR", "description": "Creation date"}
        ],
    },

    "order_phases": {
        "business_purpose": "Order processing phases and operations showing workflow stages, operation descriptions, and plant assignments",
        "keywords": ["order", "phase", "operation", "workflow", "stage", "processing"],
        "sample_queries": ["Order phases", "Processing stages", "Order operations"],
        "related_entities": ["trial_alias", "order_num", "operation"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "order_num", "type": "VARCHAR", "description": "Order number"},
            {"name": "operation_num", "type": "INTEGER", "description": "Operation sequence number"},
            {"name": "operation_description", "type": "VARCHAR", "description": "Operation description"},
            {"name": "plant_id", "type": "VARCHAR", "description": "Plant identifier"}
        ],
    },

    "outstanding_site_shipment_status_report": {
        "business_purpose": "Outstanding and pending shipments to clinical sites showing shipment status, country, and package details for delivery tracking",
        "keywords": ["outstanding", "pending", "shipment", "site", "delivery", "waiting", "in-transit"],
        "sample_queries": ["Outstanding shipments", "Pending deliveries", "What shipments are pending?"],
        "related_entities": ["trial_alias", "site_number", "shipment", "country"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "site_number", "type": "VARCHAR", "description": "Clinical site number"},
            {"name": "country", "type": "VARCHAR", "description": "Country location"},
            {"name": "shipment_#", "type": "VARCHAR", "description": "Shipment number"},
            {"name": "package_description", "type": "VARCHAR", "description": "Package description"}
        ],
    },

    "patient_status_and_treatment_report": {
        "business_purpose": "Patient visit and treatment status by trial, country, and site for clinical operations tracking",
        "keywords": ["patient", "treatment", "visit", "status", "clinical", "site"],
        "sample_queries": ["Patient status", "Treatment visits", "Patient visit report"],
        "related_entities": ["trial_alias", "country", "site", "patient"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "country", "type": "VARCHAR", "description": "Country location"},
            {"name": "site", "type": "VARCHAR", "description": "Clinical site"},
            {"name": "visit", "type": "VARCHAR", "description": "Visit identifier"},
            {"name": "visit_date", "type": "VARCHAR", "description": "Date of visit"}
        ],
    },

    "planned_order_recipe": {
        "business_purpose": "Planned order recipes showing manufacturing phases, durations, and recipe configurations for production planning",
        "keywords": ["planned", "order", "recipe", "manufacturing", "phase", "production"],
        "sample_queries": ["Planned order recipes", "Manufacturing recipes", "Production phases"],
        "related_entities": ["recipe", "phase"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "recipe_group", "type": "VARCHAR", "description": "Recipe group"},
            {"name": "recipe", "type": "VARCHAR", "description": "Recipe identifier"},
            {"name": "recipe_days", "type": "INTEGER", "description": "Recipe duration in days"},
            {"name": "phase", "type": "VARCHAR", "description": "Manufacturing phase"},
            {"name": "phase_text", "type": "VARCHAR", "description": "Phase description"}
        ],
    },

    "planned_orders": {
        "business_purpose": "Planned orders for materials showing availability dates, stock categories, and country requirements for supply planning",
        "keywords": ["planned", "order", "forecast", "requirement", "stock", "availability"],
        "sample_queries": ["Planned orders", "Future orders", "Order forecast"],
        "related_entities": ["order", "country", "material"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "availability_date_or_requirements_date", "type": "VARCHAR", "description": "Required date"},
            {"name": "category_of_stock/receipt/requirement/forecast", "type": "VARCHAR", "description": "Stock category"},
            {"name": "category_type", "type": "VARCHAR", "description": "Category type"},
            {"name": "counter", "type": "INTEGER", "description": "Counter"},
            {"name": "country/reg", "type": "VARCHAR", "description": "Country or region"}
        ],
    },

    "purchase_order_kpi": {
        "business_purpose": "Purchase order KPIs including quantity changes, document dates, and material tracking for procurement performance",
        "keywords": ["purchase", "order", "KPI", "procurement", "quantity", "performance"],
        "sample_queries": ["Purchase order KPIs", "Procurement metrics", "PO performance"],
        "related_entities": ["purchase_order", "material"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "old_qty", "type": "INTEGER", "description": "Previous quantity"},
            {"name": "new_qty", "type": "INTEGER", "description": "New quantity"},
            {"name": "purchase_document_date", "type": "VARCHAR", "description": "Document date"},
            {"name": "purchasing_document_type", "type": "VARCHAR", "description": "Document type"},
            {"name": "material", "type": "VARCHAR", "description": "Material identifier"}
        ],
    },

    "purchase_order_quantities": {
        "business_purpose": "Purchase order quantities by country, calendar period, and currency for procurement analysis and reporting",
        "keywords": ["purchase", "order", "quantity", "procurement", "country", "calendar"],
        "sample_queries": ["Purchase quantities", "Order volumes", "Procurement by country"],
        "related_entities": ["country", "purchase_order"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "base_unit_of_measure", "type": "VARCHAR", "description": "Unit of measure"},
            {"name": "calendar_month", "type": "INTEGER", "description": "Calendar month"},
            {"name": "calendar_week", "type": "INTEGER", "description": "Calendar week"},
            {"name": "country", "type": "VARCHAR", "description": "Country"},
            {"name": "currency_gr_value_pstg_date", "type": "DECIMAL", "description": "Currency value"}
        ],
    },

    "purchase_requirement": {
        "business_purpose": "Purchase requirements and requisitions including delivery dates, materials, and MRP controller assignments for procurement planning",
        "keywords": ["purchase", "requirement", "requisition", "procurement", "delivery", "MRP"],
        "sample_queries": ["Purchase requirements", "What needs to be purchased?", "Procurement needs"],
        "related_entities": ["material", "purchase_requisition"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "actual_delivery_date", "type": "VARCHAR", "description": "Actual delivery date"},
            {"name": "item_number_of_purchase_requisition", "type": "INTEGER", "description": "Requisition item number"},
            {"name": "item_number_of_purchasing_document", "type": "INTEGER", "description": "PO item number"},
            {"name": "material", "type": "VARCHAR", "description": "Material identifier"},
            {"name": "mrp_controller", "type": "VARCHAR", "description": "MRP controller"}
        ],
    },

    "qdocs": {
        "business_purpose": "Quality documents linking materials to documentation including titles, descriptions, and LY references for quality management",
        "keywords": ["quality", "document", "QA", "documentation", "material"],
        "sample_queries": ["Quality documents", "QA documentation", "Material quality docs"],
        "related_entities": ["material", "ly_number"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "title", "type": "VARCHAR", "description": "Document title"},
            {"name": "material_name", "type": "VARCHAR", "description": "Material name"},
            {"name": "material_description", "type": "VARCHAR", "description": "Material description"},
            {"name": "ly_id", "type": "VARCHAR", "description": "LY identifier"},
            {"name": "ly_number", "type": "VARCHAR", "description": "LY number"}
        ],
    },

    "re_evaluation": {
        "business_purpose": "Re-evaluation and shelf-life extension records showing request types, sample status, batch/lot numbers, and extension history for stability and expiry management",
        "keywords": ["re-evaluation", "reevaluation", "extension", "shelf-life", "expiry", "stability", "batch", "lot", "extend", "prior"],
        "sample_queries": ["Has this batch been re-evaluated?", "Shelf-life extension history", "Prior re-evaluations", "Can we extend this batch?", "Extension requests"],
        "related_entities": ["lot_number", "batch", "extension", "expiry"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "id", "type": "VARCHAR", "description": "Re-evaluation record ID"},
            {"name": "created", "type": "VARCHAR", "description": "Creation date"},
            {"name": "request_type_molecule_planner_to_complete", "type": "VARCHAR", "description": "Request type (Extension, etc.)"},
            {"name": "sample_status_ndp_material_coordinator_to_complete", "type": "VARCHAR", "description": "Sample status"},
            {"name": "ly_number_molecule_planner_to_complete", "type": "VARCHAR", "description": "LY number reference"}
        ],
    },

    "rim": {
        "business_purpose": "Regulatory Information Management records including health authority submissions, document types, and approval status for regulatory compliance",
        "keywords": ["regulatory", "RIM", "health authority", "submission", "approval", "compliance", "FDA", "EMA"],
        "sample_queries": ["Regulatory submissions", "Health authority status", "RIM records"],
        "related_entities": ["health_authority", "submission", "status"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "name_v", "type": "VARCHAR", "description": "Document name"},
            {"name": "filename_v", "type": "VARCHAR", "description": "File name"},
            {"name": "health_authority_division_c", "type": "VARCHAR", "description": "Health authority division"},
            {"name": "type_v", "type": "VARCHAR", "description": "Document type"},
            {"name": "status_v", "type": "VARCHAR", "description": "Submission status"}
        ],
    },

    "shipment_status_report": {
        "business_purpose": "Shipment status tracking including LPN status, package counts, and delivery status for logistics visibility",
        "keywords": ["shipment", "status", "delivery", "LPN", "package", "tracking", "shipped", "delivered"],
        "sample_queries": ["Shipment status", "Where is my shipment?", "Delivery status", "Package tracking"],
        "related_entities": ["shipment", "lpn", "status"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "status", "type": "VARCHAR", "description": "Shipment status"},
            {"name": "shipment", "type": "VARCHAR", "description": "Shipment number"},
            {"name": "lpn#", "type": "VARCHAR", "description": "License plate number"},
            {"name": "lpn_status", "type": "VARCHAR", "description": "LPN status"},
            {"name": "package_count", "type": "INTEGER", "description": "Number of packages"}
        ],
    },

    "shipment_summary_report": {
        "business_purpose": "Shipment summary by order, trial, and destination including site numbers and country codes for logistics reporting",
        "keywords": ["shipment", "summary", "order", "destination", "site", "country"],
        "sample_queries": ["Shipment summary", "Shipments by trial", "Delivery summary"],
        "related_entities": ["order_number", "trial_alias", "site_number", "country"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "order_number", "type": "VARCHAR", "description": "Order number"},
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "iwrs_number", "type": "VARCHAR", "description": "IWRS reference"},
            {"name": "site_number", "type": "VARCHAR", "description": "Destination site"},
            {"name": "ship_to_country_code", "type": "VARCHAR", "description": "Destination country code"}
        ],
    },

    "study_level_enrollment_report": {
        "business_purpose": "Study-level enrollment aggregates showing forecast, planned, and actual enrollment totals for trial-wide demand planning",
        "keywords": ["study", "enrollment", "trial", "forecast", "planned", "actual", "total", "participants"],
        "sample_queries": ["Study enrollment totals", "Trial enrollment", "How many patients enrolled?"],
        "related_entities": ["trial_alias", "enrollment"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "enrollment_level", "type": "VARCHAR", "description": "Aggregation level"},
            {"name": "total_enrolled_forecast", "type": "INTEGER", "description": "Forecasted enrollment"},
            {"name": "total_enrolled_planned", "type": "INTEGER", "description": "Planned enrollment"},
            {"name": "total_enrolled_actual", "type": "INTEGER", "description": "Actual enrollment"}
        ],
    },

    "warehouse_and_site_shipment_tracking_report": {
        "business_purpose": "Comprehensive shipment tracking from warehouse to site including quantities, carriers, and country destinations for end-to-end logistics visibility",
        "keywords": ["warehouse", "site", "shipment", "tracking", "carrier", "delivery", "logistics"],
        "sample_queries": ["Shipment tracking", "Warehouse to site shipments", "Carrier tracking"],
        "related_entities": ["order_number", "trial_alias", "country_name", "carrier"],
        "workflow": ["A", "B"],
        "key_columns": [
            {"name": "order_number", "type": "VARCHAR", "description": "Order number"},
            {"name": "trial_alias", "type": "VARCHAR", "description": "Trial identifier"},
            {"name": "country_name", "type": "VARCHAR", "description": "Destination country"},
            {"name": "actual_qty", "type": "INTEGER", "description": "Actual quantity shipped"},
            {"name": "carrier_code", "type": "VARCHAR", "description": "Carrier identifier"}
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
        ""
    ]
    
    # Add keywords if available
    if schema.get('keywords'):
        output.append(f"Keywords: {', '.join(schema['keywords'])}")
        output.append("")
    
    output.append("Key Columns:")
    for col in schema['key_columns']:
        output.append(f"  - {col['name']} ({col['type']}): {col['description']}")
    
    return "\n".join(output)
