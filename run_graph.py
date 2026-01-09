"""
DrawAI LangGraph Entry Point

Main entry point for running the LangGraph-based drawing application.
"""

import os
import atexit

from dotenv import load_dotenv

from graph import create_drawing_graph
from graph.state import DrawState
from graph.drawing_graph import run_with_clarification
import observability


def main():
    """Main application entry point."""
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found.")
        print("Please set it in your .env file or environment variables.")
        return
    
    observability.init_langfuse()
    atexit.register(observability.shutdown)
    
    graph = create_drawing_graph()
    
    print("=" * 60)
    print("🎨 DrawAI - LangGraph Edition")
    print("=" * 60)
    print("Features:")
    print("  • Smart strategy selection (one-go vs tool-call)")
    print("  • Prompt clarity analysis with clarification")
    print("  • Automatic backend routing (Pillow/SVG/Turtle)")
    print("=" * 60)
    
    while True:
        try:
            prompt = input("\nWhat would you like me to draw? (or Ctrl+C to exit)\n> ")
            if not prompt.strip():
                continue
            
            initial_state: DrawState = {
                "original_prompt": prompt,
                "backend": "pillow",  # Default
            }
            
            print("\n[Graph] Starting drawing workflow...")
            
            result = run_with_clarification(graph, initial_state)
            
            if result.get("error"):
                print(f"\n❌ Drawing failed: {result['error']}")
            elif result.get("output_path"):
                print("\n" + "=" * 60)
                print(f"✅ Drawing complete!")
                print(f"   Strategy: {result.get('strategy', 'unknown')}")
                print(f"   Backend: {result.get('backend', 'unknown')}")
                print(f"   Output: {result['output_path']}")
                print("=" * 60)
                
                if result.get("confidence"):
                    observability.log_score(
                        "prompt_confidence",
                        result["confidence"],
                        f"Prompt: {prompt[:50]}..."
                    )
            else:
                print("\n⚠️ Drawing completed but no output was generated.")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
