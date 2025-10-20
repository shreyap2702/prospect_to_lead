"""
Prospect Search Agent
Simulates lead discovery by searching for B2B companies matching ICP criteria.
In production, this would call Clay API and Apollo API for real data.
"""

import random
import time
from typing import Dict, Any, List
from agents.base_agent import BaseAgent


class ProspectSearchAgent(BaseAgent):
    """
    Agent responsible for discovering and collecting prospect leads.
    
    This agent simulates searching through company databases (Clay, Apollo)
    to find B2B companies matching the Ideal Customer Profile (ICP).
    
    Inputs:
        - industry (str): Target industry (e.g., "SaaS", "FinTech")
        - location (str): Geographic location (e.g., "USA", "UK")
        - employee_count (dict): Min/max employee range
        - signals (list): Buying signals (e.g., "recent_funding", "hiring_for_sales")
    
    Outputs:
        - leads (list): List of companies with contact information
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """Initialize the ProspectSearchAgent."""
        super().__init__(agent_id, config)
        self.log("ProspectSearchAgent initialized and ready", level="INFO")
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute prospect search based on ICP criteria.
        
        Args:
            inputs (dict): Contains ICP filters (industry, location, etc.)
            
        Returns:
            dict: Dictionary with 'leads' key containing list of prospects
        """
        
        # Step 1: Log starting message
        self.log("Starting prospect search...", level="INFO")
        self.log(f"Searching for: {inputs.get('industry', 'N/A')} companies in {inputs.get('location', 'N/A')}", level="INFO")
        
        # Step 2: Validate required inputs
        required_fields = ["industry", "location", "employee_count", "signals"]
        
        if not self.validate_inputs(inputs, required_fields):
            self.log("Input validation failed. Returning empty leads.", level="ERROR")
            return {"leads": []}
        
        # Extract inputs
        industry = inputs.get("industry")
        location = inputs.get("location")
        employee_count = inputs.get("employee_count", {})
        signals = inputs.get("signals", [])
        
        # Step 3: Simulate API search (mock data)
        self.log("Querying Clay API and Apollo API...", level="INFO")
        
        # Simulate API delay
        time.sleep(0.5)
        
        # Mock company database with realistic B2B SaaS companies
        mock_companies = [
            {
                "company": "CloudSync Technologies",
                "contact_name": "Sarah Mitchell",
                "email": "sarah.mitchell@cloudsync.io",
                "linkedin": "linkedin.com/in/sarahmitchell",
                "title": "VP of Sales",
                "signal": "recent_funding",
                "revenue": 45000000,
                "employee_count": 250
            },
            {
                "company": "DataFlow Systems",
                "contact_name": "Michael Chen",
                "email": "m.chen@dataflow.com",
                "linkedin": "linkedin.com/in/michaelchen",
                "title": "Chief Revenue Officer",
                "signal": "hiring_for_sales",
                "revenue": 78000000,
                "employee_count": 450
            },
            {
                "company": "AutoScale Inc",
                "contact_name": "Jennifer Rodriguez",
                "email": "jrodriguez@autoscale.io",
                "linkedin": "linkedin.com/in/jenniferrodriguez",
                "title": "Head of Business Development",
                "signal": "recent_funding",
                "revenue": 32000000,
                "employee_count": 180
            },
            {
                "company": "SecureAPI Solutions",
                "contact_name": "David Park",
                "email": "david@secureapi.com",
                "linkedin": "linkedin.com/in/davidpark",
                "title": "VP of Marketing",
                "signal": "hiring_for_sales",
                "revenue": 125000000,
                "employee_count": 620
            },
            {
                "company": "MetricsPro Analytics",
                "contact_name": "Amanda Johnson",
                "email": "ajohnson@metricspro.com",
                "linkedin": "linkedin.com/in/amandajohnson",
                "title": "Director of Sales",
                "signal": "recent_funding",
                "revenue": 55000000,
                "employee_count": 320
            },
            {
                "company": "PipelineHub",
                "contact_name": "Robert Kim",
                "email": "rkim@pipelinehub.io",
                "linkedin": "linkedin.com/in/robertkim",
                "title": "Chief Operating Officer",
                "signal": "hiring_for_sales",
                "revenue": 89000000,
                "employee_count": 410
            },
            {
                "company": "RevOps Platform",
                "contact_name": "Lisa Thompson",
                "email": "lisa.t@revopsplatform.com",
                "linkedin": "linkedin.com/in/lisathompson",
                "title": "VP of Revenue Operations",
                "signal": "recent_funding",
                "revenue": 67000000,
                "employee_count": 380
            },
            {
                "company": "GrowthEngine AI",
                "contact_name": "James Wilson",
                "email": "jwilson@growthengine.ai",
                "linkedin": "linkedin.com/in/jameswilson",
                "title": "Head of Sales",
                "signal": "hiring_for_sales",
                "revenue": 42000000,
                "employee_count": 215
            }
        ]
        
        # Filter companies based on ICP criteria
        filtered_leads = self._filter_by_icp(
            mock_companies, 
            employee_count, 
            signals
        )
        
        # Randomly select a subset for variety
        num_leads = random.randint(5, min(8, len(filtered_leads)))
        selected_leads = random.sample(filtered_leads, num_leads)
        
        # Step 4: Log output size
        self.log(
            f"Found {len(selected_leads)} leads matching ICP filters.", 
            level="SUCCESS",
            data={
                "total_searched": len(mock_companies),
                "matched_criteria": len(filtered_leads),
                "returned": len(selected_leads)
            }
        )
        
        # Log sample lead for debugging
        if selected_leads:
            self.log(
                f"Sample lead: {selected_leads[0]['company']} - {selected_leads[0]['contact_name']}",
                level="INFO"
            )
        
        # Step 5: Final success log
        self.log("Prospect search completed successfully.", level="SUCCESS")
        
        # Return structured output
        return {"leads": selected_leads}
    
    def _filter_by_icp(
        self, 
        companies: List[Dict[str, Any]], 
        employee_count: Dict[str, int],
        signals: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter companies based on ICP criteria.
        
        Args:
            companies: List of all companies
            employee_count: Min/max employee range
            signals: Required buying signals
            
        Returns:
            List of companies matching criteria
        """
        min_employees = employee_count.get("min", 0)
        max_employees = employee_count.get("max", float('inf'))
        
        filtered = []
        
        for company in companies:
            # Check employee count
            emp_count = company.get("employee_count", 0)
            if not (min_employees <= emp_count <= max_employees):
                continue
            
            # Check if company has any of the required signals
            company_signal = company.get("signal", "")
            if signals and company_signal not in signals:
                continue
            
            filtered.append(company)
        
        return filtered


# Optional: Test the agent standalone
if __name__ == "__main__":
    """
    Standalone test for ProspectSearchAgent
    """
    print("Testing ProspectSearchAgent...\n")
    
    # Create test config
    test_config = {
        "tools": [],
        "instructions": "Search for B2B SaaS companies"
    }
    
    # Create agent instance
    agent = ProspectSearchAgent(agent_id="test_prospect_search", config=test_config)
    
    # Test inputs
    test_inputs = {
        "industry": "SaaS",
        "location": "USA",
        "employee_count": {
            "min": 100,
            "max": 1000
        },
        "signals": ["recent_funding", "hiring_for_sales"]
    }
    
    # Run agent
    result = agent.run(test_inputs)
    
    # Print results
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    print(f"Total leads found: {len(result['leads'])}")
    print("\nSample leads:")
    for i, lead in enumerate(result['leads'][:3], 1):
        print(f"\n{i}. {lead['company']}")
        print(f"   Contact: {lead['contact_name']} ({lead['title']})")
        print(f"   Email: {lead['email']}")
        print(f"   Signal: {lead['signal']}")