import json
import streamlit as st
from pyvis.network import Network

# Streamlit UI Header
st.title("Enhanced Workflow Analyzer and Visualizer")
st.write("Upload a DSL JSON file to analyze and visualize the workflow.")

# File Upload
uploaded_file = st.file_uploader("Choose a DSL JSON file", type="json")

if uploaded_file is not None:
    # Load and parse the JSON data
    dsl_data = json.load(uploaded_file)

    # Display workflow metadata with expandable sections
    st.subheader("Workflow Details")
    with st.expander("Workflow Metadata", expanded=True):
        st.write(f"**Workflow ID:** {dsl_data['Id']}")
        st.write(f"**Version:** {dsl_data['Version']}")
        st.write(f"**Release Version:** {dsl_data['ReleaseVersion']}")
        st.write(f"**Data Type:** {dsl_data['DataType']}")

    # Analysis of Workflow Steps
    st.subheader("Workflow Steps Analysis")
    
    # Map Step IDs to names for easier reference
    step_id_to_name = {step['Id']: step['Name'] for step in dsl_data['Steps']}
    
    # Define colors for step types
    type_colors = {
        "ApiCallerStep": "#1f78b4",
        "ContextConfiguratorStep": "#33a02c",
        "DecideStep": "#ff7f00",
        "MessageSenderStep": "#e31a1c"
    }
    
    # Initialize a set of valid step IDs to check for missing nodes
    valid_step_ids = set(step['Id'] for step in dsl_data['Steps'])
    missing_nodes = []

    # Loop through each step and display its details
    for step in dsl_data['Steps']:
        step_type = step["StepType"].split(".")[-1]
        color = type_colors.get(step_type, "#a6cee3")
        
        # Display step information in a main expandable section
        with st.expander(f"{step['Name']} (Type: {step_type})", expanded=False):
            st.markdown(f"<span style='color: {color}; font-weight: bold;'>Step Type:</span> {step_type}", unsafe_allow_html=True)
            st.write(f"**Next Step**: {step_id_to_name.get(step.get('NextStepId', ''), 'End of Workflow')}")
            
            # Use tabs instead of nested expanders for Inputs, Outputs, and Conditional Transitions
            tabs = st.tabs(["Inputs", "Outputs", "Conditional Transitions"])
            
            # Inputs tab
            with tabs[0]:
                st.json(step.get("Inputs", {}))
            
            # Outputs tab
            with tabs[1]:
                st.json(step.get("Outputs", {}))
            
            # Conditional Transitions tab
            with tabs[2]:
                if "SelectNextStep" in step:
                    for next_step_id, condition_expr in step["SelectNextStep"].items():
                        next_step_name = step_id_to_name.get(next_step_id, "Unknown")
                        st.write(f" - **Next Step:** {next_step_name} ({next_step_id}), **Condition:** `{condition_expr}`")
                else:
                    st.write("No conditional transitions.")

    # Enhanced Graph Visualization
    st.subheader("Workflow Graph Visualization")
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
    
    # Add nodes and edges with tooltips
    for step in dsl_data['Steps']:
        step_type = step["StepType"].split(".")[-1]
        color = type_colors.get(step_type, "#a6cee3")
        title = f"<b>{step['Name']}</b><br>Type: {step_type}<br>Operation: {step.get('Inputs', {}).get('OperationName', 'N/A')}"
        net.add_node(step["Id"], label=step["Name"], color=color, title=title)
        
        # Check if the NextStepId exists before adding the edge
        next_step_id = step.get("NextStepId")
        if next_step_id and next_step_id in valid_step_ids:
            net.add_edge(step["Id"], next_step_id)
        elif next_step_id:
            missing_nodes.append(next_step_id)
        
        # Add conditional edges if available
        if "SelectNextStep" in step:
            for conditional_step_id, condition in step["SelectNextStep"].items():
                if conditional_step_id in valid_step_ids:
                    net.add_edge(step["Id"], conditional_step_id, title=condition, color="#ffa500", dash=True)
                else:
                    missing_nodes.append(conditional_step_id)

    # Display warnings if there are missing nodes
    if missing_nodes:
        st.warning(f"Warning: The following steps are referenced but not defined in the workflow: {set(missing_nodes)}")

    # Display the interactive network in Streamlit
    net.show("workflow_visualization.html")
    st.components.v1.html(open("workflow_visualization.html", "r").read(), height=750, scrolling=True)
