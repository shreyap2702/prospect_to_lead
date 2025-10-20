"""
Outreach Content Agent
Generates personalized cold email content for top-ranked leads.
Uses OpenAI GPT-4o-mini when API key is available, falls back to templates.
"""

import os
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from mock_api import mock_gpt_email_generation


class OutreachContentAgent(BaseAgent):
    """
    Agent responsible for generating personalized outreach emails.
    
    Creates email subject lines and body content tailored to each lead
    based on their company info and signals.
    
    Inputs:
        - ranked_leads (list): Scored and ranked leads
        - top_n (int): Number of top leads to generate content for
        - persona (str): Sender persona (e.g., "SDR", "Account Executive")
        - tone (str): Email tone (e.g., "professional and friendly")
    
    Outputs:
        - messages (list): Email content for each lead
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """Initialize the OutreachContentAgent."""
        super().__init__(agent_id, config)
        
        # Check if OpenAI is available
        self.openai_key = os.getenv('OPENAI_API_KEY', '')
        self.use_openai = (
            self.openai_key and 
            self.openai_key != 'your_openai_api_key_here' and
            not self.openai_key.startswith('mock_')
        )
        
        if self.use_openai:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_key)
                self.log("✨ OpenAI GPT-4o-mini enabled for email generation", level="SUCCESS")
            except ImportError:
                self.log("⚠️  OpenAI package not installed. Using template mode.", level="WARNING")
                self.use_openai = False
            except Exception as e:
                self.log(f"⚠️  Could not initialize OpenAI: {e}", level="WARNING")
                self.use_openai = False
        else:
            self.log("📝 Using template-based email generation (mock mode)", level="INFO")
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized email content for leads.
        
        Args:
            inputs (dict): Contains ranked leads and email preferences
            
        Returns:
            dict: Dictionary with 'messages' containing email content
        """
        
        self.log("Starting outreach content generation...", level="INFO")
        
        # Validate inputs
        if not self.validate_inputs(inputs, ["ranked_leads"]):
            self.log("Missing ranked_leads input.", level="ERROR")
            return {"messages": []}
        
        ranked_leads = inputs.get("ranked_leads", [])
        top_n = inputs.get("top_n", 10)
        persona = inputs.get("persona", "SDR")
        tone = inputs.get("tone", "professional and friendly")
        
        if not ranked_leads:
            self.log("No leads to generate content for.", level="WARNING")
            return {"messages": []}
        
        # Select top N leads
        top_leads = ranked_leads[:top_n]
        
        mode = "OpenAI GPT-4o-mini" if self.use_openai else "Template-based"
        self.log(f"Generating personalized emails for top {len(top_leads)} leads using {mode}...", level="INFO")
        
        # Generate content for each lead
        messages = []
        for i, lead in enumerate(top_leads, 1):
            self.log(f"  Generating email {i}/{len(top_leads)} for {lead.get('company', 'Unknown')}", level="INFO")
            
            if self.use_openai:
                message = self._generate_email_with_gpt(lead, persona, tone)
            else:
                message = self._generate_email_template(lead, persona, tone)
            
            messages.append(message)
        
        self.log(
            f"Generated {len(messages)} personalized email messages.",
            level="SUCCESS"
        )
        
        # Show sample
        if messages:
            self.log(
                f"Sample subject: {messages[0]['subject']}",
                level="INFO"
            )
        
        return {"messages": messages}
    
    def _generate_email_with_gpt(
        self, 
        lead: Dict[str, Any],
        persona: str,
        tone: str
    ) -> Dict[str, Any]:
        """
        Generate personalized email using OpenAI GPT-4o-mini.
        """
        
        company = lead.get("company", "the company")
        contact_name = lead.get("contact_name", "there")
        first_name = contact_name.split()[0] if contact_name else "there"
        title = lead.get("title", "")
        signal = lead.get("signal", "")
        email = lead.get("email", "")
        score = lead.get("score", 0)
        
        # Build context for GPT
        signal_context = ""
        if signal == "recent_funding":
            signal_context = f"{company} recently raised funding"
        elif signal == "hiring_for_sales":
            signal_context = f"{company} is actively hiring for sales roles"
        
        # Create prompt for GPT
        prompt = f"""You are a {persona} writing a cold outreach email to {first_name} ({title}) at {company}.

Context:
- Company: {company}
- Contact: {first_name} {title if title else ''}
- Signal: {signal_context if signal_context else 'Growing B2B company'}
- Lead Score: {score}/100 (high fit for our ICP)

Task: Write a personalized cold email with:
1. A compelling subject line (max 60 characters)
2. Email body that:
   - Opens with the signal/context
   - Introduces Analytos.ai (AI-powered analytics for B2B companies)
   - Mentions 2-3 pain points we solve (fragmented data, manual reporting, missed opportunities)
   - Includes a soft call-to-action (15-min call)
   - Uses a {tone} tone
   - Keeps it under 150 words
   - Ends with "Best regards, SDR Team, Analytos.ai"

Format your response as:
SUBJECT: [subject line here]

BODY:
[email body here]"""

        try:
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert B2B sales email writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract subject and body
            parts = content.split("BODY:", 1)
            subject_part = parts[0].replace("SUBJECT:", "").strip()
            body_part = parts[1].strip() if len(parts) > 1 else content
            
            return {
                "lead": company,
                "email": email,
                "contact_name": contact_name,
                "subject": subject_part,
                "email_body": body_part,
                "generated_by": "openai_gpt4o_mini"
            }
            
        except Exception as e:
            self.log(f"GPT generation failed: {e}. Using mock GPT instead.", level="WARNING")
            from mock_api import mock_gpt_email_generation
            mock_response = mock_gpt_email_generation(lead.get("company", "Unknown"), tone)
            return {
                "lead": lead.get("company", "Unknown"),
                "email": lead.get("email", ""),
                "contact_name": lead.get("contact_name", ""),
                "subject": mock_response["subject"],
                "email_body": mock_response["email_body"],
                "generated_by": mock_response["generated_by"]
            }

    
    def _generate_email_template(
        self, 
        lead: Dict[str, Any],
        persona: str,
        tone: str
    ) -> Dict[str, Any]:
        """
        Generate personalized email using template (fallback/mock mode).
        """
        
        company = lead.get("company", "your company")
        contact_name = lead.get("contact_name", "there")
        first_name = contact_name.split()[0] if contact_name else "there"
        title = lead.get("title", "")
        signal = lead.get("signal", "")
        email = lead.get("email", "")
        
        # Generate subject line based on signal
        if signal == "recent_funding":
            subject = f"Congrats on {company}'s recent funding!"
        elif signal == "hiring_for_sales":
            subject = f"Scaling {company}'s sales team?"
        else:
            subject = f"Quick idea for {company}"
        
        # Generate email body
        body = self._create_email_body_template(
            first_name, 
            company, 
            title, 
            signal
        )
        
        return {
            "lead": company,
            "email": email,
            "contact_name": contact_name,
            "subject": subject,
            "email_body": body,
            "generated_by": "template"
        }
    
    def _create_email_body_template(
        self,
        first_name: str,
        company: str,
        title: str,
        signal: str
    ) -> str:
        """
        Create email body with template personalization.
        """
        
        # Opening based on signal
        if signal == "recent_funding":
            opening = f"I saw that {company} recently raised funding - congrats! That's exciting."
        elif signal == "hiring_for_sales":
            opening = f"I noticed {company} is actively hiring for sales roles. Looks like you're scaling!"
        else:
            opening = f"I've been following {company}'s growth and I'm impressed with what you're building."
        
        # Main value prop
        body = f"""Hi {first_name},

{opening}

I'm reaching out because we work with similar B2B companies to help them streamline their data analytics and improve decision-making processes.

Companies like yours often struggle with:
• Fragmented data across multiple tools
• Time-consuming manual reporting
• Difficulty identifying growth opportunities

Our platform at Analytos.ai helps solve these challenges by providing AI-powered analytics that surface actionable insights automatically.

Would you be open to a quick 15-minute call next week to explore if this could help {company}? 

I'd love to share some specific ideas based on what I've seen work for companies in your space.

Best regards,
SDR Team
Analytos.ai

P.S. No pressure - if the timing isn't right, I completely understand. Just let me know!"""
        
        return body


# Standalone test
if __name__ == "__main__":
    print("Testing OutreachContentAgent...\n")
    
    agent = OutreachContentAgent(agent_id="test_outreach", config={})
    
    test_inputs = {
        "ranked_leads": [
            {
                "company": "DataFlow Systems",
                "contact_name": "Michael Chen",
                "email": "m.chen@dataflow.com",
                "title": "Chief Revenue Officer",
                "signal": "hiring_for_sales",
                "score": 95.5,
                "ranking": 1
            },
            {
                "company": "CloudSync Technologies",
                "contact_name": "Sarah Mitchell",
                "email": "sarah.mitchell@cloudsync.io",
                "title": "VP of Sales",
                "signal": "recent_funding",
                "score": 92.3,
                "ranking": 2
            }
        ],
        "top_n": 2,
        "persona": "SDR",
        "tone": "professional and friendly"
    }
    
    result = agent.run(test_inputs)
    
    print("\n" + "="*60)
    print("GENERATED EMAILS:")
    print("="*60)
    for i, msg in enumerate(result['messages'], 1):
        print(f"\nEmail #{i}")
        print(f"To: {msg['contact_name']} ({msg['email']})")
        print(f"Subject: {msg['subject']}")
        print(f"Generated by: {msg.get('generated_by', 'unknown')}")
        print(f"\n{msg['email_body'][:300]}...")
        print("-" * 60)