"""
Drawing Graph Assembly

Main LangGraph state machine that orchestrates the drawing workflow.
"""

from langgraph.graph import StateGraph, END

from graph.state import DrawState
from graph.nodes.prompt_analyzer import analyze_prompt
from graph.nodes.strategy_selector import select_strategy
from graph.nodes.backend_router import route_backend
from graph.nodes.one_go_executor import execute_one_go
from graph.nodes.tool_call_executor import execute_tool_call


def _should_clarify(state: DrawState) -> str:
    """Routing function: check if clarification is needed."""
    if state.get("needs_clarification", False):
        return "needs_clarification"
    return "proceed"


def _route_strategy(state: DrawState) -> str:
    """Routing function: route to the appropriate strategy executor."""
    strategy = state.get("strategy", "one-go")
    if strategy == "tool-call":
        return "tool-call"
    return "one-go"


def create_drawing_graph() -> StateGraph:
    """
    Create and compile the drawing graph.
    
    Graph flow:
    1. Analyze prompt → decide if clarification needed
    2. If needs clarification → return to user (interrupt)
    3. Select strategy (one-go vs tool-call)
    4. Route backend (pillow/svg/turtle)
    5. Execute appropriate strategy
    6. Done
    
    Returns:
        Compiled StateGraph ready for invocation
    """
    # Create graph with DrawState
    builder = StateGraph(DrawState)
    
    # Add nodes
    builder.add_node("analyze_prompt", analyze_prompt)
    builder.add_node("select_strategy", select_strategy)
    builder.add_node("route_backend", route_backend)
    builder.add_node("execute_one_go", execute_one_go)
    builder.add_node("execute_tool_call", execute_tool_call)
    
    # Set entry point
    builder.set_entry_point("analyze_prompt")
    
    # Add conditional edge for clarification check
    builder.add_conditional_edges(
        "analyze_prompt",
        _should_clarify,
        {
            "needs_clarification": END,  # Interrupt to ask user
            "proceed": "select_strategy",
        }
    )
    
    # Linear flow: strategy → backend
    builder.add_edge("select_strategy", "route_backend")
    
    # Route to appropriate executor based on strategy
    builder.add_conditional_edges(
        "route_backend",
        _route_strategy,
        {
            "one-go": "execute_one_go",
            "tool-call": "execute_tool_call",
        }
    )
    
    # Both executors end the graph
    builder.add_edge("execute_one_go", END)
    builder.add_edge("execute_tool_call", END)
    
    # Compile
    graph = builder.compile()
    
    return graph


def run_with_clarification(graph, initial_state: DrawState) -> DrawState:
    """
    Run the graph with support for human-in-the-loop clarification.
    
    If the graph stops for clarification, this function will prompt the user
    and continue until completion.
    
    Args:
        graph: Compiled StateGraph
        initial_state: Initial DrawState with original_prompt
    
    Returns:
        Final DrawState with output_path or error
    """
    state = initial_state
    
    while True:
        # Run graph
        result = graph.invoke(state)
        
        # Check if we need clarification
        if result.get("needs_clarification") and result.get("clarification_question"):
            print(f"\n❓ {result['clarification_question']}")
            user_answer = input("> ").strip()
            
            if not user_answer:
                # User wants to proceed anyway
                result["needs_clarification"] = False
            else:
                # Update prompt with clarification and re-run
                original = result.get("original_prompt", "")
                result["original_prompt"] = f"{original}. Additional context: {user_answer}"
                result["needs_clarification"] = False
                result["clarification_question"] = None
                result["confidence"] = None
            
            state = result
            continue
        
        # Graph completed
        return result
