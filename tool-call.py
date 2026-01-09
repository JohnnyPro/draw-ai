import inspect
import sys
import os
import argparse
import typing
from pathlib import Path

from google import genai
from google.genai import types

# Import implementations
from primitives.pillow_impl import PillowDrawer
from primitives.svg_impl import SVGDrawer
from primitives.turtle_impl import TurtleDrawer
from primitives import definitions

from dotenv import load_dotenv
from datetime import datetime

# This will hold the function declarations for the LLM
PRIMITIVE_TOOLS = []
OUTPUT_DIRECTORY = "./outputs"


# --- Step 1 & 2: Read definitions and generate tools ---
def _load_primitive_definitions():
    """
    Loads the drawable functions from the definitions module.
    The new SDK can often use the function objects directly.
    """
    global PRIMITIVE_TOOLS
    for name, func in inspect.getmembers(definitions, inspect.isfunction):
        if name.startswith("draw_"):
            PRIMITIVE_TOOLS.append(func)


def _execute_drawing_function(drawer_instance, function_name, **kwargs):
    func = getattr(drawer_instance, function_name, None)
    if func:
        func(**kwargs)
    else:
        print(f"Error: Drawing function {function_name} not found in drawer.")

def main():
    parser = argparse.ArgumentParser(description="Generate drawings using LLM function calls.")
    parser.add_argument("--drawer_type", type=str, default="pillow", choices=["pillow", "svg", "turtle"],
                        help="Choose drawing backend: pillow, svg, or turtle.")
    parser.add_argument("--width", type=int, default=800, help="Canvas width.")
    parser.add_argument("--height", type=int, default=800, help="Canvas height.")
    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()

    # The new SDK automatically picks up the GOOGLE_API_KEY
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found. Please set it in your .env file or environment variables.")
        sys.exit(1)
    
    client = genai.Client()

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    _load_primitive_definitions()

    print("=" * 60)
    print(f"🖼️  Function-Calling Drawing Application ({args.drawer_type.upper()} backend)")
    print("=" * 60)

    while True:
        try:
            prompt = input("\nWhat would you like me to draw? (or Ctrl+C to exit)\n> ")
            if not prompt.strip():
                continue

            print(f"Sending prompt to LLM: '{prompt}'")
            
            # The new API for tool use involves a single generate_content call
            response = client.models.generate_content(
                model="models/gemini-flash-latest",
                contents=prompt,
                generation_config=types.GenerationConfig(tools=PRIMITIVE_TOOLS)
            )

            # Instantiate the drawer
            drawer = None
            if args.drawer_type == "pillow":
                drawer = PillowDrawer(args.width, args.height)
            elif args.drawer_type == "svg":
                drawer = SVGDrawer(args.width, args.height)
            elif args.drawer_type == "turtle":
                drawer = TurtleDrawer(args.width, args.height)
            else:
                print("Invalid drawer type selected.")
                continue

            # Process function calls from the LLM response
            if response.candidates and response.candidates[0].content.parts:
                print("LLM is generating the drawing...")
                has_calls = False
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        has_calls = True
                        function_call = part.function_call
                        # Convert arguments to a standard dict
                        args_dict = {key: value for key, value in function_call.args.items()}
                        print(f"  - Executing: {function_call.name}({args_dict})")
                        _execute_drawing_function(drawer, function_call.name, **args_dict)
                    elif part.text:
                        print(f"LLM said: {part.text}")
                
                if not has_calls:
                    print("The LLM did not return any drawing instructions.")
                    continue
            else:
                print("The LLM did not provide a valid response.")
                continue

            # --- Save output ---
            if drawer:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if args.drawer_type == "svg":
                    filename = f"tool_call_{timestamp}.svg"
                elif args.drawer_type == "turtle":
                    filename = f"tool_call_{timestamp}.eps"
                else: # pillow
                    filename = f"tool_call_{timestamp}.png"

                filepath = os.path.join(OUTPUT_DIRECTORY, filename)
                drawer.save(filepath)
                
                print("\n" + "=" * 60)
                print(f"✅ Drawing saved to: {filepath}")
                print("=" * 60)

                if args.drawer_type == "turtle":
                    print("Note: Turtle output is saved as a Postscript (.eps) file.")
                elif args.drawer_type == "pillow":
                    # Try to show the image
                    try:
                        from PIL import Image
                        Image.open(filepath).show()
                    except Exception:
                        print(f"(Could not automatically open {filepath})")

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
