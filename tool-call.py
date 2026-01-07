import inspect
import sys
import os
import importlib
import argparse
import typing
from pathlib import Path

import google.generativeai as genai
from google.generativeai.types import Tool
from google.generativeai.types import FunctionDeclaration

# Import implementations
from primitives.pillow_impl import PillowDrawer
from primitives.svg_impl import SVGDrawer
from primitives.turtle_impl import TurtleDrawer

from dotenv import load_dotenv
from datetime import datetime

# This will hold the function declarations for the LLM
PRIMITIVE_TOOLS = []
OUTPUT_DIRECTORY = "./outputs"


# --- Step 1 & 2: Read definitions and generate tools ---
def _load_primitive_definitions():
    import primitives.definitions as definitions_module

    for name, func in inspect.getmembers(definitions_module, inspect.isfunction):
        if name.startswith("draw_"):
            signature = inspect.signature(func)
            parameters_properties = {}
            parameters_required = []

            for param_name, param in signature.parameters.items():
                param_json_type = None
                is_optional = False

                # Correctly identify Optional types
                if hasattr(param.annotation, '__origin__') and param.annotation.__origin__ is typing.Union:
                    args = typing.get_args(param.annotation)
                    if type(None) in args:
                        is_optional = True
                        # Get the non-None type
                        non_none_args = [a for a in args if a is not type(None)]
                        if non_none_args:
                            param_type = non_none_args[0]
                        else:
                            continue # Should not happen in our case
                    else:
                        param_type = param.annotation
                else:
                    param_type = param.annotation

                if param_type is str:
                    param_json_type = "string"
                elif param_type is int:
                    param_json_type = "integer"


                if param_json_type:
                    parameters_properties[param_name] = {"type": param_json_type}
                    if not is_optional:
                        parameters_required.append(param_name)

            description = inspect.getdoc(func) or f"Draws a {name.replace('draw_', '')}."

            tool_spec = {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters_properties,
                    "required": parameters_required,
                },
            }
            PRIMITIVE_TOOLS.append(Tool(function_declarations=[FunctionDeclaration(**tool_spec)]))


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

    # Configure API key
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file or environment variables.")
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        sys.exit(1)

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    _load_primitive_definitions()

    model = genai.GenerativeModel('gemini-2.5-flash', tools=PRIMITIVE_TOOLS)
    print("=" * 60)
    print(f"🖼️  Function-Calling Drawing Application ({args.drawer_type.upper()} backend)")
    print("=" * 60)

    while True:
        try:
            prompt = input("\nWhat would you like me to draw? (or Ctrl+C to exit)\n> ")
            if not prompt.strip():
                continue

            print(f"Sending prompt to LLM: '{prompt}'")
            chat = model.start_chat(enable_automatic_function_calling=False)
            response = chat.send_message(prompt)

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

            # Process function calls from the LLM
            if response.candidates and response.candidates[0].content.parts:
                print("LLM is generating the drawing...")
                has_calls = False
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        has_calls = True
                        function_call = part.function_call
                        print(f"  - Executing: {function_call.name}")
                        _execute_drawing_function(drawer, function_call.name, **function_call.args)
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
