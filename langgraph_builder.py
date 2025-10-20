import os
import json
from typing import Dict, Any, List
from datetime import datetime
import re
import importlib

def load_agent_class(agent_name: str):
    try:
        module_name = f"agents.{agent_name.lower()}"
        module = importlib.import_module(module_name)
        return getattr(module, agent_name)
    except (ModuleNotFoundError, AttributeError) as e:
        raise ImportError(f"Could not load agent class '{agent_name}': {e}")

def load_workflow(workflow_path: str = "workflow.json") -> Dict[str, Any]:
    print(f"\n{'='*60}")
    print(f"🔧 Loading Workflow Configuration")
    print(f"{'='*60}\n")
    
    if not os.path.exists(workflow_path):
        raise FileNotFoundError(f" Workflow file not found: {workflow_path}")
    
    # Load and parse JSON
    try:
        with open(workflow_path, 'r') as file:
            workflow = json.load(file)
        
        print(f"Successfully loaded: {workflow_path}")
        print(f"Workflow Name: {workflow.get('workflow_name', 'Unnamed')}")
        print(f"Description: {workflow.get('description', 'No description')}")
        print(f"Total Steps: {len(workflow.get('steps', []))}")
        
        return workflow
        
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")
        raise

def validate_workflow(workflow: Dict[str, Any]) -> bool:
    print(f"\n{'='*60}")
    print(f"🔍 Validating Workflow Structure")
    print(f"{'='*60}\n")
    
    required_fields = ['workflow_name', 'steps']
    
    for field in required_fields:
        if field not in workflow:
            raise ValueError(f"Missing required field: {field}")
        print(f"Found required field: {field}")
    
    # Check that steps is a list and not empty
    steps = workflow['steps']
    if not isinstance(steps, list):
        raise ValueError("'steps' must be a list")
    
    if len(steps) == 0:
        raise ValueError("Workflow must have at least one step")
    
    print(f"Workflow has {len(steps)} step(s)")
    
    # Validate each step has required fields
    print(f"\nValidating Individual Steps:")
    for i, step in enumerate(steps, 1):
        step_id = step.get('id', f'step_{i}')
        print(f"\n  Step {i}: {step_id}")
        
        # Check required step fields
        required_step_fields = ['id', 'agent', 'inputs', 'instructions']
        for field in required_step_fields:
            if field not in step:
                raise ValueError(f"❌ Step '{step_id}' missing field: {field}")
            print(f"{field}: {type(step[field]).__name__}")
    
    print(f"\nAll validations passed!")
    return True

def print_workflow_summary(workflow: Dict[str, Any]) -> None:
    print(f"\n{'='*60}")
    print(f"📊 Workflow Execution Plan")
    print(f"{'='*60}\n")
    
    steps = workflow['steps']
    
    for i, step in enumerate(steps, 1):
        step_id = step['id']
        agent_name = step['agent']
        
        print(f"Step {i}: [{step_id}]")
        print(f"  └─ Agent: {agent_name}")
        print(f"  └─ Tools: {len(step.get('tools', []))} configured")
        
        # Show input dependencies
        inputs = step.get('inputs', {})
        dependencies = [v for v in str(inputs).split('{{') if '}}' in v]
        if dependencies:
            print(f"  └─ Dependencies: {len(dependencies)} placeholder(s)")
        
        if i < len(steps):
            print(f"     ↓")
    
    print(f"\n{'='*60}\n")


def resolve_placeholders(data: Any, data_store: Dict[str, Any]) -> Any:
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
                    print(f"Warning: Could not resolve placeholder {{{{match}}}}")
                    print(f" Available keys: {list(data_store.keys())}")
            
            return result
    
    # Return unchanged for other types
    return data


def execute_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    
    print(f"\n{'='*60}")
    print(f"Starting Workflow Execution")
    print(f"{'='*60}\n")
    
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
        
        print(f"\n{'─'*60}")
        print(f"📍 Step {i}/{len(steps)}: {step_id}")
        print(f"{'─'*60}")
        
        step_start_time = datetime.now()
        
        try:

            agent_class = load_agent_class(agent_name)
            
            # 2. Create agent instance with configuration
            agent_config = {
                'tools': step.get('tools', []),
                'instructions': step.get('instructions', ''),
                'output_schema': step.get('output_schema', {})
            }
            agent_instance = agent_class(agent_id=step_id, config=agent_config)
            
            # 3. Resolve placeholders in inputs
            print(f"\n  🔄 Resolving input placeholders...")
            raw_inputs = step['inputs']
            resolved_inputs = resolve_placeholders(raw_inputs, data_store)
            
            print(f"  📥 Inputs prepared for {agent_name}")
            
            # 4. Execute the agent
            print(f"\n  ▶️  Executing {agent_name}...")
            output = agent_instance.run(resolved_inputs)
            
            # 5. Store output in data_store
            data_store[step_id] = {'output': output}
            
            print(f"\n  ✅ Step {step_id} completed successfully!")
            print(f"  📤 Output keys: {list(output.keys()) if isinstance(output, dict) else 'N/A'}")
            
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
            print(f"\n  ❌ Error in step {step_id}: {str(e)}")
            
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
                print(f"\n❌ Workflow stopped due to error in step: {step_id}")
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
    print(f"\n{'='*60}")
    print(f"📊 Workflow Execution Summary")
    print(f"{'='*60}\n")
    
    print(f"Workflow: {results['workflow_name']}")
    print(f"Status: {results['status'].upper()}")
    print(f"Start: {results['start_time']}")
    print(f"End: {results['end_time']}")
    print(f"\nSteps Executed: {len(results['steps'])}\n")
    
    for step in results['steps']:
        status_icon = "✅" if step['status'] == 'success' else "❌"
        print(f"{status_icon} {step['step_id']} ({step['agent']})")
        print(f"   └─ Duration: {step['duration_seconds']:.2f}s")
        if step['status'] == 'failed':
            print(f"   └─ Error: {step.get('error', 'Unknown')}")
    
    print(f"\n{'='*60}\n")


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
        
        print(f"💾 Results saved to: {output_file}\n")
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}\n")
        raise


if __name__ == "__main__":
    main()