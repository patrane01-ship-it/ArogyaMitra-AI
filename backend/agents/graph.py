"""
ArogyaMitra AI - LangGraph Master Orchestration Graph
Wires Ingestion, Trend, and Reminder agents into a robust state machine.
Per TECH_STACK.md §3 and PRODUCTION_BACKEND.md §6.2.
"""

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from backend.core.logger import logger
from backend.agents.ingestion_agent import ingestion_agent_node
from backend.agents.trend_agent import trend_agent_node
from backend.agents.reminder_agent import reminder_agent_node


class ArogyaState(TypedDict):
    record_id: str
    user_id: str
    record_type: str
    file_path: Optional[str]
    raw_text: str
    extracted_entities: Dict[str, Any]
    clinical_params: List[Dict[str, Any]]
    risk_score: float
    risk_level: str
    reminders_created: List[Dict[str, Any]]
    doctor_report_content: str
    errors: List[Dict[str, Any]]
    current_step: str


def route_after_ingestion(state: ArogyaState) -> str:
    """If ingestion failed, skip remaining nodes and terminate."""
    if state.get("current_step") == "ingestion_failed":
        logger.warning(f"[Graph] Ingestion failed for {state.get('record_id')}. Routing to END.")
        return END
    return "trend_agent"


def route_after_trend(state: ArogyaState) -> str:
    """Route to reminder_agent if document is a prescription, otherwise END."""
    if state.get("record_type") == "PRESCRIPTION":
        logger.info("[Graph] Document is prescription. Routing to reminder_agent.")
        return "reminder_agent"
    return END


# Build the LangGraph StateGraph
workflow = StateGraph(ArogyaState)

# Add Agent Nodes
workflow.add_node("ingestion_agent", ingestion_agent_node)
workflow.add_node("trend_agent", trend_agent_node)
workflow.add_node("reminder_agent", reminder_agent_node)

# Set Entry Point
workflow.set_entry_point("ingestion_agent")

# Add Conditional Edges
workflow.add_conditional_edges(
    "ingestion_agent",
    route_after_ingestion,
    {
        "trend_agent": "trend_agent",
        END: END,
    }
)

workflow.add_conditional_edges(
    "trend_agent",
    route_after_trend,
    {
        "reminder_agent": "reminder_agent",
        END: END,
    }
)

workflow.add_edge("reminder_agent", END)

# Compile graph
graph = workflow.compile()


async def run_pipeline(
    record_id: str,
    user_id: str = "local_user",
    file_path: Optional[str] = None,
    record_type: str = "LAB_REPORT",
    raw_text: str = "",
) -> Dict[str, Any]:
    """Helper function to execute the full LangGraph agent pipeline."""
    initial_state: ArogyaState = {
        "record_id": record_id,
        "user_id": user_id,
        "record_type": record_type,
        "file_path": file_path,
        "raw_text": raw_text,
        "extracted_entities": {},
        "clinical_params": [],
        "risk_score": 0.0,
        "risk_level": "LOW",
        "reminders_created": [],
        "doctor_report_content": "",
        "errors": [],
        "current_step": "init",
    }

    logger.info(f"[Graph] Executing pipeline for record_id={record_id}")
    final_state = await graph.ainvoke(initial_state)
    logger.info(
        f"[Graph] Pipeline complete | record_id={record_id} | errors={len(final_state.get('errors', []))}"
    )
    return final_state
