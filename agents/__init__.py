"""
Agents Package
Contains all sub-agents for the LangGraph Prospect-to-Lead Workflow.
"""

from agents.base_agent import BaseAgent

# Import all agent classes here for easy access
from agents.prospect_search_agent import ProspectSearchAgent
from agents.scoring_agent import ScoringAgent
from agents.outreach_content_agent import OutreachContentAgent
from agents.feedback_trainer_agent import FeedbackTrainerAgent

# Optional: Define what gets exported when someone does "from agents import *"
__all__ = [
    'BaseAgent',
    'ProspectSearchAgent',
    'ScoringAgent',
    'OutreachContentAgent',
    'FeedbackTrainerAgent',
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'Your Name'