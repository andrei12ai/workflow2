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

    # Enhanced Graph Visualization - Initializing Pyvis Network
    net = Network(height="1000px", width="100%", bgcolor="#222222", font_color="white", directed = True)
    
    # PASS 1: Add all nodes
    for step in dsl_data['Steps']:
        step_type = step["StepType"].split(",")[0].split(".")[-1]
        color = type_colors.get(step_type, "#a6cee3")
        title = f"{step['Id']}"
        shape = "box"
        net.add_node(step["Id"], label=step["Name"], color=color, title=title, shape=shape, mass=10)

    # PASS 2: Add edges only after all nodes have been added
    for step in dsl_data['Steps']:
        # Check if the NextStepId exists before adding the edge
        next_step_id = step.get("NextStepId")
        if next_step_id and next_step_id in valid_step_ids:
            net.add_edge(step["Id"], next_step_id, arrowStrikethrough = False, value = 2)
        elif next_step_id:
            missing_nodes.append(next_step_id)
        
        # Add conditional edges if available
        if "SelectNextStep" in step:
            for conditional_step_id, condition in step["SelectNextStep"].items():
                if conditional_step_id in valid_step_ids:
                    net.add_edge(step["Id"], conditional_step_id, title=condition, color="#ffa500", dash=True, value = 2)
                else:
                    missing_nodes.append(conditional_step_id)

    # Display warnings if there are missing nodes
    if missing_nodes:
        st.warning(f"Warning: The following steps are referenced but not defined in the workflow: {set(missing_nodes)}")

    # Generate the HTML visualization
    try:
        html_content = net.generate_html()  # Directly generate HTML without saving to file
        st.components.v1.html(html_content, height=750, scrolling=True)  # Display in Streamlit
    except Exception as e:
        st.error(f"An error occurred while generating the visualization: {e}")

    # Display step-by-step information in the Streamlit app
    for step in dsl_data['Steps']:
        step_type = step["StepType"].split(",")[0].split(".")[-1]
        color = type_colors.get(step_type, "#a6cee3")
        
        # Display step information in a main expandable section
        st.write(1. )
        with st.expander(f"**{step['Name']}**", expanded=False, icon="fire"):
            st.markdown(f"<span style='color: {color}; font-weight: bold;'>Step Type:</span> {step_type}", unsafe_allow_html=True)
            st.write(f"**Next Step**: {step_id_to_name.get(step.get('NextStepId', ''), 'see Conditional Transitions tab')}")
            
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
