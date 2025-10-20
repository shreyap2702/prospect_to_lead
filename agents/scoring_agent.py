"""
Scoring Agent
Scores and ranks leads based on ICP fit criteria.
Simple scoring algorithm based on revenue, employee count, and signals.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent


class ScoringAgent(BaseAgent):
    """
    Agent responsible for scoring and ranking leads.
    
    Assigns a score (0-100) to each lead based on:
    - Revenue fit
    - Employee count fit
    - Presence of buying signals
    
    Inputs:
        - leads (list): List of prospect leads from ProspectSearchAgent
        - scoring_criteria (dict): Weights for different scoring factors
    
    Outputs:
        - ranked_leads (list): Leads sorted by score (highest first)
    """
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score and rank leads based on ICP fit.
        
        Args:
            inputs (dict): Contains leads and scoring criteria
            
        Returns:
            dict: Dictionary with 'ranked_leads' sorted by score
        """
        
        self.log("Starting lead scoring...", level="INFO")
        
        # Validate inputs
        if not self.validate_inputs(inputs, ["leads"]):
            self.log("Missing leads input. Returning empty results.", level="ERROR")
            return {"ranked_leads": []}
        
        leads = inputs.get("leads", [])
        scoring_criteria = inputs.get("scoring_criteria", {})
        
        if not leads:
            self.log("No leads to score.", level="WARNING")
            return {"ranked_leads": []}
        
        self.log(f"Scoring {len(leads)} leads...", level="INFO")
        
        # Get scoring weights (with defaults)
        revenue_weight = scoring_criteria.get("revenue_weight", 0.3)
        employee_weight = scoring_criteria.get("employee_count_weight", 0.2)
        signal_weight = scoring_criteria.get("signal_weight", 0.5)
        
        # Score each lead
        scored_leads = []
        for lead in leads:
            score = self._calculate_score(
                lead, 
                revenue_weight, 
                employee_weight, 
                signal_weight
            )
            
            # Add score to lead
            lead_with_score = lead.copy()
            lead_with_score["score"] = round(score, 2)
            scored_leads.append(lead_with_score)
        
        # Sort by score (highest first)
        ranked_leads = sorted(scored_leads, key=lambda x: x["score"], reverse=True)
        
        # Add ranking number
        for i, lead in enumerate(ranked_leads, 1):
            lead["ranking"] = i
        
        # Log results
        self.log(
            f"Scoring complete. Top lead: {ranked_leads[0]['company']} (Score: {ranked_leads[0]['score']})",
            level="SUCCESS"
        )
        
        self.log(
            f"Score range: {ranked_leads[-1]['score']} to {ranked_leads[0]['score']}",
            level="INFO"
        )
        
        return {"ranked_leads": ranked_leads}
    
    def _calculate_score(
        self, 
        lead: Dict[str, Any],
        revenue_weight: float,
        employee_weight: float,
        signal_weight: float
    ) -> float:
        """
        Calculate score for a single lead.
        
        Simple scoring algorithm:
        - Revenue: 0-100 based on target range (20M-200M)
        - Employee count: 0-100 based on size
        - Signal: 100 if has signal, 50 if not
        """
        
        # Revenue score (target: 20M-200M)
        revenue = lead.get("revenue", 50000000)
        if revenue >= 200000000:
            revenue_score = 100
        elif revenue >= 20000000:
            # Linear scale between 20M and 200M
            revenue_score = 50 + ((revenue - 20000000) / 180000000) * 50
        else:
            revenue_score = (revenue / 20000000) * 50
        
        # Employee count score (target: 100-1000)
        employees = lead.get("employee_count", 300)
        if 100 <= employees <= 1000:
            employee_score = 100
        elif employees > 1000:
            employee_score = 80
        else:
            employee_score = (employees / 100) * 80
        
        # Signal score
        signal = lead.get("signal", "")
        signal_score = 100 if signal else 50
        
        # Weighted total
        total_score = (
            revenue_score * revenue_weight +
            employee_score * employee_weight +
            signal_score * signal_weight
        )
        
        return min(total_score, 100)  # Cap at 100


# Standalone test
if __name__ == "__main__":
    print("Testing ScoringAgent...\n")
    
    agent = ScoringAgent(agent_id="test_scoring", config={})
    
    # Mock leads
    test_inputs = {
        "leads": [
            {"company": "Company A", "revenue": 50000000, "employee_count": 300, "signal": "recent_funding", "contact_name": "John Doe", "email": "john@companya.com"},
            {"company": "Company B", "revenue": 150000000, "employee_count": 800, "signal": "hiring_for_sales", "contact_name": "Jane Smith", "email": "jane@companyb.com"},
            {"company": "Company C", "revenue": 30000000, "employee_count": 200, "signal": "", "contact_name": "Bob Johnson", "email": "bob@companyc.com"}
        ],
        "scoring_criteria": {
            "revenue_weight": 0.3,
            "employee_count_weight": 0.2,
            "signal_weight": 0.5
        }
    }
    
    result = agent.run(test_inputs)
    
    print("\n" + "="*60)
    print("RANKED LEADS:")
    print("="*60)
    for lead in result['ranked_leads']:
        print(f"\n#{lead['ranking']} - {lead['company']}")
        print(f"   Score: {lead['score']}")
        print(f"   Revenue: ${lead['revenue']:,}")
        print(f"   Employees: {lead['employee_count']}")