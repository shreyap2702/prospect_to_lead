import random
import time

def query_clay_api(query: str):
    """Mock simulation of Clay API search."""
    time.sleep(0.3)
    return {
        "source": "Clay API",
        "query": query,
        "results": random.sample(
            ["AutoScale Inc", "DataFlow Systems", "CloudSync Technologies",
             "PipelineHub", "MetricsPro Analytics", "RevOps Platform"], k=4
        )
    }

def query_apollo_api(query: str):
    """Mock simulation of Apollo API search."""
    time.sleep(0.3)
    return {
        "source": "Apollo API",
        "query": query,
        "results": random.sample(
            ["AutoScale Inc", "DataFlow Systems", "PipelineHub",
             "GrowthBase AI", "SalesNest Solutions", "Leadify Co"], k=5
        )
    }

def mock_gpt_email_generation(company_name):
    """Simulate OpenAI API response for email generation."""
    return {
        "subject": f"Scaling {company_name}'s sales team?",
        "body": (
            f"Hi team {company_name},\n\n"
            "We noticed your recent growth and wanted to introduce "
            "our lead optimization platform to help scale your outreach.\n\n"
            "Best,\nShreya"
        )
    }
