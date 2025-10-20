import json
import os
import re
import importlib
import logging
from typing import Dict, Any, List, TypedDict
from datetime import datetime
from langgraph.graph import StateGraph, END


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ==============================================================================
# LANGGRAPH STATE DEFINITION
# ==============================================================================

class WorkflowState(TypedDict, total=False):
    """
    Shared state across all nodes in the LangGraph workflow.
    Each agent reads from and writes to this state.
    """
    # Raw inputs
    icp: Dict[str, Any]
    signals: List[str]
    
    # Step outputs
    leads: List[Dict[str, Any]]
    enriched_leads: List[Dict[str, Any]]
    ranked_leads: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]
    sent_status: List[Dict[str, Any]]
    responses: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    
    # Metadata
    step_count: int
    errors: List[str]


# ==============================================================================
# STEP 1: Load and Parse Workflow
# ==============================================================================

def load_workflow(workflow_path: str = "workflow.json") -> Dict[str, Any]:
    """
    Load and parse the workflow.json file.
    
    Args:
        workflow_path (str): Path to the workflow JSON file
        
    Returns:
        dict: Parsed workflow configuration
    """
    logger.info("=" * 80)
    logger.info("Loading Workflow Configuration")
    logger.info("=" * 80)
    
    if not os.path.exists(workflow_path):
        logger.error(f"Workflow file not found: {workflow_path}")
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
    
    try:
        with open(workflow_path, 'r') as file:
            workflow = json.load(file)
        
        logger.info(f"Successfully loaded: {workflow_path}")
        logger.info(f"Workflow Name: {workflow.get('workflow_name', 'Unnamed')}")
        logger.info(f"Description: {workflow.get('description', 'No description')}")
        logger.info(f"Total Steps: {len(workflow.get('steps', []))}")
        
        return workflow
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        raise


def validate_workflow(workflow: Dict[str, Any]) -> bool:
    """
    Validate that the workflow has required fields.
    
    Args:
        workflow (dict): Workflow configuration
        
    Returns:
        bool: True if valid
    """
    logger.info("=" * 80)
    logger.info("Validating Workflow Structure")
    logger.info("=" * 80)
    
    required_fields = ['workflow_name', 'steps']
    
    for field in required_fields:
        if field not in workflow:
            logger.error(f"Missing required field: {field}")
            raise ValueError(f"Missing required field: {field}")
        logger.debug(f"Found required field: {field}")
    
    steps = workflow['steps']
    if not isinstance(steps, list) or len(steps) == 0:
        logger.error("Workflow must have at least one step")
        raise ValueError("Workflow must have at least one step")
    
    logger.info(f"Workflow contains {len(steps)} step(s)")
    
    logger.info("Validating Individual Steps:")
    for i, step in enumerate(steps, 1):
        step_id = step.get('id', f'step_{i}')
        logger.info(f"  Step {i}: {step_id}")
        
        required_step_fields = ['id', 'agent', 'inputs', 'instructions']
        for field in required_step_fields:
            if field not in step:
                logger.error(f"Step '{step_id}' missing field: {field}")
                raise ValueError(f"Step '{step_id}' missing field: {field}")
            logger.debug(f"    - {field}: present")
    
    logger.info("All validations passed successfully")
    return True


# ==============================================================================
# STEP 2: Dynamic Agent Loading
# ==============================================================================

def load_agent_class(agent_name: str):
    """
    Dynamically import and return an agent class.
    
    Args:
        agent_name (str): Name of the agent class (e.g., "ProspectSearchAgent")
        
    Returns:
        class: The agent class
        
    Example:
        Agent file location: agents/prospect_search_agent.py
        Class name: ProspectSearchAgent
    """
    logger.debug(f"Loading agent: {agent_name}")
    
    try:
        # Convert class name to module name
        # ProspectSearchAgent -> prospect_search_agent
        module_name = re.sub(r'(?<!^)(?=[A-Z])', '_', agent_name).lower()
        
        # Import from agents package
        module_path = f"agents.{module_name}"
        
        logger.debug(f"  Importing from: {module_path}")
        
        module = importlib.import_module(module_path)
        agent_class = getattr(module, agent_name)
        
        logger.info(f"  Successfully loaded agent: {agent_name}")
        
        return agent_class
        
    except ModuleNotFoundError as e:
        logger.error(f"Module not found: {module_path}")
        logger.error(f"Expected file location: agents/{module_name}.py")
        raise Exception(f"Could not load agent class '{agent_name}': {e}")
    except AttributeError as e:
        logger.error(f"Class {agent_name} not found in module {module_path}")
        raise Exception(f"Could not load agent class '{agent_name}': {e}")


# ==============================================================================
# STEP 3: Create Node Functions for LangGraph
# ==============================================================================

def create_node_function(step_config: Dict[str, Any], agent_class):
    """
    Create a LangGraph node function that wraps an agent.
    
    Args:
        step_config: Step configuration from workflow.json
        agent_class: The agent class to instantiate
        
    Returns:
        function: A node function compatible with LangGraph
    """
    step_id = step_config['id']
    agent_name = step_config['agent']
    
    def node_function(state: WorkflowState) -> WorkflowState:
        """
        Node function executed by LangGraph.
        Reads from state, runs agent, writes back to state.
        """
        logger.info("-" * 80)
        logger.info(f"Executing Node: {step_id}")
        logger.info("-" * 80)
        
        start_time = datetime.now()
        
        try:
            # Create agent instance
            agent_config = {
                'tools': step_config.get('tools', []),
                'instructions': step_config.get('instructions', ''),
                'output_schema': step_config.get('output_schema', {})
            }
            agent_instance = agent_class(agent_id=step_id, config=agent_config)
            
            # Prepare inputs from state
            inputs = prepare_inputs_from_state(step_config['inputs'], state)
            
            logger.info(f"  Running agent: {agent_name}")
            
            # Execute agent
            output = agent_instance.run(inputs)
            
            # Update state with output
            state = update_state_with_output(state, step_id, output)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"  Node {step_id} completed in {duration:.2f}s")
            
            # Increment step counter
            state['step_count'] = state.get('step_count', 0) + 1
            
            return state
            
        except Exception as e:
            logger.error(f"Error in node {step_id}: {str(e)}", exc_info=True)
            
            # Track error in state
            if 'errors' not in state:
                state['errors'] = []
            state['errors'].append(f"{step_id}: {str(e)}")
            
            raise
    
    # Set function name for debugging
    node_function.__name__ = f"{step_id}_node"
    
    return node_function


def prepare_inputs_from_state(input_config: Dict[str, Any], state: WorkflowState) -> Dict[str, Any]:
    """
    Prepare agent inputs by resolving references to state variables.
    
    Args:
        input_config: Input configuration with potential state references
        state: Current workflow state
        
    Returns:
        dict: Resolved inputs ready for agent
    """
    resolved_inputs = {}
    
    for key, value in input_config.items():
        if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            # Extract state variable name
            # {{prospect_search.output.leads}} -> extract 'leads' from state
            state_key = extract_state_key(value)
            
            if state_key in state:
                resolved_inputs[key] = state[state_key]
            else:
                logger.warning(f"State key '{state_key}' not found in state")
                resolved_inputs[key] = value
        else:
            resolved_inputs[key] = value
    
    return resolved_inputs


def extract_state_key(placeholder: str) -> str:
    """
    Extract the state key from a placeholder.
    
    Examples:
        {{prospect_search.output.leads}} -> leads
        {{enrichment.output.enriched_leads}} -> enriched_leads
        {{scoring.output.ranked_leads}} -> ranked_leads
    """
    # Remove {{ and }}
    placeholder = placeholder.strip('{}').strip()
    
    # Split by dots and get the last part (the actual state key)
    parts = placeholder.split('.')
    
    # If format is step_id.output.key, return key
    if len(parts) >= 3 and parts[1] == 'output':
        return parts[2]
    
    # Otherwise return the last part
    return parts[-1]


def update_state_with_output(state: WorkflowState, step_id: str, output: Dict[str, Any]) -> WorkflowState:
    """
    Update the workflow state with agent output.
    
    Args:
        state: Current workflow state
        step_id: ID of the step that produced output
        output: Agent output dictionary
        
    Returns:
        WorkflowState: Updated state
    """
    # Map step outputs to state keys
    output_mapping = {
        'prospect_search': 'leads',
        'enrichment': 'enriched_leads',
        'scoring': 'ranked_leads',
        'outreach_content': 'messages',
        'send': 'sent_status',
        'response_tracking': 'responses',
        'feedback_trainer': 'recommendations'
    }
    
    # Update state based on output keys
    for key, value in output.items():
        if key in output_mapping.values():
            # Direct mapping
            state[key] = value
        elif step_id in output_mapping:
            # Use step-based mapping
            state[output_mapping[step_id]] = value
    
    # Also store raw output under step_id for debugging
    # (Note: This isn't part of the TypedDict, but can be useful)
    
    return state


# ==============================================================================
# STEP 4: Build LangGraph from Workflow Config
# ==============================================================================

def build_langgraph(workflow: Dict[str, Any]) -> StateGraph:
    """
    Dynamically build a LangGraph from workflow configuration.
    
    Args:
        workflow: Workflow configuration dictionary
        
    Returns:
        StateGraph: Compiled LangGraph ready for execution
    """
    logger.info("=" * 80)
    logger.info("Building LangGraph")
    logger.info("=" * 80)
    
    # Initialize StateGraph
    graph = StateGraph(WorkflowState)
    
    steps = workflow['steps']
    node_functions = {}
    
    # Create node functions for each step
    for step in steps:
        step_id = step['id']
        agent_name = step['agent']
        
        logger.info(f"  Creating node: {step_id} ({agent_name})")
        
        # Load agent class
        agent_class = load_agent_class(agent_name)
        
        # Create node function
        node_func = create_node_function(step, agent_class)
        node_functions[step_id] = node_func
        
        # Add node to graph
        graph.add_node(step_id, node_func)
    
    # Add edges between nodes (sequential flow)
    logger.info("\n  Adding edges:")
    for i in range(len(steps) - 1):
        from_node = steps[i]['id']
        to_node = steps[i + 1]['id']
        graph.add_edge(from_node, to_node)
        logger.info(f"    {from_node} -> {to_node}")
    
    # Add edge from last node to END
    last_node = steps[-1]['id']
    graph.add_edge(last_node, END)
    logger.info(f"    {last_node} -> END")
    
    # Set entry point
    entry_point = steps[0]['id']
    graph.set_entry_point(entry_point)
    logger.info(f"\n  Entry point: {entry_point}")
    
    logger.info("\n  Compiling graph...")
    compiled_graph = graph.compile()
    
    logger.info("  LangGraph built successfully")
    
    return compiled_graph


# ==============================================================================
# STEP 5: Execute LangGraph
# ==============================================================================

def execute_langgraph(graph, workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the LangGraph workflow.
    
    Args:
        graph: Compiled LangGraph
        workflow: Workflow configuration
        
    Returns:
        dict: Execution results
    """
    logger.info("=" * 80)
    logger.info("Executing LangGraph Workflow")
    logger.info("=" * 80)
    
    start_time = datetime.now()
    
    # Initialize state with inputs from first step
    first_step = workflow['steps'][0]
    initial_state = {
        'step_count': 0,
        'errors': []
    }
    
    # Add any direct inputs from first step
    for key, value in first_step['inputs'].items():
        if not (isinstance(value, str) and value.startswith("{{")):
            initial_state[key] = value
    
    logger.info(f"Initial state keys: {list(initial_state.keys())}")
    
    try:
        # Execute the graph
        final_state = graph.invoke(initial_state)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Prepare execution results
        execution_results = {
            'workflow_name': workflow['workflow_name'],
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'steps_executed': final_state.get('step_count', 0),
            'status': 'completed' if len(final_state.get('errors', [])) == 0 else 'partial_failure',
            'errors': final_state.get('errors', []),
            'final_state': {
                'leads_count': len(final_state.get('leads', [])),
                'ranked_leads_count': len(final_state.get('ranked_leads', [])),
                'messages_count': len(final_state.get('messages', [])),
                'recommendations_count': len(final_state.get('recommendations', []))
            }
        }
        
        return execution_results
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            'workflow_name': workflow['workflow_name'],
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'status': 'failed',
            'error': str(e)
        }


def print_execution_summary(results: Dict[str, Any]) -> None:
    """
    Print a summary of the workflow execution.
    
    Args:
        results (dict): Execution results
    """
    logger.info("=" * 80)
    logger.info("LangGraph Execution Summary")
    logger.info("=" * 80)
    
    logger.info(f"Workflow: {results['workflow_name']}")
    logger.info(f"Status: {results['status'].upper()}")
    logger.info(f"Start Time: {results['start_time']}")
    logger.info(f"End Time: {results['end_time']}")
    logger.info(f"Duration: {results.get('duration_seconds', 0):.2f}s")
    logger.info(f"Steps Executed: {results.get('steps_executed', 0)}")
    
    if 'final_state' in results:
        logger.info("\nFinal State Summary:")
        for key, value in results['final_state'].items():
            logger.info(f"  {key}: {value}")
    
    if results.get('errors'):
        logger.error("\nErrors encountered:")
        for error in results['errors']:
            logger.error(f"  - {error}")
    
    logger.info("=" * 80)


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    """
    Main function to run the complete LangGraph workflow.
    """
    try:
        # Step 1: Load and validate workflow
        workflow = load_workflow("workflow.json")
        validate_workflow(workflow)
        
        # Step 2: Build LangGraph
        graph = build_langgraph(workflow)
        
        # Step 3: Execute LangGraph
        results = execute_langgraph(graph, workflow)
        
        # Print summary
        print_execution_summary(results)
        
        # Save results to file
        output_file = f"langgraph_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        logger.critical(f"Fatal Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()