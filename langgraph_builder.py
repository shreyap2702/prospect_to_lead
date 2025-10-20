import json
import os
import re
import importlib
import logging
from typing import Dict, Any, List
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


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
        # Insert underscore before each capital letter, then lowercase everything
        module_name = ''
        for i, char in enumerate(agent_name):
            if char.isupper() and i > 0:
                module_name += '_'
            module_name += char.lower()
        
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
# STEP 3: Placeholder Replacement & Execution
# ==============================================================================

def resolve_placeholders(data: Any, data_store: Dict[str, Any]) -> Any:
    """
    Recursively resolve placeholders like {{step_id.output.field}} in data.
    
    Args:
        data: Input data (can be dict, list, str, or any type)
        data_store: Dictionary containing outputs from previous steps
        
    Returns:
        Data with all placeholders replaced
        
    Example:
        Input: {"leads": "{{prospect_search.output.leads}}"}
        data_store: {"prospect_search": {"output": {"leads": [...]}}}
        Output: {"leads": [...]}
    """
    
    if isinstance(data, dict):
        # Process dictionary recursively
        return {key: resolve_placeholders(value, data_store) for key, value in data.items()}
    
    elif isinstance(data, list):
        # Process list recursively
        return [resolve_placeholders(item, data_store) for item in data]
    
    elif isinstance(data, str):
        # Check if string contains placeholders
        placeholder_pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(placeholder_pattern, data)
        
        if matches:
            # Replace each placeholder
            result = data
            for match in matches:
                # Parse placeholder: "step_id.output.field"
                parts = match.strip().split('.')
                
                # Navigate through data_store
                value = data_store
                try:
                    for part in parts:
                        value = value[part]
                    
                    # If the entire string is just a placeholder, return the value directly
                    if data == f"{{{{{match}}}}}":
                        return value
                    
                    # Otherwise, replace the placeholder in the string
                    result = result.replace(f"{{{{{match}}}}}", str(value))
                    
                except (KeyError, TypeError) as e:
                    logger.warning(f"Could not resolve placeholder: {{{{{match}}}}}")
                    logger.warning(f"Available keys in data_store: {list(data_store.keys())}")
            
            return result
    
    # Return unchanged for other types
    return data


def execute_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the entire workflow step by step.
    
    Args:
        workflow (dict): Workflow configuration
        
    Returns:
        dict: Complete execution results with all step outputs
    """
    logger.info("=" * 80)
    logger.info("Starting Workflow Execution")
    logger.info("=" * 80)
    
    steps = workflow['steps']
    data_store = {}  # Store outputs from each step
    execution_results = {
        'workflow_name': workflow['workflow_name'],
        'start_time': datetime.now().isoformat(),
        'steps': []
    }
    
    # Execute each step sequentially
    for i, step in enumerate(steps, 1):
        step_id = step['id']
        agent_name = step['agent']
        
        logger.info("-" * 80)
        logger.info(f"Executing Step {i}/{len(steps)}: {step_id}")
        logger.info("-" * 80)
        
        step_start_time = datetime.now()
        
        try:
            # 1. Load the agent class dynamically
            agent_class = load_agent_class(agent_name)
            
            # 2. Create agent instance with configuration
            agent_config = {
                'tools': step.get('tools', []),
                'instructions': step.get('instructions', ''),
                'output_schema': step.get('output_schema', {})
            }
            agent_instance = agent_class(agent_id=step_id, config=agent_config)
            
            # 3. Resolve placeholders in inputs
            logger.info("  Resolving input placeholders")
            raw_inputs = step['inputs']
            resolved_inputs = resolve_placeholders(raw_inputs, data_store)
            
            logger.debug(f"  Inputs prepared for {agent_name}")
            
            # 4. Execute the agent
            logger.info(f"  Running agent: {agent_name}")
            output = agent_instance.run(resolved_inputs)
            
            # 5. Store output in data_store
            data_store[step_id] = {'output': output}
            
            logger.info(f"  Step {step_id} completed successfully")
            if isinstance(output, dict):
                logger.debug(f"  Output contains keys: {list(output.keys())}")
            
            # Record step execution
            step_result = {
                'step_id': step_id,
                'agent': agent_name,
                'status': 'success',
                'duration_seconds': (datetime.now() - step_start_time).total_seconds(),
                'output_preview': str(output)[:200] + '...' if len(str(output)) > 200 else str(output)
            }
            execution_results['steps'].append(step_result)
            
        except Exception as e:
            logger.error(f"Error in step {step_id}: {str(e)}", exc_info=True)
            
            step_result = {
                'step_id': step_id,
                'agent': agent_name,
                'status': 'failed',
                'error': str(e),
                'duration_seconds': (datetime.now() - step_start_time).total_seconds()
            }
            execution_results['steps'].append(step_result)
            
            # Decide whether to continue or stop
            if not workflow.get('error_handling', {}).get('continue_on_error', False):
                logger.error(f"Workflow stopped due to error in step: {step_id}")
                break
    
    # Finalize execution results
    execution_results['end_time'] = datetime.now().isoformat()
    execution_results['status'] = 'completed' if all(
        s['status'] == 'success' for s in execution_results['steps']
    ) else 'partial_failure'
    
    return execution_results


def print_execution_summary(results: Dict[str, Any]) -> None:
    """
    Print a summary of the workflow execution.
    
    Args:
        results (dict): Execution results
    """
    logger.info("=" * 80)
    logger.info("Workflow Execution Summary")
    logger.info("=" * 80)
    
    logger.info(f"Workflow: {results['workflow_name']}")
    logger.info(f"Status: {results['status'].upper()}")
    logger.info(f"Start Time: {results['start_time']}")
    logger.info(f"End Time: {results['end_time']}")
    logger.info(f"Steps Executed: {len(results['steps'])}")
    logger.info("")
    
    for step in results['steps']:
        status = "SUCCESS" if step['status'] == 'success' else "FAILED"
        logger.info(f"[{status}] {step['step_id']} ({step['agent']})")
        logger.info(f"         Duration: {step['duration_seconds']:.2f}s")
        if step['status'] == 'failed':
            logger.error(f"         Error: {step.get('error', 'Unknown')}")
    
    logger.info("=" * 80)


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    """
    Main function to run the complete workflow.
    """
    try:
        # Step 1: Load and validate workflow
        workflow = load_workflow("workflow.json")
        validate_workflow(workflow)
        
        # Step 2 & 3: Execute workflow
        results = execute_workflow(workflow)
        
        # Print summary
        print_execution_summary(results)
        
        # Save results to file
        output_file = f"execution_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to: {output_file}")
        
    except Exception as e:
        logger.critical(f"Fatal Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()