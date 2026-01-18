import os
import sys
import webbrowser
import time
import argparse
import json
import re
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.panel import Panel
from rich.align import Align
from rich.live import Live

from crytonix.llm.client import LLMClient
from crytonix.agents.manager import ManagerAgent
from crytonix.agents.planner import PlannerAgent
from crytonix.agents.coding import CodingAgent
from crytonix.agents.verification import VerificationAgent
from crytonix.agents.architect import ArchitectAgent
from crytonix.server import run_server_in_background
from crytonix.voice import VoiceManager, JervisMode, VoiceConfig, create_jervis

console = Console()
CONFIG_DIR = os.path.expanduser("~/.crytonix")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

ASCII_LOGO = r"""
   ______            __              _
  / ____/______  __ / /_ ____  ____ ( )_  __
 / /   / ___/ / / // __// __ \/ __ \|/| |/_/
/ /___/ /  / /_/ // /_ / /_/ / / / / _>  <
\____/_/   \__, / \__/ \____/_/ /_/ /_/|_|
          /____/
"""

def ensure_config():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({}, f)

def load_config():
    ensure_config()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(key, value):
    config = load_config()
    config[key] = value
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def stream_agent_response(agent, input_content, title, style):
    """Helper to stream response to a Rich Live Panel."""
    full_response = ""
    with Live(Panel("Thinking...", title=title, border_style=style), refresh_per_second=10, console=console) as live:
        for chunk in agent.chat_stream(input_content):
            full_response += chunk
            # Render Markdown dynamically
            live.update(Panel(Markdown(full_response), title=title, border_style=style))
    return full_response

def main():
    parser = argparse.ArgumentParser(description="Crytonix: The AI Coding Agent")
    parser.add_argument("-m", "--model", help="Override the LLM model")
    parser.add_argument("-p", "--provider", help="Override the LLM provider (google, groq, openrouter)")
    parser.add_argument("-i", "--image", help="Path or URL to an image for reference")
    parser.add_argument("-r", "--resume", help="Path to a history file to resume a session")
    parser.add_argument("-c", "--context", help="Comma-separated list of files/folders to include as context")
    parser.add_argument("-s", "--serve", action="store_true", help="Start a local web server after generation")
    parser.add_argument("--set-key", nargs=2, metavar=('PROVIDER', 'KEY'), help="Save an API key to config")
    parser.add_argument("--session", help="Name of the session to save/load history")
    parser.add_argument("--list-sessions", action="store_true", help="List all saved sessions")
    parser.add_argument("--voice", action="store_true", help="Enable Voice Mode (simple TTS/STT)")
    parser.add_argument("--jervis", action="store_true", help="Enable full Jervis Mode (wake word 'Hey Crytonix', continuous conversation)")
    parser.add_argument("--voice-persona", choices=["jarvis", "friday", "british", "aussie"], default="jarvis", help="Voice persona for TTS")
    parser.add_argument("--tdd", action="store_true", help="Enforce Test-Driven Development workflow")
    parser.add_argument("--dashboard", action="store_true", help="Launch the Project Health Dashboard")
    
    args = parser.parse_args()

    # Handle Dashboard
    if args.dashboard:
        from crytonix.dashboard import run_dashboard
        run_dashboard()
        sys.exit(0)

    # Handle List Sessions
    if args.list_sessions:
        sessions_dir = os.path.join(CONFIG_DIR, "sessions")
        if os.path.exists(sessions_dir):
            sessions = [d for d in os.listdir(sessions_dir) if os.path.isdir(os.path.join(sessions_dir, d))]
            if sessions:
                console.print(Panel("\n".join(sessions), title="Saved Sessions", border_style="cyan"))
            else:
                console.print("[dim]No sessions found.[/dim]")
        else:
            console.print("[dim]No sessions directory found.[/dim]")
        sys.exit(0)

    # Handle Config Updates
    if args.set_key:
        provider_key_map = {
            "google": "GOOGLE_API_KEY",
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY"
         }
        provider = args.set_key[0].lower()
        if provider not in provider_key_map:
            console.print(f"[bold red]Error:[/bold red] Unknown provider '{provider}'. Valid: google, groq, openrouter")
            sys.exit(1)
        
        save_config(provider_key_map[provider], args.set_key[1])
        console.print(f"[bold green]✓[/bold green] API key for {provider} saved to {CONFIG_FILE}")
        sys.exit(0)

    # Splash Screen
    console.print(Align.center(f"[bold cyan]{ASCII_LOGO}[/bold cyan]"))
    console.print(Align.center("[dim]The Professional AI Coding Agent[/dim]\n"))

    # Determine Provider & Model
    config = load_config()
    provider = args.provider or config.get("default_provider") or os.environ.get("CRYTONIX_PROVIDER", "google").lower()
    model = args.model or config.get("default_model")

    try:
        client = LLMClient(provider=provider, model=model)
    except Exception as e:
        console.print(f"[bold red]Initialization Error:[/bold red] {e}")
        console.print("[dim]Tip: Use --set-key to save your API keys.[/dim]")
        sys.exit(1)

    # Agents
    manager = ManagerAgent("Manager", client)
    planner = PlannerAgent("Planner", client)
    coder = CodingAgent("Coder", client)
    verifier = VerificationAgent("Verifier", client)
    architect = ArchitectAgent("Architect", client)

    # Voice / Jervis Mode Init
    voice_mgr = None
    jervis_mode = None
    jervis_active = False
    
    if args.jervis:
        # Full Jervis Mode with wake word detection
        try:
            console.print("[bold cyan]🦾 Initializing Jervis Mode...[/bold cyan]")
            jervis_mode = create_jervis(
                wake_word="hey crytonix",
                voice=args.voice_persona,
                enable_wake_word=True,
                enable_sounds=True
            )
            if jervis_mode.enabled:
                console.print("[bold green]🎤 Jervis Mode Activated[/bold green]")
                console.print("[dim]Say 'Hey Crytonix' to activate, or speak commands.[/dim]")
                jervis_active = True
                # Set voice_mgr for compatibility in main loop
                voice_mgr = type('VoiceMgrShim', (), {
                    'enabled': True,
                    'speak': jervis_mode.speak,
                    'listen': jervis_mode.listen
                })()
            else:
                console.print("[bold red]Jervis Mode Init Failed. Falling back to basic voice.[/bold red]")
                args.voice = True  # Fallback
        except Exception as e:
            console.print(f"[bold red]Jervis Mode Error:[/bold red] {e}")
            console.print("[dim]Falling back to basic voice mode...[/dim]")
            args.voice = True  # Fallback
    
    if args.voice and not jervis_active:
        # Basic voice mode (legacy)
        try:
            voice_mgr = VoiceManager()
            if voice_mgr.enabled:
                console.print("[bold green]🎤 Voice Mode Enabled (Basic)[/bold green]")
                voice_mgr.speak("Systems online. Ready for input.")
            else:
                console.print("[bold red]Voice Init Failed. Check dependencies.[/bold red]")
        except Exception:
            pass

    # Session Path Logic
    session_mgr_path = "crytonix_history_mgr.json"
    session_plan_path = "crytonix_history_plan.json"
    session_code_path = "crytonix_history_code.json"
    
    if args.session:
        session_dir = os.path.join(CONFIG_DIR, "sessions", args.session)
        os.makedirs(session_dir, exist_ok=True)
        session_mgr_path = os.path.join(session_dir, "manager.json")
        session_plan_path = os.path.join(session_dir, "planner.json")
        session_code_path = os.path.join(session_dir, "coder.json")
        
        # Auto-resume if exists
        try:
            if os.path.exists(session_mgr_path):
                manager.load_history(session_mgr_path)
                planner.load_history(session_plan_path)
                coder.load_history(session_code_path)
                console.print(f"[bold green]✓[/bold green] Loaded session '{args.session}'")
        except Exception as e:
            console.print(f"[bold red]Error loading session:[/bold red] {e}")

    # Explicit Resume History (Legacy Flag)
    if args.resume and not args.session:
        try:
            manager.load_history(f"{args.resume}_mgr.json")
            planner.load_history(f"{args.resume}_plan.json")
            coder.load_history(f"{args.resume}_code.json")
            console.print(f"[bold green]✓[/bold green] Resumed session from {args.resume}")
        except Exception as e:
            console.print(f"[bold red]Error loading history:[/bold red] {e}")

    # Load Context Files
    if args.context:
        files = [f.strip() for f in args.context.split(",")]
        manager.add_context_files(files)
        planner.add_context_files(files)
        coder.add_context_files(files)
        console.print(f"[bold green]✓[/bold green] Loaded {len(files)} context files")

    # Initial Prompt Logic
    user_request_content = []
    
    if args.image:
        console.print(f"[bold yellow]Image Input Detected:[/bold yellow] {args.image}")
        if args.image.startswith("http"):
            user_request_content.append({"type": "image_url", "image_url": {"url": args.image}})
        else:
            try:
                b64_img = client._encode_image(args.image)
                user_request_content.append({"type": "image_url", "image_url": {"url": b64_img}})
            except Exception as e:
                console.print(f"[bold red]Error loading image:[/bold red] {e}")
                sys.exit(1)

    if voice_mgr and voice_mgr.enabled:
         user_text = voice_mgr.listen("[bold green]Speak your command:[/bold green]")
    else:
         user_text = Prompt.ask("[bold green]>[/bold green]")
    
    # Inject TDD Context if enabled
    if args.tdd:
        user_text = f"[SYSTEM: TDD MODE ENABLED. Enforce Test-Driven Development.] {user_text}"

    user_request_content.append({"type": "text", "text": user_text})
    
    server_started = False
    port = 8080

    # Main Orchestration Loop
    while True:
        try:
            # 1. User -> Manager (Streaming)
            mgr_response = stream_agent_response(manager, user_request_content, "Manager", "magenta")

            # Check for Delegation Calls [CALL: Agent] ...
            call_match = re.search(r"\[CALL: (\w+)\](.*)", mgr_response, re.DOTALL)
            
            if call_match:
                agent_name = call_match.group(1).strip()
                instruction = call_match.group(2).strip()
                
                console.print(Panel(f"[bold]Delegating to {agent_name}:[/bold] {instruction[:100]}...", title="Manager Decision", border_style="magenta"))
                
                if agent_name.lower() == "planner":
                    # Stream Planner
                    plan_response = stream_agent_response(planner, instruction, "Planner Output", "blue")
                    
                    # Feedback to Manager
                    user_request_content = f"Planner Output:\n{plan_response}\n\nWhat next?"

                elif agent_name.lower() == "architect":
                    # Stream Architect
                    arch_response = stream_agent_response(architect, instruction, "Architect Output", "cyan")
                    
                    # Execute Tools
                    with console.status("Scaffolding...", spinner="earth"):
                         tool_output = architect.execute_tools(arch_response)
                    
                    if tool_output:
                         console.print(Panel(tool_output, title="Scaffold Results", border_style="white"))

                    # Feedback to Manager
                    user_request_content = f"Architect Output:\n{arch_response}\n\nTool Output:\n{tool_output}\n\nWhat next?"

                elif agent_name.lower() == "coder":
                    # Stream Coder
                    code_response = stream_agent_response(coder, instruction, "Coder Output", "yellow")
                    
                    # Execute Tools (File Writing)
                    with console.status("Executing tools...", spinner="dots"):
                         tool_output = coder.execute_tools(code_response)
                    
                    console.print(f"[bold green]Coder finished.[/bold green]")
                    if tool_output:
                         console.print(Panel(tool_output, title="Tool Output", border_style="white"))
                    
                    # Feedback to Manager
                    user_request_content = f"Coder Output:\n{code_response}\n\nTool Output:\n{tool_output}\n\nWhat next?"

                elif agent_name.lower() == "verifier":
                    # Stream Verifier
                    ver_response = stream_agent_response(verifier, instruction, "Verifier Output", "green")
                    
                    # Execute Tools (Tests/Analysis)
                    with console.status("Running verification...", spinner="dots"):
                         tool_output = verifier.execute_tools(ver_response)
                    
                    if tool_output:
                         console.print(Panel(tool_output, title="Verification Results", border_style="white"))
                    
                    # Interactive Debugger (Human-in-the-Loop)
                    if "STATUS: FAIL" in ver_response or "STATUS: FAIL" in str(tool_output):
                        console.print("[bold red]🚨 Verification Failed![/bold red]")
                        choice = Prompt.ask(
                            "How do you want to proceed?",
                            choices=["fix", "guide", "ignore"],
                            default="fix"
                        )
                        
                        if choice == "fix":
                            user_request_content = f"Verification Failed. Fix the issues:\n{ver_response}\n{tool_output}"
                        elif choice == "guide":
                            advice = Prompt.ask("Enter your guidance for the Coder")
                            user_request_content = f"Verification Failed. User Guidance: {advice}\nErrors:\n{ver_response}"
                        else:
                            user_request_content = "Ignore the errors and proceed. What next?"
                    else:
                        # Feedback to Manager
                        user_request_content = f"Verifier Output:\n{ver_response}\n\nTool Output:\n{tool_output}\n\nWhat next?"

                else:
                    console.print(f"[bold red]Unknown Agent:[/bold red] {agent_name}")
                    user_request_content = f"Error: Agent {agent_name} not found."

                if not manager_response:
                     # Fallback if streaming failed or returned empty
                     manager_response = "I have no response."
                
                if voice_mgr and voice_mgr.enabled:
                    # Speak the summary (maybe truncate code blocks for sanity)
                    voice_mgr.speak(manager_response[:200]) # Speak first 200 chars

                # Save Checkpoints
                manager.save_history(session_mgr_path)
                planner.save_history(session_plan_path)
                coder.save_history(session_code_path)

                # Optional Server
                if args.serve and not server_started:
                    port = run_server_in_background(port)
                    url = f"http://localhost:{port}"
                    console.print(f"[bold white]Starting server at {url}...[/bold white]")
                    time.sleep(1) 
                    webbrowser.open(url)
                    server_started = True
                
                # Wait for next user input
                if voice_mgr and voice_mgr.enabled:
                     next_input = voice_mgr.listen("[bold green]Speak next command:[/bold green]")
                else:
                     next_input = Prompt.ask("\n[bold green]>[/bold green]")
                
                if next_input.lower() in ["exit", "quit", "q"]:
                    console.print("[bold cyan]Goodbye![/bold cyan]")
                    sys.exit(0)
                
                user_request_content = next_input
            
        except KeyboardInterrupt:
            # Graceful exit on Ctrl+C inside loop
            console.print("\n[bold yellow]Interrupted by user.[/bold yellow]")
            if Confirm.ask("Do you want to exit?", default=True):
                 manager.save_history("crytonix_history_mgr_interrupt.json")
                 console.print("[dim]Session saved to crytonix_history_mgr_interrupt.json[/dim]")
                 sys.exit(0)
            else:
                continue
        except Exception as e:
            console.print(f"\n[bold red]Runtime Error:[/bold red] {e}")
            if Confirm.ask("Do you want to retry the last action?", default=True):
                continue
            else:
                console.print("[bold red]Exiting...[/bold red]")
                sys.exit(1)

if __name__ == "__main__":
    main()
