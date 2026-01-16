"""
Crytonix Voice Mode GUI - Premium Voice Assistant Interface
============================================================
A modern, futuristic GUI for the Jervis Mode voice assistant.
Features animated voice orb, real-time status, and smooth animations.
"""

import tkinter as tk
from tkinter import messagebox
import threading
import math
import time
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Try to import customtkinter for modern look, fallback to tkinter
try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    HAS_CTK = True
except ImportError:
    HAS_CTK = False
    ctk = tk  # Fallback

# Import voice module
try:
    from .voice import JervisMode, VoiceConfig, VoiceState
except ImportError:
    try:
        from voice import JervisMode, VoiceConfig, VoiceState
    except ImportError:
        JervisMode = None
        VoiceConfig = None
        VoiceState = None


# ============================================================================
# COLOR PALETTE - Cyberpunk/Jarvis Theme
# ============================================================================

class Colors:
    """Premium dark theme color palette."""
    # Backgrounds
    BG_DARK = "#0a0a0f"
    BG_CARD = "#12121a"
    BG_HOVER = "#1a1a24"
    
    # Accents
    CYAN = "#00d4ff"
    CYAN_DIM = "#006680"  # Dimmed cyan for glow effect
    CYAN_DARK = "#003344"  # Darker cyan
    PURPLE = "#a855f7"
    PURPLE_DIM = "#5c2d91"  # Dimmed purple for glow
    PURPLE_DARK = "#3d1a6d"  # Darker purple
    MAGENTA = "#ec4899"
    GREEN = "#22c55e"
    RED = "#ef4444"
    ORANGE = "#f97316"
    ORANGE_DIM = "#7d3a0b"  # Dimmed orange
    
    # Text
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_DIM = "#64748b"
    
    # Borders
    BORDER = "#1e293b"
    BORDER_ACCENT = "#334155"


# ============================================================================
# ANIMATED VOICE ORB
# ============================================================================

class VoiceOrb(tk.Canvas):
    """
    Animated voice visualization orb.
    Pulses, glows, and animates based on voice state.
    """
    
    def __init__(self, parent, size: int = 200, **kwargs):
        super().__init__(
            parent, 
            width=size, 
            height=size, 
            bg=Colors.BG_DARK,
            highlightthickness=0,
            **kwargs
        )
        
        self.size = size
        self.center = size // 2
        self.base_radius = size // 4
        self.current_radius = self.base_radius
        self.target_radius = self.base_radius
        
        # Animation state
        self.state = "idle"  # idle, listening, processing, speaking
        self.phase = 0.0
        self.glow_intensity = 0.0
        self.pulse_rings = []
        
        # Colors based on state (primary, dim, dark)
        self.colors = {
            "idle": (Colors.CYAN, Colors.CYAN_DIM, Colors.CYAN_DARK),
            "listening": (Colors.CYAN, Colors.CYAN_DIM, Colors.CYAN_DARK),
            "processing": (Colors.ORANGE, Colors.ORANGE_DIM, Colors.BG_DARK),
            "speaking": (Colors.PURPLE, Colors.PURPLE_DIM, Colors.PURPLE_DARK),
        }
        
        self._running = True
        self._animate()
    
    def set_state(self, state: str):
        """Set the orb animation state."""
        self.state = state
        if state == "listening":
            self.target_radius = self.base_radius * 1.2
        elif state == "speaking":
            self.target_radius = self.base_radius * 1.1
        elif state == "processing":
            self.target_radius = self.base_radius * 0.9
        else:
            self.target_radius = self.base_radius
    
    def _animate(self):
        """Main animation loop."""
        if not self._running:
            return
        
        self.delete("all")
        self.phase += 0.05
        
        # Smooth radius transition
        self.current_radius += (self.target_radius - self.current_radius) * 0.1
        
        color, dim_color, dark_color = self.colors.get(self.state, self.colors["idle"])
        
        # Draw outer glow rings
        self._draw_glow_rings(color, dim_color, dark_color)
        
        # Draw pulsing rings for listening state
        if self.state == "listening":
            self._draw_pulse_rings(color)
        
        # Draw main orb with gradient effect
        self._draw_orb(color, dim_color, dark_color)
        
        # Draw inner details
        self._draw_inner_details(color)
        
        # Schedule next frame (~60fps)
        self.after(16, self._animate)
    
    def _draw_glow_rings(self, color: str, dim_color: str, dark_color: str):
        """Draw outer glow effect using layered rings."""
        ring_colors = [dark_color, dim_color, dark_color]
        for i in range(3):
            radius = self.current_radius + 20 + i * 15
            pulse = math.sin(self.phase + i * 0.5) * 5
            radius += pulse
            
            # Use progressively dimmer colors for outer rings
            ring_color = ring_colors[i] if i < len(ring_colors) else dark_color
            self.create_oval(
                self.center - radius, self.center - radius,
                self.center + radius, self.center + radius,
                outline=ring_color,
                width=2 - i * 0.5 if i < 2 else 1,
                tags="glow"
            )
    
    def _draw_pulse_rings(self, color: str):
        """Draw expanding pulse rings for listening state."""
        # Add new pulse ring periodically
        if int(self.phase * 10) % 20 == 0:
            self.pulse_rings.append({"radius": self.current_radius, "alpha": 1.0})
        
        # Update and draw pulse rings
        new_rings = []
        for ring in self.pulse_rings:
            ring["radius"] += 2
            ring["alpha"] -= 0.02
            
            if ring["alpha"] > 0:
                new_rings.append(ring)
                self.create_oval(
                    self.center - ring["radius"], self.center - ring["radius"],
                    self.center + ring["radius"], self.center + ring["radius"],
                    outline=color,
                    width=1,
                    tags="pulse"
                )
        
        self.pulse_rings = new_rings[:10]  # Limit rings
    
    def _draw_orb(self, color: str, dim_color: str, dark_color: str):
        """Draw the main orb with gradient effect."""
        # Create layered circles for gradient effect
        layers = 5
        layer_colors = [dark_color, dark_color, dim_color, dim_color, color]
        for i in range(layers):
            factor = 1 - (i / layers)
            radius = self.current_radius * factor
            
            # Breathing animation
            breath = math.sin(self.phase * 0.5) * 3 * factor
            radius += breath
            
            layer_color = layer_colors[i] if i < len(layer_colors) else color
            self.create_oval(
                self.center - radius, self.center - radius,
                self.center + radius, self.center + radius,
                fill=layer_color,
                outline="",
                tags="orb"
            )
    
    def _draw_inner_details(self, color: str):
        """Draw inner orb details and decorations."""
        # Rotating lines for processing state
        if self.state == "processing":
            for i in range(8):
                angle = self.phase * 2 + i * (math.pi / 4)
                r1 = self.current_radius * 0.3
                r2 = self.current_radius * 0.7
                
                x1 = self.center + math.cos(angle) * r1
                y1 = self.center + math.sin(angle) * r1
                x2 = self.center + math.cos(angle) * r2
                y2 = self.center + math.sin(angle) * r2
                
                self.create_line(x1, y1, x2, y2, fill=color, width=2, tags="detail")
        
        # Sound wave visualization for speaking
        elif self.state == "speaking":
            for i in range(5):
                height = math.sin(self.phase * 3 + i) * 15 + 10
                x = self.center - 20 + i * 10
                self.create_rectangle(
                    x, self.center - height,
                    x + 6, self.center + height,
                    fill=color,
                    outline="",
                    tags="wave"
                )
    
    def stop(self):
        """Stop the animation."""
        self._running = False


# ============================================================================
# STATUS INDICATOR
# ============================================================================

class StatusIndicator(tk.Frame if not HAS_CTK else ctk.CTkFrame):
    """Status indicator showing current voice state."""
    
    def __init__(self, parent, **kwargs):
        if HAS_CTK:
            super().__init__(parent, fg_color=Colors.BG_CARD, corner_radius=10, **kwargs)
        else:
            super().__init__(parent, bg=Colors.BG_CARD, **kwargs)
        
        self.status_dot = tk.Canvas(
            self, width=12, height=12, 
            bg=Colors.BG_CARD, highlightthickness=0
        )
        self.status_dot.pack(side="left", padx=(10, 5), pady=10)
        self._draw_dot(Colors.TEXT_DIM)
        
        if HAS_CTK:
            self.status_label = ctk.CTkLabel(
                self, text="Ready", 
                text_color=Colors.TEXT_SECONDARY,
                font=("Segoe UI", 14)
            )
        else:
            self.status_label = tk.Label(
                self, text="Ready",
                fg=Colors.TEXT_SECONDARY,
                bg=Colors.BG_CARD,
                font=("Segoe UI", 14)
            )
        self.status_label.pack(side="left", padx=(0, 10), pady=10)
    
    def _draw_dot(self, color: str):
        """Draw the status dot."""
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 10, 10, fill=color, outline="")
    
    def set_status(self, status: str, color: str = None):
        """Update the status display."""
        status_colors = {
            "Ready": Colors.TEXT_DIM,
            "Listening...": Colors.CYAN,
            "Processing...": Colors.ORANGE,
            "Speaking...": Colors.PURPLE,
            "Wake Word Active": Colors.GREEN,
        }
        
        color = color or status_colors.get(status, Colors.TEXT_DIM)
        self._draw_dot(color)
        
        if HAS_CTK:
            self.status_label.configure(text=status)
        else:
            self.status_label.config(text=status)


# ============================================================================
# CHAT DISPLAY
# ============================================================================

class ChatDisplay(tk.Frame if not HAS_CTK else ctk.CTkFrame):
    """Scrollable chat history display."""
    
    def __init__(self, parent, **kwargs):
        if HAS_CTK:
            super().__init__(parent, fg_color=Colors.BG_CARD, corner_radius=10, **kwargs)
        else:
            super().__init__(parent, bg=Colors.BG_CARD, **kwargs)
        
        # Create scrollable text area
        if HAS_CTK:
            self.text = ctk.CTkTextbox(
                self, 
                fg_color=Colors.BG_DARK,
                text_color=Colors.TEXT_PRIMARY,
                font=("Consolas", 12),
                wrap="word",
                state="disabled"
            )
        else:
            self.text = tk.Text(
                self,
                bg=Colors.BG_DARK,
                fg=Colors.TEXT_PRIMARY,
                font=("Consolas", 12),
                wrap="word",
                state="disabled",
                relief="flat",
                padx=10,
                pady=10
            )
        self.text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure tags for styling
        if not HAS_CTK:
            self.text.tag_configure("user", foreground=Colors.CYAN)
            self.text.tag_configure("ai", foreground=Colors.PURPLE)
            self.text.tag_configure("system", foreground=Colors.TEXT_DIM)
    
    def add_message(self, role: str, message: str):
        """Add a message to the chat display."""
        if HAS_CTK:
            self.text.configure(state="normal")
        else:
            self.text.config(state="normal")
        
        prefix = "🎤 You: " if role == "user" else "🤖 Crytonix: " if role == "ai" else "⚙️ "
        tag = role if not HAS_CTK else None
        
        self.text.insert("end", f"\n{prefix}{message}\n", tag)
        self.text.see("end")
        
        if HAS_CTK:
            self.text.configure(state="disabled")
        else:
            self.text.config(state="disabled")
    
    def clear(self):
        """Clear the chat display."""
        if HAS_CTK:
            self.text.configure(state="normal")
            self.text.delete("1.0", "end")
            self.text.configure(state="disabled")
        else:
            self.text.config(state="normal")
            self.text.delete("1.0", "end")
            self.text.config(state="disabled")


# ============================================================================
# CONTROL PANEL
# ============================================================================

class ControlPanel(tk.Frame if not HAS_CTK else ctk.CTkFrame):
    """Control panel with buttons and settings."""
    
    def __init__(self, parent, on_start=None, on_stop=None, on_settings=None, **kwargs):
        if HAS_CTK:
            super().__init__(parent, fg_color=Colors.BG_CARD, corner_radius=10, **kwargs)
        else:
            super().__init__(parent, bg=Colors.BG_CARD, **kwargs)
        
        self.on_start = on_start
        self.on_stop = on_stop
        self.is_active = False
        
        # Main action button
        if HAS_CTK:
            self.action_btn = ctk.CTkButton(
                self,
                text="🎤 Start Voice Mode",
                command=self._toggle_voice,
                fg_color=Colors.CYAN,
                hover_color="#00a8cc",
                text_color=Colors.BG_DARK,
                font=("Segoe UI Bold", 14),
                height=50,
                corner_radius=25
            )
        else:
            self.action_btn = tk.Button(
                self,
                text="🎤 Start Voice Mode",
                command=self._toggle_voice,
                bg=Colors.CYAN,
                fg=Colors.BG_DARK,
                font=("Segoe UI Bold", 14),
                relief="flat",
                padx=20,
                pady=10
            )
        self.action_btn.pack(fill="x", padx=20, pady=(20, 10))
        
        # Settings row
        settings_frame = tk.Frame(self, bg=Colors.BG_CARD) if not HAS_CTK else ctk.CTkFrame(self, fg_color=Colors.BG_CARD)
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        # Volume control
        vol_label = tk.Label(settings_frame, text="🔊 Volume", fg=Colors.TEXT_SECONDARY, bg=Colors.BG_CARD, font=("Segoe UI", 11))
        vol_label.pack(side="left")
        
        if HAS_CTK:
            self.volume_slider = ctk.CTkSlider(
                settings_frame,
                from_=0, to=100,
                number_of_steps=20,
                fg_color=Colors.BORDER,
                progress_color=Colors.CYAN,
                button_color=Colors.CYAN,
                button_hover_color="#00a8cc"
            )
            self.volume_slider.set(80)
        else:
            self.volume_slider = tk.Scale(
                settings_frame,
                from_=0, to=100,
                orient="horizontal",
                bg=Colors.BG_CARD,
                fg=Colors.TEXT_PRIMARY,
                troughcolor=Colors.BORDER,
                highlightthickness=0,
                showvalue=False
            )
            self.volume_slider.set(80)
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=10)
        
        # Voice selection
        voice_frame = tk.Frame(self, bg=Colors.BG_CARD) if not HAS_CTK else ctk.CTkFrame(self, fg_color=Colors.BG_CARD)
        voice_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        voice_label = tk.Label(voice_frame, text="🗣️ Voice", fg=Colors.TEXT_SECONDARY, bg=Colors.BG_CARD, font=("Segoe UI", 11))
        voice_label.pack(side="left")
        
        voices = ["Jarvis (Male)", "Friday (Female)", "British", "Australian"]
        if HAS_CTK:
            self.voice_dropdown = ctk.CTkOptionMenu(
                voice_frame,
                values=voices,
                fg_color=Colors.BG_DARK,
                button_color=Colors.BORDER_ACCENT,
                button_hover_color=Colors.BG_HOVER,
                dropdown_fg_color=Colors.BG_CARD,
                dropdown_hover_color=Colors.BG_HOVER
            )
        else:
            self.voice_var = tk.StringVar(value=voices[0])
            self.voice_dropdown = tk.OptionMenu(voice_frame, self.voice_var, *voices)
            self.voice_dropdown.config(bg=Colors.BG_DARK, fg=Colors.TEXT_PRIMARY, highlightthickness=0)
        self.voice_dropdown.pack(side="right", padx=10)
        
        # Wake word toggle
        wake_frame = tk.Frame(self, bg=Colors.BG_CARD) if not HAS_CTK else ctk.CTkFrame(self, fg_color=Colors.BG_CARD)
        wake_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        wake_label = tk.Label(wake_frame, text="✨ Wake Word", fg=Colors.TEXT_SECONDARY, bg=Colors.BG_CARD, font=("Segoe UI", 11))
        wake_label.pack(side="left")
        
        if HAS_CTK:
            self.wake_switch = ctk.CTkSwitch(
                wake_frame,
                text="Hey Crytonix",
                text_color=Colors.TEXT_DIM,
                fg_color=Colors.BORDER,
                progress_color=Colors.CYAN,
                button_color=Colors.TEXT_PRIMARY,
                button_hover_color=Colors.CYAN
            )
        else:
            self.wake_var = tk.BooleanVar(value=False)
            self.wake_switch = tk.Checkbutton(
                wake_frame, text="Hey Crytonix",
                variable=self.wake_var,
                bg=Colors.BG_CARD, fg=Colors.TEXT_DIM,
                selectcolor=Colors.BG_DARK
            )
        self.wake_switch.pack(side="right", padx=10)
    
    def _toggle_voice(self):
        """Toggle voice mode on/off."""
        if self.is_active:
            self.is_active = False
            if HAS_CTK:
                self.action_btn.configure(
                    text="🎤 Start Voice Mode",
                    fg_color=Colors.CYAN
                )
            else:
                self.action_btn.config(text="🎤 Start Voice Mode", bg=Colors.CYAN)
            if self.on_stop:
                self.on_stop()
        else:
            self.is_active = True
            if HAS_CTK:
                self.action_btn.configure(
                    text="⏹️ Stop Voice Mode",
                    fg_color=Colors.RED
                )
            else:
                self.action_btn.config(text="⏹️ Stop Voice Mode", bg=Colors.RED)
            if self.on_start:
                self.on_start()


# ============================================================================
# MAIN VOICE GUI WINDOW
# ============================================================================

class VoiceGUI:
    """
    Main Voice Mode GUI Window.
    Premium, futuristic interface for the Crytonix voice assistant.
    """
    
    def __init__(self, callback: Optional[Callable[[str], str]] = None):
        """
        Initialize the Voice GUI.
        
        Args:
            callback: Function that takes user input and returns AI response.
        """
        self.callback = callback or self._default_callback
        self.jervis: Optional[JervisMode] = None
        self.voice_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Create main window
        if HAS_CTK:
            self.root = ctk.CTk()
            self.root.configure(fg_color=Colors.BG_DARK)
        else:
            self.root = tk.Tk()
            self.root.configure(bg=Colors.BG_DARK)
        
        self.root.title("Crytonix Voice Mode")
        self.root.geometry("450x700")
        self.root.minsize(400, 600)
        
        # Set window icon if available
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        self._build_ui()
        self._init_voice()
    
    def _build_ui(self):
        """Build the main UI."""
        # Header
        header_frame = tk.Frame(self.root, bg=Colors.BG_DARK) if not HAS_CTK else ctk.CTkFrame(self.root, fg_color=Colors.BG_DARK)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        if HAS_CTK:
            title = ctk.CTkLabel(
                header_frame,
                text="CRYTONIX",
                text_color=Colors.CYAN,
                font=("Segoe UI Black", 28)
            )
        else:
            title = tk.Label(
                header_frame,
                text="CRYTONIX",
                fg=Colors.CYAN,
                bg=Colors.BG_DARK,
                font=("Segoe UI Black", 28)
            )
        title.pack()
        
        if HAS_CTK:
            subtitle = ctk.CTkLabel(
                header_frame,
                text="Voice Assistant",
                text_color=Colors.TEXT_DIM,
                font=("Segoe UI", 12)
            )
        else:
            subtitle = tk.Label(
                header_frame,
                text="Voice Assistant",
                fg=Colors.TEXT_DIM,
                bg=Colors.BG_DARK,
                font=("Segoe UI", 12)
            )
        subtitle.pack()
        
        # Voice Orb
        orb_frame = tk.Frame(self.root, bg=Colors.BG_DARK)
        orb_frame.pack(pady=20)
        
        self.orb = VoiceOrb(orb_frame, size=200)
        self.orb.pack()
        
        # Status Indicator
        self.status = StatusIndicator(self.root)
        self.status.pack(fill="x", padx=20, pady=10)
        
        # Chat Display
        self.chat = ChatDisplay(self.root)
        self.chat.pack(fill="both", expand=True, padx=20, pady=10)
        self.chat.add_message("system", "Welcome to Crytonix Voice Mode! Click 'Start Voice Mode' to begin.")
        
        # Control Panel
        self.controls = ControlPanel(
            self.root,
            on_start=self._start_voice,
            on_stop=self._stop_voice
        )
        self.controls.pack(fill="x", padx=20, pady=(10, 20))
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _init_voice(self):
        """Initialize the voice system."""
        if JervisMode is None:
            self.chat.add_message("system", "⚠️ Voice module not available. Install dependencies with: pip install -r requirements-voice.txt")
            return
        
        try:
            config = VoiceConfig(
                enable_wake_word=False,
                enable_sounds=True,
                continuous_mode=False
            )
            self.jervis = JervisMode(config)
            
            if self.jervis.enabled:
                self.chat.add_message("system", "✅ Voice system initialized successfully!")
            else:
                self.chat.add_message("system", "⚠️ Voice system partially initialized. Some features may be unavailable.")
        except Exception as e:
            self.chat.add_message("system", f"❌ Voice initialization failed: {str(e)}")
    
    def _start_voice(self):
        """Start voice mode."""
        if not self.jervis or not self.jervis.enabled:
            self.chat.add_message("system", "❌ Voice system not available.")
            return
        
        self._running = True
        self.status.set_status("Listening...", Colors.CYAN)
        self.orb.set_state("listening")
        
        # Start voice thread
        self.voice_thread = threading.Thread(target=self._voice_loop, daemon=True)
        self.voice_thread.start()
        
        self.chat.add_message("system", "🎤 Voice mode started. Speak your command...")
    
    def _stop_voice(self):
        """Stop voice mode."""
        self._running = False
        
        if self.jervis:
            self.jervis.stop()
        
        self.status.set_status("Ready", Colors.TEXT_DIM)
        self.orb.set_state("idle")
        self.chat.add_message("system", "⏹️ Voice mode stopped.")
    
    def _voice_loop(self):
        """Main voice interaction loop."""
        while self._running and self.jervis:
            try:
                # Update UI to listening state
                self.root.after(0, lambda: self.orb.set_state("listening"))
                self.root.after(0, lambda: self.status.set_status("Listening...", Colors.CYAN))
                
                # Listen for input
                user_input = self.jervis.listen("Speak now...")
                
                if not user_input or not self._running:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ["exit", "quit", "goodbye", "bye", "stop"]:
                    self.root.after(0, lambda: self._stop_voice())
                    self.root.after(0, lambda: self.controls._toggle_voice())
                    break
                
                # Add user message to chat
                self.root.after(0, lambda msg=user_input: self.chat.add_message("user", msg))
                
                # Processing state
                self.root.after(0, lambda: self.orb.set_state("processing"))
                self.root.after(0, lambda: self.status.set_status("Processing...", Colors.ORANGE))
                
                # Get response
                response = self.callback(user_input)
                
                # Add AI response to chat
                self.root.after(0, lambda msg=response: self.chat.add_message("ai", msg))
                
                # Speaking state
                self.root.after(0, lambda: self.orb.set_state("speaking"))
                self.root.after(0, lambda: self.status.set_status("Speaking...", Colors.PURPLE))
                
                # Speak response
                if self.jervis and self._running:
                    self.jervis.speak(response)
                
            except Exception as e:
                self.root.after(0, lambda err=str(e): self.chat.add_message("system", f"❌ Error: {err}"))
        
        # Reset state when loop ends
        self.root.after(0, lambda: self.orb.set_state("idle"))
        self.root.after(0, lambda: self.status.set_status("Ready", Colors.TEXT_DIM))
    
    def _default_callback(self, user_input: str) -> str:
        """Default callback when no LLM is connected."""
        return f"I heard: '{user_input}'. Connect an LLM callback for intelligent responses."
    
    def _on_close(self):
        """Handle window close."""
        self._running = False
        if self.jervis:
            self.jervis.stop()
        self.orb.stop()
        self.root.destroy()
    
    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()
    
    def set_callback(self, callback: Callable[[str], str]):
        """Set the response callback function."""
        self.callback = callback


# ============================================================================
# COMPACT FLOATING WIDGET
# ============================================================================

class VoiceWidget:
    """
    Compact floating voice widget.
    Minimal always-on-top interface for quick voice interactions.
    """
    
    def __init__(self, callback: Optional[Callable[[str], str]] = None):
        self.callback = callback or (lambda x: f"Echo: {x}")
        self.jervis: Optional[JervisMode] = None
        self._running = False
        
        # Create compact window
        if HAS_CTK:
            self.root = ctk.CTk()
            self.root.configure(fg_color=Colors.BG_DARK)
        else:
            self.root = tk.Tk()
            self.root.configure(bg=Colors.BG_DARK)
        
        self.root.title("Crytonix")
        self.root.geometry("120x120")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)  # Frameless
        
        self._build_ui()
        self._make_draggable()
        self._init_voice()
    
    def _build_ui(self):
        """Build compact UI."""
        # Small orb
        self.orb = VoiceOrb(self.root, size=100)
        self.orb.pack(padx=10, pady=10)
        
        # Click to toggle
        self.orb.bind("<Button-1>", self._toggle_voice)
        
        # Right click to close
        self.orb.bind("<Button-3>", lambda e: self._on_close())
    
    def _make_draggable(self):
        """Make window draggable."""
        self._drag_data = {"x": 0, "y": 0}
        
        def start_drag(event):
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
        
        def do_drag(event):
            x = self.root.winfo_x() - self._drag_data["x"] + event.x
            y = self.root.winfo_y() - self._drag_data["y"] + event.y
            self.root.geometry(f"+{x}+{y}")
        
        self.root.bind("<Button-1>", start_drag)
        self.root.bind("<B1-Motion>", do_drag)
    
    def _init_voice(self):
        """Initialize voice."""
        if JervisMode:
            try:
                self.jervis = JervisMode(VoiceConfig(
                    enable_wake_word=False,
                    enable_sounds=True
                ))
            except:
                pass
    
    def _toggle_voice(self, event=None):
        """Toggle voice mode."""
        if self._running:
            self._running = False
            self.orb.set_state("idle")
            if self.jervis:
                self.jervis.stop()
        else:
            self._running = True
            self.orb.set_state("listening")
            threading.Thread(target=self._voice_interaction, daemon=True).start()
    
    def _voice_interaction(self):
        """Single voice interaction."""
        if not self.jervis:
            return
        
        user_input = self.jervis.listen()
        if user_input:
            self.orb.set_state("processing")
            response = self.callback(user_input)
            self.orb.set_state("speaking")
            self.jervis.speak(response)
        
        self._running = False
        self.root.after(0, lambda: self.orb.set_state("idle"))
    
    def _on_close(self):
        """Close widget."""
        self._running = False
        if self.jervis:
            self.jervis.stop()
        self.orb.stop()
        self.root.destroy()
    
    def run(self):
        """Start widget."""
        self.root.mainloop()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def launch_voice_gui(callback: Optional[Callable[[str], str]] = None, compact: bool = False):
    """
    Launch the Voice Mode GUI.
    
    Args:
        callback: Function that processes user input and returns response
        compact: If True, launch compact floating widget instead of full GUI
    
    Returns:
        The GUI instance
    """
    if compact:
        gui = VoiceWidget(callback)
    else:
        gui = VoiceGUI(callback)
    
    gui.run()
    return gui


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crytonix Voice Mode GUI")
    parser.add_argument("--compact", "-c", action="store_true", help="Launch compact floating widget")
    args = parser.parse_args()
    
    # Demo callback
    def demo_callback(user_input: str) -> str:
        responses = {
            "hello": "Hello! I'm Crytonix, your voice assistant. How can I help you today?",
            "time": f"The current time is displayed on your screen.",
            "help": "I can help with coding tasks, answer questions, and assist with your projects.",
        }
        
        for key, response in responses.items():
            if key in user_input.lower():
                return response
        
        return f"I understood: '{user_input}'. Connect me to an LLM for intelligent responses!"
    
    launch_voice_gui(callback=demo_callback, compact=args.compact)
