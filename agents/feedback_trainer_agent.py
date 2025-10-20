"""
Feedback Trainer Agent
Analyzes campaign performance and suggests improvements.
Simple rule-based recommendation system.
"""

import random
from typing import Dict, Any, List
from agents.base_agent import BaseAgent


class FeedbackTrainerAgent(BaseAgent):
    """
    Agent responsible for learning from campaign performance.
    
    Analyzes email performance metrics and suggests improvements to:
    - ICP targeting criteria
    - Email messaging and tone
    - Subject line variations
    - Timing and frequency
    
    Inputs:
        - responses (list): Email messages sent
        - campaign_metrics (dict): Performance thresholds
    
    Outputs:
        - recommendations (list): Suggested improvements
        - status (str): Approval status
    """
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze campaign and generate improvement recommendations.
        
        Args:
            inputs (dict): Contains email responses and metrics
            
        Returns:
            dict: Dictionary with recommendations and status
        """
        
        self.log("Starting feedback analysis...", level="INFO")
        
        # Validate inputs
        if not self.validate_inputs(inputs, ["responses"]):
            self.log("Missing responses input.", level="ERROR")
            return {"recommendations": [], "status": "failed"}
        
        responses = inputs.get("responses", [])
        campaign_metrics = inputs.get("campaign_metrics", {})
        
        if not responses:
            self.log("No responses to analyze.", level="WARNING")
            return {"recommendations": [], "status": "no_data"}
        
        self.log(f"Analyzing {len(responses)} email messages...", level="INFO")
        
        # Simulate campaign metrics
        simulated_metrics = self._simulate_campaign_metrics(len(responses))
        
        self.log(
            f"Campaign metrics - Open rate: {simulated_metrics['open_rate']:.1%}, "
            f"Reply rate: {simulated_metrics['reply_rate']:.1%}",
            level="INFO"
        )
        
        # Generate recommendations based on performance
        recommendations = self._generate_recommendations(
            simulated_metrics,
            campaign_metrics,
            responses
        )
        
        self.log(
            f"Generated {len(recommendations)} recommendations for improvement.",
            level="SUCCESS"
        )
        
        # Log top recommendation
        if recommendations:
            self.log(
                f"Top recommendation: {recommendations[0]['category']} - {recommendations[0]['suggested_value']}",
                level="INFO"
            )
        
        return {
            "recommendations": recommendations,
            "campaign_metrics": simulated_metrics,
            "status": "pending_approval"
        }
    
    def _simulate_campaign_metrics(self, num_emails: int) -> Dict[str, Any]:
        """
        Simulate realistic campaign performance metrics.
        
        In production, this would pull real data from email service provider.
        """
        
        # Realistic B2B cold email metrics
        open_rate = random.uniform(0.20, 0.35)  # 20-35% is typical
        reply_rate = random.uniform(0.02, 0.08)  # 2-8% is good
        click_rate = random.uniform(0.05, 0.15)  # 5-15%
        
        return {
            "emails_sent": num_emails,
            "opens": int(num_emails * open_rate),
            "replies": int(num_emails * reply_rate),
            "clicks": int(num_emails * click_rate),
            "open_rate": open_rate,
            "reply_rate": reply_rate,
            "click_rate": click_rate
        }
    
    def _generate_recommendations(
        self,
        metrics: Dict[str, Any],
        thresholds: Dict[str, float],
        responses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations based on performance.
        
        Simple rule-based system that suggests improvements.
        """
        
        recommendations = []
        
        open_threshold = thresholds.get("open_rate_threshold", 0.25)
        reply_threshold = thresholds.get("reply_rate_threshold", 0.05)
        
        # Recommendation 1: Subject line optimization
        if metrics["open_rate"] < open_threshold:
            recommendations.append({
                "category": "subject_line",
                "current_value": "Generic subject lines",
                "suggested_value": "Try more personalized subject lines with company-specific details",
                "reason": f"Open rate ({metrics['open_rate']:.1%}) is below target ({open_threshold:.1%})",
                "confidence": 0.85,
                "priority": "high"
            })
        
        # Recommendation 2: Email body optimization
        if metrics["reply_rate"] < reply_threshold:
            recommendations.append({
                "category": "email_content",
                "current_value": "Current email template",
                "suggested_value": "Shorten email body and add more specific value proposition",
                "reason": f"Reply rate ({metrics['reply_rate']:.1%}) is below target ({reply_threshold:.1%})",
                "confidence": 0.78,
                "priority": "high"
            })
        
        # Recommendation 3: ICP refinement
        recommendations.append({
            "category": "icp_targeting",
            "current_value": "Current industry: SaaS, Revenue: $20M-$200M",
            "suggested_value": "Narrow to companies with $50M-$150M revenue for better fit",
            "reason": "Mid-market companies show higher engagement based on initial data",
            "confidence": 0.72,
            "priority": "medium"
        })
        
        # Recommendation 4: Timing optimization
        if metrics["open_rate"] < 0.30:
            recommendations.append({
                "category": "send_timing",
                "current_value": "Sending emails throughout the day",
                "suggested_value": "Send emails Tuesday-Thursday, 9-11 AM in prospect's timezone",
                "reason": "Open rates typically higher during mid-week mornings",
                "confidence": 0.80,
                "priority": "medium"
            })
        
        # Recommendation 5: Follow-up strategy
        recommendations.append({
            "category": "follow_up",
            "current_value": "Single touchpoint",
            "suggested_value": "Implement 3-touch sequence: Initial, +3 days, +7 days",
            "reason": "Multi-touch sequences increase response rates by 40-60%",
            "confidence": 0.88,
            "priority": "high"
        })
        
        # Sort by priority and confidence
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(
            key=lambda x: (priority_order[x["priority"]], x["confidence"]),
            reverse=True
        )
        
        return recommendations[:5]  # Return top 5


# Standalone test
if __name__ == "__main__":
    print("Testing FeedbackTrainerAgent...\n")
    
    agent = FeedbackTrainerAgent(agent_id="test_feedback", config={})
    
    test_inputs = {
        "responses": [
            {"lead": "Company A", "subject": "Test 1", "email_body": "..."},
            {"lead": "Company B", "subject": "Test 2", "email_body": "..."},
            {"lead": "Company C", "subject": "Test 3", "email_body": "..."},
            {"lead": "Company D", "subject": "Test 4", "email_body": "..."},
            {"lead": "Company E", "subject": "Test 5", "email_body": "..."}
        ],
        "campaign_metrics": {
            "open_rate_threshold": 0.25,
            "reply_rate_threshold": 0.05
        }
    }
    
    result = agent.run(test_inputs)
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS:")
    print("="*60)
    print(f"\nStatus: {result['status']}")
    print(f"\nCampaign Metrics:")
    metrics = result['campaign_metrics']
    print(f"  Emails sent: {metrics['emails_sent']}")
    print(f"  Open rate: {metrics['open_rate']:.1%}")
    print(f"  Reply rate: {metrics['reply_rate']:.1%}")
    
    print(f"\nTop Recommendations:")
    for i, rec in enumerate(result['recommendations'][:3], 1):
        print(f"\n{i}. {rec['category'].upper()} [{rec['priority']} priority]")
        print(f"   Current: {rec['current_value']}")
        print(f"   Suggested: {rec['suggested_value']}")
        print(f"   Reason: {rec['reason']}")
        print(f"   Confidence: {rec['confidence']:.0%}")