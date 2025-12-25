"""
Clinical Supply Chain Control Tower - Streamlit Application

Main application with two interfaces:
1. Monitoring Dashboard (Workflow A)
2. Conversational Assistant (Workflow B)
"""
import streamlit as st
import logging
from datetime import datetime
import json
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Page configuration
st.set_page_config(
    page_title="Clinical Supply Chain Control Tower",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .critical {
        color: #dc3545;
        font-weight: bold;
    }
    .high {
        color: #fd7e14;
        font-weight: bold;
    }
    .medium {
        color: #ffc107;
        font-weight: bold;
    }
    .success {
        color: #28a745;
        font-weight: bold;
    }
    .citation {
        font-size: 0.85rem;
        color: #6c757d;
        font-style: italic;
        margin-top: 0.5rem;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    
    # Sidebar navigation
    st.sidebar.markdown("# 🏥 Clinical Supply Chain")
    st.sidebar.markdown("### Control Tower")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Select Workflow",
        ["🏠 Home", "📊 Monitoring Dashboard", "💬 Conversational Assistant"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This system automates risk detection and assists managers "
        "in making complex supply chain decisions for clinical trials."
    )
    
    # Route to appropriate page
    if page == "🏠 Home":
        show_home_page()
    elif page == "📊 Monitoring Dashboard":
        show_monitoring_dashboard()
    elif page == "💬 Conversational Assistant":
        show_conversational_assistant()


def show_home_page():
    """Display home page with system overview."""
    st.markdown('<div class="main-header">Clinical Supply Chain Control Tower</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to the Agentic AI System for Pharmaceutical Supply Chain Management
    
    This system helps manage complex clinical trials across 50+ countries by automating 
    risk detection and providing intelligent decision support.
    """)
    
    # Two columns for workflows
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Workflow A: Supply Watchdog")
        st.markdown("""
        **Autonomous Monitoring System**
        
        Automatically identifies:
        - 🔴 Expiring batches (≤90 days)
        - 📉 Predicted stock shortfalls
        - ⚠️ Critical supply risks
        
        **Output**: Structured JSON alerts for email notifications
        """)
        
        if st.button("Go to Monitoring Dashboard", key="home_workflow_a"):
            st.session_state.page = "📊 Monitoring Dashboard"
            st.rerun()
    
    with col2:
        st.markdown("### 💬 Workflow B: Scenario Strategist")
        st.markdown("""
        **Conversational Decision Support**
        
        Answers queries like:
        - 🔄 Can we extend batch expiry?
        - 📦 What's the current stock level?
        - 📈 Predict demand for next 8 weeks
        - ✅ Check regulatory approvals
        
        **Output**: Natural language responses with data citations
        """)
        
        if st.button("Go to Conversational Assistant", key="home_workflow_b"):
            st.session_state.page = "💬 Conversational Assistant"
            st.rerun()
    
    # System architecture
    st.markdown("---")
    st.markdown("### 🏗️ System Architecture")
    
    st.markdown("""
    **Multi-Agent Architecture** with 8 specialized agents:
    1. **Router Agent** - Workflow classification
    2. **Schema Retrieval Agent** - Context management
    3. **SQL Generation Agent** - Self-healing queries
    4. **Inventory Agent** - Stock & expiry management
    5. **Demand Forecasting Agent** - Enrollment analysis
    6. **Regulatory Agent** - Compliance verification
    7. **Logistics Agent** - Shipping feasibility
    8. **Synthesis Agent** - Response formatting
    """)
    
    # Key features
    st.markdown("### ✨ Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🎯 Zero Hallucinations**
        - All responses grounded in database queries
        - Data citations for every answer
        """)
    
    with col2:
        st.markdown("""
        **🔄 Self-Healing SQL**
        - Automatic error correction
        - 3-attempt retry logic
        """)
    
    with col3:
        st.markdown("""
        **🤖 Explainable AI**
        - Clear reasoning for decisions
        - Source table citations
        """)


def show_monitoring_dashboard():
    """Display Workflow A: Monitoring Dashboard."""
    st.markdown('<div class="main-header">📊 Supply Watchdog - Monitoring Dashboard</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    Autonomous monitoring system that identifies expiring batches and predicts stock shortfalls.
    """)
    
    # Control buttons
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("🔄 Run Supply Watchdog", type="primary", use_container_width=True):
            run_supply_watchdog()
    
    with col2:
        if st.button("📥 Export JSON", use_container_width=True):
            export_json_results()
    
    with col3:
        if st.button("🔍 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Display results if available
    if "workflow_a_result" in st.session_state:
        display_workflow_a_results(st.session_state.workflow_a_result)
    else:
        st.info("👆 Click 'Run Supply Watchdog' to execute autonomous monitoring")
        
        # Show example output
        with st.expander("📋 Example Output Structure"):
            st.json({
                "alert_date": "2025-12-24",
                "risk_summary": {
                    "total_expiring_batches": 15,
                    "total_shortfall_predictions": 3
                },
                "expiry_alerts": [
                    {
                        "severity": "CRITICAL",
                        "batch_id": "LOT-14364098",
                        "material": "Dog Patch",
                        "location": "Taiwan",
                        "expiry_date": "2026-01-15",
                        "days_remaining": 22,
                        "quantity": 100,
                        "unit": "packages"
                    }
                ],
                "shortfall_predictions": [
                    {
                        "country": "Germany",
                        "material": "CT-2004-PSX",
                        "current_stock": 50,
                        "projected_8week_demand": 80,
                        "shortfall": 30,
                        "estimated_stockout_date": "2026-02-10"
                    }
                ]
            })


def run_supply_watchdog():
    """Execute Workflow A and store results."""
    with st.spinner("🔄 Running Supply Watchdog... This may take a few moments."):
        try:
            # Force fresh orchestrator instance to pick up code changes
            import src.workflows.orchestrator as orch_module
            orch_module._orchestrator_instance = None
            
            from src.workflows import get_orchestrator
            orchestrator = get_orchestrator()
            result = orchestrator.run_supply_watchdog(trigger_type="manual")
            
            st.session_state.workflow_a_result = result
            st.session_state.workflow_a_timestamp = datetime.now()
            
            if result.get("success"):
                st.success("✅ Supply Watchdog completed successfully!")
                
                # Send email alert if configured
                try:
                    from src.services.email_service import send_watchdog_alert
                    import os
                    
                    if os.getenv("RESEND_API_KEY") and os.getenv("ALERT_EMAIL_TO"):
                        email_result = send_watchdog_alert(result)
                        if email_result.get("success"):
                            st.success(f"📧 Email alert sent to {email_result.get('to')}")
                        else:
                            st.warning(f"📧 Email not sent: {email_result.get('error', 'Unknown error')}")
                except Exception as email_error:
                    st.warning(f"📧 Email service error: {str(email_error)}")
            else:
                st.error(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            st.error(f"❌ Error executing workflow: {str(e)}")
            st.exception(e)


def display_workflow_a_results(result: dict):
    """Display Workflow A results."""
    if not result.get("success"):
        st.error(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
        return
    
    # Summary cards
    st.markdown('<div class="sub-header">📈 Risk Summary</div>', unsafe_allow_html=True)
    
    summary = result.get("summary", {})
    output = result.get("output", {})
    risk_summary = output.get("risk_summary", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Expiring Batches",
            risk_summary.get("total_expiring_batches", 0),
            delta=None
        )
    
    with col2:
        st.metric(
            "Critical Batches",
            summary.get("critical_batches", 0),
            delta=None,
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "Predicted Shortfalls",
            risk_summary.get("total_shortfall_predictions", 0),
            delta=None,
            delta_color="inverse"
        )
    
    with col4:
        # Overall risk indicator
        critical = summary.get("critical_batches", 0)
        shortfalls = risk_summary.get("total_shortfall_predictions", 0)
        
        if critical > 5 or shortfalls > 3:
            risk_level = "🔴 HIGH"
            risk_color = "critical"
        elif critical > 0 or shortfalls > 0:
            risk_level = "🟠 MEDIUM"
            risk_color = "high"
        else:
            risk_level = "🟢 LOW"
            risk_color = "success"
        
        st.markdown(f"**Risk Level**")
        st.markdown(f'<div class="{risk_color}">{risk_level}</div>', unsafe_allow_html=True)
    
    # Expiry Alerts Table
    st.markdown('<div class="sub-header">⚠️ Expiry Alerts</div>', unsafe_allow_html=True)
    
    expiry_alerts = output.get("expiry_alerts", [])
    
    if expiry_alerts:
        # Filter by severity
        severity_filter = st.multiselect(
            "Filter by Severity",
            ["CRITICAL", "HIGH", "MEDIUM"],
            default=["CRITICAL", "HIGH", "MEDIUM"]
        )
        
        filtered_alerts = [a for a in expiry_alerts if a.get("severity") in severity_filter]
        
        # Display as table
        import pandas as pd
        df_alerts = pd.DataFrame(filtered_alerts)
        
        # Style the dataframe
        def highlight_severity(row):
            if row['severity'] == 'CRITICAL':
                return ['background-color: #ffcccc'] * len(row)
            elif row['severity'] == 'HIGH':
                return ['background-color: #ffe6cc'] * len(row)
            else:
                return ['background-color: #fff9cc'] * len(row)
        
        if not df_alerts.empty:
            styled_df = df_alerts.style.apply(highlight_severity, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)
        else:
            st.info("No expiry alerts matching the selected filters.")
    else:
        st.success("✅ No batches expiring within 90 days!")
    
    # Shortfall Predictions Table
    st.markdown('<div class="sub-header">📉 Shortfall Predictions</div>', unsafe_allow_html=True)
    
    shortfall_predictions = output.get("shortfall_predictions", [])
    
    if shortfall_predictions:
        import pandas as pd
        df_shortfalls = pd.DataFrame(shortfall_predictions)
        
        st.dataframe(df_shortfalls, use_container_width=True, height=300)
    else:
        st.success("✅ No shortfalls predicted for the next 8 weeks!")
    
    # Citations
    with st.expander("📚 Data Sources & Citations"):
        citations = result.get("citations", [])
        if citations:
            for i, citation in enumerate(citations, 1):
                st.markdown(f"**Source {i}:**")
                st.json(citation)
        else:
            st.info("No citations available")
    
    # Execution metadata
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"⏰ Executed: {result.get('execution_time', 'N/A')}")
    with col2:
        st.caption(f"🔄 Trigger: {result.get('trigger_type', 'manual')}")


def export_json_results():
    """Export Workflow A results as JSON."""
    if "workflow_a_result" not in st.session_state:
        st.warning("⚠️ No results to export. Run Supply Watchdog first.")
        return
    
    result = st.session_state.workflow_a_result
    json_string = result.get("json_string", json.dumps(result.get("output", {}), indent=2))
    
    st.download_button(
        label="📥 Download JSON",
        data=json_string,
        file_name=f"supply_watchdog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )


def show_conversational_assistant():
    """Display Workflow B: Conversational Assistant."""
    st.markdown('<div class="main-header">💬 Scenario Strategist - Conversational Assistant</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    Ask questions about inventory, demand, regulatory approvals, and logistics. 
    The system will provide data-backed answers with citations.
    """)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Example queries
    with st.expander("💡 Example Queries"):
        st.markdown("""
        **Shelf-Life Extension:**
        - Can we extend the expiry of Batch LOT-14364098 for Germany?
        - Has Batch LOT-59019698 been re-evaluated before?
        
        **Inventory:**
        - What is the current stock level for Material MAT-93657?
        - Show me all batches expiring in Taiwan within 60 days
        
        **Demand & Forecasting:**
        - Predict demand for Trial CT-2004-PSX for next 8 weeks
        - What is the enrollment rate for Zimbabwe?
        
        **Regulatory:**
        - Is shelf-life extension approved in Germany?
        - Check regulatory status for Trial CT-6910-RDE
        
        **Logistics:**
        - What is the shipping time to Germany?
        - Can we ship Batch LOT-14364098 before it expires?
        """)
    
    # Chat interface
    st.markdown("---")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            if message["role"] == "assistant" and "citations" in message:
                with st.expander("📚 Data Sources"):
                    for citation in message["citations"]:
                        st.caption(f"• {citation.get('table', 'Unknown table')}")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about the supply chain..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                response = process_conversational_query(prompt)
                
                st.markdown(response["content"])
                
                if response.get("citations"):
                    with st.expander("📚 Data Sources"):
                        for citation in response["citations"]:
                            st.caption(f"• {citation.get('table', 'Unknown table')}")
        
        # Add assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["content"],
            "citations": response.get("citations", [])
        })
    
    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            st.rerun()


def process_conversational_query(query: str) -> dict:
    """Process user query through Workflow B."""
    try:
        # Force fresh orchestrator instance to pick up code changes
        import src.workflows.orchestrator as orch_module
        orch_module._orchestrator_instance = None
        
        from src.workflows import get_orchestrator
        orchestrator = get_orchestrator()
        result = orchestrator.run_scenario_strategist(query)
        
        if result.get("success"):
            return {
                "content": result.get("response", "No response generated"),
                "citations": result.get("citations", [])
            }
        else:
            return {
                "content": f"❌ Error: {result.get('error', 'Unknown error')}",
                "citations": []
            }
    
    except Exception as e:
        return {
            "content": f"❌ Error processing query: {str(e)}",
            "citations": []
        }


if __name__ == "__main__":
    main()
