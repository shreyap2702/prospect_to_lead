# LangGraph Prospect-to-Lead Workflow

An AI-powered system that automatically finds B2B prospects, scores them, generates personalized emails, and learns from campaign performance using LangGraph.

## What It Does

This workflow automates lead generation for B2B companies:

1. **Finds Prospects** - Searches for companies matching your target profile
2. **Scores Leads** - Ranks prospects based on fit and buying signals
3. **Creates Outreach** - Generates personalized email content
4. **Learns & Improves** - Analyzes results and suggests optimizations

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/shreyap2702/prospect_to_lead
cd prospect_to_lead

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install requirements.txt
```

### Configuration

Create a `.env` file with your API keys:

```bash
CLAY_API_KEY=your_key_here
APOLLO_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Run the Workflow

```bash
python langgraph_builder.py
```

That's it! The system will:
- Load the workflow configuration from `workflow.json`
- Execute each agent in sequence
- Save results to a timestamped JSON file

## How It Works

### The Workflow

Everything is defined in `workflow.json`:

```json
{
  "workflow_name": "OutboundLeadGeneration",
  "steps": [
    {"id": "prospect_search", "agent": "ProspectSearchAgent"},
    {"id": "scoring", "agent": "ScoringAgent"},
    {"id": "outreach_content", "agent": "OutreachContentAgent"},
    {"id": "feedback_trainer", "agent": "FeedbackTrainerAgent"}
  ]
}
```

### LangGraph Architecture

The system uses LangGraph's StateGraph to orchestrate agents:

```
ProspectSearchAgent → ScoringAgent → OutreachContentAgent → FeedbackTrainerAgent
        ↓                  ↓                  ↓                      ↓
    Find leads        Score leads      Generate emails       Analyze results
```

All agents share a common state that flows through the pipeline.

## Project Structure

```
prospect_to_lead/
├── langgraph_builder.py    # Main orchestration script
├── workflow.json            # Workflow configuration
├── agents/                  # Agent implementations
│   ├── prospect_search_agent.py
│   ├── scoring_agent.py
│   ├── outreach_content_agent.py
│   └── feedback_trainer_agent.py
├── .env                     # API keys (create this)
└── README.md
```

## The Agents

### ProspectSearchAgent
Finds companies matching your Ideal Customer Profile using Clay and Apollo APIs.

**Output**: List of qualified leads with contact information

### ScoringAgent
Ranks leads based on revenue, growth signals, and technology fit.

**Output**: Scored and ranked leads (0-100 scale)

### OutreachContentAgent
Generates personalized email content for each prospect.

**Output**: Email subject lines and body content

### FeedbackTrainerAgent
Analyzes campaign metrics and suggests improvements.

**Output**: Recommendations for better performance

## Example Output

After running the workflow, you'll get:

```json
{
  "workflow_name": "OutboundLeadGeneration",
  "status": "completed",
  "duration_seconds": 0.51,
  "final_state": {
    "leads_count": 8,
    "ranked_leads_count": 8,
    "messages_count": 8,
    "recommendations_count": 16
  }
}
```

## Customization

### Modify the Workflow

Edit `workflow.json` to change:
- Target industries and locations
- Scoring criteria
- Email tone and style
- Number of leads to process

### Add New Agents

1. Create a new file in `/agents`:

```python
class MyNewAgent:
    def __init__(self, agent_id: str, config: dict):
        self.agent_id = agent_id
        self.config = config
    
    def run(self, inputs: dict) -> dict:
        # Your logic here
        return {"output": "data"}
```

2. Add it to `workflow.json`:

```json
{
  "id": "my_new_step",
  "agent": "MyNewAgent",
  "inputs": {"data": "{{previous_step.output.data}}"}
}
```

The system will automatically load and execute your new agent.

## Key Features

- **Dynamic Configuration**: Change workflow without touching code
- **LangGraph Native**: Uses StateGraph for proper agent orchestration
- **Modular Design**: Each agent is independent and reusable
- **State Management**: Data flows automatically between agents
- **Professional Logging**: Track every step of execution
- **Error Handling**: Graceful failure with detailed error messages

## Requirements

- Python 3.8+
- LangGraph
- LangChain
- API keys for: Clay, Apollo, OpenAI

## Troubleshooting

**Agent not found error?**
- Ensure agent file name matches class name (e.g., `ProspectSearchAgent` → `prospect_search_agent.py`)

**Missing dependencies?**
- Run `pip install langgraph langchain langchain-core`

**API errors?**
- Check your `.env` file has valid API keys

## License

MIT

## Contact

For questions or issues, please open a GitHub issue.