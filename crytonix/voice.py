"""
Crytonix Enhanced Voice Module - "Jervis Mode"
================================================
A comprehensive voice assistant with:
- Wake word detection ("Hey Crytonix")
- High-quality Edge TTS
- Voice Activity Detection
- Audio feedback (Jarvis-style sounds)
- Built-in voice commands
- Continuous conversation mode
"""

import os
import sys
import time
import queue
import threading
import tempfile
import asyncio
import hashlib
from dataclasses import dataclass
from typing import Optional, Callable, List, Tuple
from enum import Enum
from pathlib import Path

# Rich console for styled output
from rich.console import Console

console = Console()

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class VoiceConfig:
    """Voice assistant configuration."""
    wake_word: str = "hey crytonix"
    voice_name: str = "en-US-GuyNeural"  # Microsoft Edge voice
    speech_rate: str = "+0%"  # Can be -50% to +100%
    volume: float = 1.0  # 0.0 to 1.0
    listen_timeout: int = 5  # seconds
    phrase_timeout: float = 3.0  # seconds of silence to end phrase
    enable_wake_word: bool = True
    enable_sounds: bool = True
    continuous_mode: bool = True
    vad_aggressiveness: int = 2  # 0-3, higher = more aggressive filtering


class VoiceState(Enum):
    IDLE = "idle"
    LISTENING_WAKE = "listening_wake"
    LISTENING_COMMAND = "listening_command"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    PAUSED = "paused"


# ============================================================================
# AUDIO FEEDBACK SYSTEM
# ============================================================================

class AudioFeedback:
    """Manages Jarvis-style audio feedback sounds."""
    
    AUDIO_DIR = Path(__file__).parent / "audio"
    
    # Synthesized sound parameters (we'll generate these if files don't exist)
    SOUNDS = {
        "startup": {"freq": 880, "duration": 0.3, "type": "ascending"},
        "listening": {"freq": 1200, "duration": 0.15, "type": "beep"},
        "success": {"freq": 1000, "duration": 0.2, "type": "dual_ascending"},
        "error": {"freq": 400, "duration": 0.3, "type": "descending"},
        "thinking": {"freq": 600, "duration": 0.1, "type": "pulse"},
        "wake_detected": {"freq": 1400, "duration": 0.1, "type": "double_beep"},
    }
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.mixer_initialized = False
        self._init_mixer()
        self._ensure_audio_files()
    
    def _init_mixer(self):
        """Initialize pygame mixer for audio playback."""
        try:
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.mixer_initialized = True
        except Exception as e:
            console.print(f"[dim]Audio mixer init failed: {e}[/dim]")
            self.enabled = False
    
    def _ensure_audio_files(self):
        """Generate audio files if they don't exist."""
        if not self.enabled:
            return
            
        self.AUDIO_DIR.mkdir(exist_ok=True)
        
        for sound_name, params in self.SOUNDS.items():
            path = self.AUDIO_DIR / f"{sound_name}.wav"
            if not path.exists():
                self._generate_sound(path, params)
    
    def _generate_sound(self, path: Path, params: dict):
        """Generate a sound file using numpy."""
        try:
            import numpy as np
            import wave
            
            sample_rate = 22050
            duration = params["duration"]
            freq = params["freq"]
            sound_type = params["type"]
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            if sound_type == "beep":
                audio = np.sin(2 * np.pi * freq * t) * 0.5
            elif sound_type == "ascending":
                freq_sweep = np.linspace(freq * 0.5, freq, len(t))
                audio = np.sin(2 * np.pi * freq_sweep * t) * 0.5
            elif sound_type == "descending":
                freq_sweep = np.linspace(freq, freq * 0.5, len(t))
                audio = np.sin(2 * np.pi * freq_sweep * t) * 0.5
            elif sound_type == "dual_ascending":
                freq_sweep = np.linspace(freq * 0.7, freq * 1.3, len(t))
                audio = np.sin(2 * np.pi * freq_sweep * t) * 0.4
                audio += np.sin(2 * np.pi * freq_sweep * 1.5 * t) * 0.3
            elif sound_type == "double_beep":
                half = len(t) // 2
                audio = np.zeros(len(t))
                audio[:half] = np.sin(2 * np.pi * freq * t[:half]) * 0.5
                audio[half:] = np.sin(2 * np.pi * freq * 1.2 * t[half:]) * 0.5
            elif sound_type == "pulse":
                envelope = np.sin(np.pi * t / duration)
                audio = np.sin(2 * np.pi * freq * t) * envelope * 0.5
            else:
                audio = np.sin(2 * np.pi * freq * t) * 0.5
            
            # Apply fade in/out
            fade_samples = int(sample_rate * 0.02)
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            audio[:fade_samples] *= fade_in
            audio[-fade_samples:] *= fade_out
            
            # Convert to 16-bit PCM
            audio = (audio * 32767).astype(np.int16)
            
            # Write WAV file
            with wave.open(str(path), 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio.tobytes())
                
        except ImportError:
            console.print("[dim]numpy not available for sound generation[/dim]")
        except Exception as e:
            console.print(f"[dim]Sound generation failed: {e}[/dim]")
    
    def play(self, sound_name: str, block: bool = False):
        """Play a sound effect."""
        if not self.enabled or not self.mixer_initialized:
            return
            
        try:
            import pygame
            path = self.AUDIO_DIR / f"{sound_name}.wav"
            if path.exists():
                sound = pygame.mixer.Sound(str(path))
                sound.play()
                if block:
                    while pygame.mixer.get_busy():
                        time.sleep(0.01)
        except Exception as e:
            pass  # Silently fail for audio
    
    def stop_all(self):
        """Stop all playing audio."""
        if self.mixer_initialized:
            try:
                import pygame
                pygame.mixer.stop()
            except:
                pass


# ============================================================================
# WAKE WORD DETECTOR
# ============================================================================

class WakeWordDetector:
    """
    Wake word detector using OpenWakeWord or fallback to keyword spotting.
    Detects "Hey Crytonix" to activate the assistant.
    """
    
    def __init__(self, wake_phrase: str = "hey crytonix"):
        self.wake_phrase = wake_phrase.lower()
        self.oww_model = None
        self.use_oww = False
        self.use_vosk = False
        self.vosk_model = None
        self._init_detector()
    
    def _init_detector(self):
        """Initialize wake word detection system."""
        # Try OpenWakeWord first
        try:
            import openwakeword
            from openwakeword.model import Model
            
            # Use pre-trained model or custom
            self.oww_model = Model(
                wakeword_models=["hey_jarvis"],  # Similar phonetically
                inference_framework="onnx"
            )
            self.use_oww = True
            console.print("[dim]Wake word: OpenWakeWord initialized[/dim]")
            return
        except ImportError:
            pass
        except Exception as e:
            console.print(f"[dim]OpenWakeWord init failed: {e}[/dim]")
        
        # Fallback to Vosk for keyword detection
        try:
            from vosk import Model, KaldiRecognizer
            import json
            
            # Check for vosk model
            model_path = Path.home() / ".crytonix" / "vosk-model-small-en-us-0.15"
            if model_path.exists():
                self.vosk_model = Model(str(model_path))
                self.use_vosk = True
                console.print("[dim]Wake word: Vosk keyword spotting initialized[/dim]")
                return
        except ImportError:
            pass
        except Exception as e:
            console.print(f"[dim]Vosk init failed: {e}[/dim]")
        
        console.print("[yellow]Wake word detection unavailable. Using manual activation.[/yellow]")
    
    def detect_from_audio(self, audio_data: bytes, sample_rate: int = 16000) -> bool:
        """Check if audio contains wake word."""
        if self.use_oww and self.oww_model:
            try:
                import numpy as np
                # Convert bytes to numpy array
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                predictions = self.oww_model.predict(audio_array)
                
                # Check if any wake word detected above threshold
                for model_name, scores in predictions.items():
                    if max(scores) > 0.5:  # Confidence threshold
                        return True
            except Exception:
                pass
        
        return False
    
    def detect_from_text(self, text: str) -> bool:
        """Check if text contains wake phrase (fallback method)."""
        text_lower = text.lower().strip()
        
        # Check for exact or fuzzy match
        variations = [
            self.wake_phrase,
            "hey crytonix",
            "hey cryptonix", 
            "a crytonix",
            "hey cry tonics",
            "hey cryo tonics",
        ]
        
        for var in variations:
            if var in text_lower or text_lower.startswith(var.split()[0]):
                return True
        
        return False


# ============================================================================
# EDGE TTS ENGINE
# ============================================================================

class EdgeTTSEngine:
    """High-quality text-to-speech using Microsoft Edge TTS (free)."""
    
    VOICES = {
        "jarvis": "en-US-GuyNeural",       # Male, professional
        "friday": "en-US-JennyNeural",     # Female, assistant
        "british": "en-GB-RyanNeural",     # British male
        "aussie": "en-AU-WilliamNeural",   # Australian male
    }
    
    def __init__(self, voice: str = "jarvis", rate: str = "+0%"):
        self.voice = self.VOICES.get(voice, voice)
        self.rate = rate
        self.volume = 1.0
        self.cache_dir = Path(tempfile.gettempdir()) / "crytonix_tts_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.current_playback = None
        self._stop_flag = threading.Event()
        self.last_audio_path: Optional[Path] = None
        
    def set_rate(self, rate: str):
        """Set speech rate (e.g., '+20%', '-10%')."""
        self.rate = rate
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
    
    def _get_cache_path(self, text: str) -> Path:
        """Get cached audio file path for text."""
        text_hash = hashlib.md5(f"{text}:{self.voice}:{self.rate}".encode()).hexdigest()
        return self.cache_dir / f"{text_hash}.mp3"
    
    async def _generate_audio(self, text: str, output_path: Path):
        """Generate audio file from text using Edge TTS."""
        import edge_tts
        
        communicate = edge_tts.Communicate(
            text,
            voice=self.voice,
            rate=self.rate
        )
        await communicate.save(str(output_path))
    
    def speak(self, text: str, block: bool = True) -> bool:
        """
        Speak text using Edge TTS.
        Returns True if completed, False if interrupted.
        """
        if not text or not text.strip():
            return True
        
        self._stop_flag.clear()
        
        # Clean text for speech
        clean_text = self._clean_for_speech(text)
        
        try:
            # Check cache first
            cache_path = self._get_cache_path(clean_text)
            
            if not cache_path.exists():
                # Generate audio
                asyncio.run(self._generate_audio(clean_text, cache_path))
            
            self.last_audio_path = cache_path
            
            # Play audio
            return self._play_audio(cache_path, block)
            
        except ImportError:
            console.print("[red]edge-tts not installed. Run: pip install edge-tts[/red]")
            return self._fallback_speak(text)
        except Exception as e:
            console.print(f"[dim]TTS error: {e}[/dim]")
            return self._fallback_speak(text)
    
    def _clean_for_speech(self, text: str) -> str:
        """Clean text for natural speech."""
        import re
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.+?)`', r'\1', text)        # Inline code
        text = re.sub(r'```[\s\S]*?```', 'See code block.', text)  # Code blocks
        text = re.sub(r'#{1,6}\s*', '', text)         # Headers
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # Links
        
        # Clean up
        text = re.sub(r'\n{2,}', '. ', text)
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        
        return text.strip()
    
    def _play_audio(self, path: Path, block: bool) -> bool:
        """Play audio file using pygame."""
        try:
            import pygame
            
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            # Set volume
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play()
            
            if block:
                while pygame.mixer.music.get_busy():
                    if self._stop_flag.is_set():
                        pygame.mixer.music.stop()
                        return False
                    time.sleep(0.05)
            
            return True
            
        except Exception as e:
            console.print(f"[dim]Audio playback error: {e}[/dim]")
            return True
    
    def _fallback_speak(self, text: str) -> bool:
        """Fallback to pyttsx3 if Edge TTS unavailable."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text[:500])  # Limit length
            engine.runAndWait()
            return True
        except:
            console.print(f"[cyan]🔊 {text[:200]}...[/cyan]")
            return True
    
    def stop(self):
        """Stop current speech."""
        self._stop_flag.set()
        try:
            import pygame
            pygame.mixer.music.stop()
        except:
            pass
    
    def repeat_last(self) -> bool:
        """Replay the last spoken audio."""
        if self.last_audio_path and self.last_audio_path.exists():
            return self._play_audio(self.last_audio_path, block=True)
        return False


# ============================================================================
# VOICE ACTIVITY DETECTOR
# ============================================================================

class VoiceActivityDetector:
    """Detects speech in audio using Silero VAD or WebRTC VAD."""
    
    def __init__(self, aggressiveness: int = 2):
        self.aggressiveness = aggressiveness
        self.vad = None
        self.silero_model = None
        self._init_vad()
    
    def _init_vad(self):
        """Initialize VAD system."""
        # Try Silero VAD first (more accurate)
        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                trust_repo=True
            )
            self.silero_model = model
            console.print("[dim]VAD: Silero initialized[/dim]")
            return
        except Exception:
            pass
        
        # Fallback to WebRTC VAD
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(self.aggressiveness)
            console.print("[dim]VAD: WebRTC initialized[/dim]")
        except ImportError:
            console.print("[dim]VAD: No VAD available, using timeout[/dim]")
    
    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        """Check if audio chunk contains speech."""
        if self.silero_model:
            try:
                import torch
                import numpy as np
                
                audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                audio_tensor = torch.from_numpy(audio_array)
                
                confidence = self.silero_model(audio_tensor, sample_rate).item()
                return confidence > 0.5
            except:
                pass
        
        if self.vad:
            try:
                # WebRTC VAD requires specific frame lengths (10, 20, or 30 ms)
                frame_duration = 30  # ms
                frame_length = int(sample_rate * frame_duration / 1000) * 2  # bytes
                
                if len(audio_chunk) >= frame_length:
                    return self.vad.is_speech(audio_chunk[:frame_length], sample_rate)
            except:
                pass
        
        return True  # Assume speech if no VAD available


# ============================================================================
# VOICE COMMAND HANDLER
# ============================================================================

class VoiceCommandHandler:
    """Handles built-in voice commands before sending to LLM."""
    
    COMMANDS = {
        # Stop commands
        ("stop", "be quiet", "shut up", "silence", "enough"): "stop",
        # Repeat commands
        ("repeat", "repeat that", "say that again", "what did you say"): "repeat",
        # Volume commands
        ("louder", "volume up", "speak louder", "increase volume"): "volume_up",
        ("softer", "quieter", "volume down", "speak softer", "decrease volume"): "volume_down",
        # Pause/Resume
        ("pause", "wait", "hold on"): "pause",
        ("resume", "continue", "go on"): "resume",
        # Sleep/Wake
        ("go to sleep", "sleep mode", "standby"): "sleep",
        ("wake up", "i'm back", "activate"): "wake",
        # Status
        ("status", "are you there", "you there"): "status",
    }
    
    def parse(self, text: str) -> Optional[str]:
        """Parse text for voice commands. Returns command name or None."""
        text_lower = text.lower().strip()
        
        for triggers, command in self.COMMANDS.items():
            for trigger in triggers:
                if text_lower == trigger or text_lower.startswith(trigger + " "):
                    return command
        
        return None


# ============================================================================
# ADVANCED SPEECH RECOGNIZER
# ============================================================================

class SpeechRecognizer:
    """Enhanced speech recognition with VAD and multiple engines."""
    
    def __init__(self, vad: Optional[VoiceActivityDetector] = None):
        self.recognizer = None
        self.microphone = None
        self.vad = vad or VoiceActivityDetector()
        self.vosk_model = None
        self._init_recognizer()
    
    def _init_recognizer(self):
        """Initialize speech recognition."""
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise on init
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
        except Exception as e:
            console.print(f"[red]Speech recognition init failed: {e}[/red]")
    
    def listen(
        self, 
        prompt: str = "Listening...", 
        timeout: int = 5,
        phrase_timeout: float = 3.0
    ) -> Tuple[str, bool]:
        """
        Listen for speech input.
        Returns (text, success) tuple.
        """
        if not self.recognizer or not self.microphone:
            return input(f"{prompt} (mic unavailable): "), True
        
        console.print(f"[cyan]🎤 {prompt}[/cyan]")
        
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_timeout
                )
            
            console.print("[dim]Processing audio...[/dim]")
            
            # Try Google Speech Recognition first (online)
            try:
                text = self.recognizer.recognize_google(audio)
                console.print(f"[green]🗣️ You: {text}[/green]")
                return text, True
            except Exception:
                pass
            
            # Fallback to Vosk (offline)
            if self.vosk_model:
                try:
                    from vosk import KaldiRecognizer
                    import json
                    
                    rec = KaldiRecognizer(self.vosk_model, 16000)
                    rec.AcceptWaveform(audio.get_raw_data())
                    result = json.loads(rec.FinalResult())
                    text = result.get("text", "")
                    if text:
                        console.print(f"[green]🗣️ You: {text}[/green]")
                        return text, True
                except:
                    pass
            
            return "", False
            
        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower():
                return "", False
            console.print(f"[dim]Listen error: {e}[/dim]")
            return "", False


# ============================================================================
# JERVIS MODE - MAIN ORCHESTRATOR
# ============================================================================

class JervisMode:
    """
    Full Jervis Mode orchestrator.
    Combines wake word detection, speech recognition, TTS, and voice commands
    into a seamless voice assistant experience.
    """
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self.state = VoiceState.IDLE
        self.enabled = False
        
        # Components
        self.audio = AudioFeedback(enabled=self.config.enable_sounds)
        self.wake_detector = WakeWordDetector(self.config.wake_word)
        self.tts = EdgeTTSEngine(voice="jarvis", rate=self.config.speech_rate)
        self.vad = VoiceActivityDetector(self.config.vad_aggressiveness)
        self.recognizer = SpeechRecognizer(self.vad)
        self.commands = VoiceCommandHandler()
        
        # State
        self.last_response = ""
        self._stop_event = threading.Event()
        
        self._init_system()
    
    def _init_system(self):
        """Initialize the Jervis system."""
        try:
            # Check core dependencies
            import speech_recognition
            self.enabled = True
        except ImportError:
            console.print("[red]Core voice dependencies missing.[/red]")
            self.enabled = False
            return
        
        # Play startup sound
        if self.config.enable_sounds:
            self.audio.play("startup", block=True)
        
        self.speak("Systems online. Crytonix at your service.")
        self.state = VoiceState.LISTENING_WAKE if self.config.enable_wake_word else VoiceState.IDLE
    
    def speak(self, text: str, block: bool = True) -> bool:
        """Speak text with audio feedback."""
        if not text:
            return True
        
        self.state = VoiceState.SPEAKING
        self.last_response = text
        
        result = self.tts.speak(text, block=block)
        
        if result:
            self.state = VoiceState.IDLE
        
        return result
    
    def listen(self, prompt: str = "Listening...") -> str:
        """Listen for user speech with audio feedback."""
        self.state = VoiceState.LISTENING_COMMAND
        
        if self.config.enable_sounds:
            self.audio.play("listening")
        
        text, success = self.recognizer.listen(
            prompt=prompt,
            timeout=self.config.listen_timeout,
            phrase_timeout=self.config.phrase_timeout
        )
        
        if success and text:
            # Check for voice commands first
            command = self.commands.parse(text)
            if command:
                self._handle_command(command)
                return ""  # Command handled, don't pass to LLM
            
            if self.config.enable_sounds:
                self.audio.play("success")
        
        self.state = VoiceState.IDLE
        return text
    
    def listen_for_wake_word(self, timeout: float = 30.0) -> bool:
        """
        Listen continuously for wake word.
        Returns True when wake word detected.
        """
        if not self.config.enable_wake_word:
            return True
        
        self.state = VoiceState.LISTENING_WAKE
        start_time = time.time()
        
        console.print("[dim]Listening for 'Hey Crytonix'...[/dim]")
        
        while time.time() - start_time < timeout:
            if self._stop_event.is_set():
                return False
            
            text, success = self.recognizer.listen(
                prompt="",
                timeout=3,
                phrase_timeout=2.0
            )
            
            if success and text:
                if self.wake_detector.detect_from_text(text):
                    if self.config.enable_sounds:
                        self.audio.play("wake_detected")
                    console.print("[cyan]✨ Wake word detected![/cyan]")
                    return True
        
        return False
    
    def _handle_command(self, command: str):
        """Handle built-in voice command."""
        if command == "stop":
            self.tts.stop()
            self.speak("Stopping.", block=True)
            
        elif command == "repeat":
            if self.last_response:
                self.tts.repeat_last()
            else:
                self.speak("Nothing to repeat.")
                
        elif command == "volume_up":
            self.tts.set_volume(min(1.0, self.tts.volume + 0.2))
            self.speak(f"Volume increased to {int(self.tts.volume * 100)} percent.")
            
        elif command == "volume_down":
            self.tts.set_volume(max(0.1, self.tts.volume - 0.2))
            self.speak(f"Volume decreased to {int(self.tts.volume * 100)} percent.")
            
        elif command == "pause":
            self.state = VoiceState.PAUSED
            self.speak("Pausing. Say 'resume' to continue.")
            
        elif command == "resume":
            self.state = VoiceState.IDLE
            self.speak("Resuming. How can I help?")
            
        elif command == "sleep":
            self.state = VoiceState.PAUSED
            self.speak("Going to sleep. Say 'wake up' to activate.")
            
        elif command == "wake":
            self.state = VoiceState.IDLE
            if self.config.enable_sounds:
                self.audio.play("startup")
            self.speak("I'm awake. Ready for commands.")
            
        elif command == "status":
            self.speak("All systems operational. Ready to assist.")
    
    def start_continuous_mode(self, callback: Callable[[str], str]):
        """
        Start continuous conversation mode.
        
        Args:
            callback: Function that takes user input and returns response.
        """
        if not self.enabled:
            console.print("[red]Jervis mode not available.[/red]")
            return
        
        console.print("[bold cyan]🚀 Jervis Mode Activated[/bold cyan]")
        console.print("[dim]Say 'Hey Crytonix' to activate, or speak a command.[/dim]")
        console.print("[dim]Say 'exit' or 'goodbye' to quit.[/dim]\n")
        
        self._stop_event.clear()
        
        try:
            while not self._stop_event.is_set():
                # Wait for wake word if enabled
                if self.config.enable_wake_word:
                    if not self.listen_for_wake_word(timeout=60):
                        continue
                
                # Listen for command
                user_input = self.listen("What can I do for you?")
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ["exit", "quit", "goodbye", "bye"]:
                    self.speak("Goodbye! Shutting down Jervis mode.")
                    break
                
                # Show thinking indicator
                self.state = VoiceState.PROCESSING
                if self.config.enable_sounds:
                    self.audio.play("thinking")
                
                # Get response from callback (e.g., LLM)
                try:
                    response = callback(user_input)
                    self.speak(response)
                except Exception as e:
                    if self.config.enable_sounds:
                        self.audio.play("error")
                    self.speak(f"I encountered an error: {str(e)[:100]}")
                
                self.state = VoiceState.IDLE
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Jervis mode interrupted.[/yellow]")
        finally:
            self._stop_event.set()
            self.state = VoiceState.IDLE
    
    def stop(self):
        """Stop Jervis mode."""
        self._stop_event.set()
        self.tts.stop()
        self.audio.stop_all()


# ============================================================================
# LEGACY COMPATIBILITY LAYER
# ============================================================================

class VoiceManager:
    """
    Backward-compatible voice manager.
    Wraps JervisMode for existing code that uses the old interface.
    """
    
    def __init__(self):
        self.tts_engine = None
        self.r = None
        self.mic = None
        self.enabled = False
        self.jervis: Optional[JervisMode] = None
        
        # Try to initialize Jervis mode
        try:
            self.jervis = JervisMode(VoiceConfig(
                enable_wake_word=False,  # Disable for legacy mode
                enable_sounds=True,
                continuous_mode=False
            ))
            self.enabled = self.jervis.enabled
        except Exception as e:
            console.print(f"[dim]Jervis init failed, trying legacy: {e}[/dim]")
            self._init_legacy()
    
    def _init_legacy(self):
        """Legacy initialization using pyttsx3."""
        try:
            import pyttsx3
            import speech_recognition as sr
            
            self.tts_engine = pyttsx3.init()
            self.r = sr.Recognizer()
            self.mic = sr.Microphone()
            self.enabled = True
        except ImportError as e:
            console.print(f"[dim]Voice dependencies missing: {e}[/dim]")
        except Exception as e:
            console.print(f"[dim]Voice initialization error: {e}[/dim]")
    
    def speak(self, text: str):
        """Speak text."""
        if not self.enabled or not text:
            return
        
        if self.jervis:
            self.jervis.speak(text, block=True)
        elif self.tts_engine:
            try:
                clean_text = text.replace("*", "").replace("#", "").replace("`", "")
                self.tts_engine.say(clean_text)
                self.tts_engine.runAndWait()
            except:
                pass
    
    def listen(self, prompt_text: str = "Listening...") -> str:
        """Listen for voice input."""
        if not self.enabled:
            return input(f"{prompt_text} (Voice disabled): ")
        
        if self.jervis:
            return self.jervis.listen(prompt_text)
        
        # Legacy listen
        console.print(f"[cyan]🎤 {prompt_text}[/cyan]")
        try:
            with self.mic as source:
                self.r.adjust_for_ambient_noise(source)
                audio = self.r.listen(source, timeout=5)
            
            console.print("[dim]Processing audio...[/dim]")
            text = self.r.recognize_google(audio)
            console.print(f"[green]🗣️ You said: {text}[/green]")
            return text
        except Exception as e:
            console.print(f"[dim]Listening failed: {e}[/dim]")
            return input("Fallback Input: ")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_jervis(
    wake_word: str = "hey crytonix",
    voice: str = "jarvis",
    enable_wake_word: bool = True,
    enable_sounds: bool = True
) -> JervisMode:
    """Factory function to create a configured Jervis instance."""
    config = VoiceConfig(
        wake_word=wake_word,
        enable_wake_word=enable_wake_word,
        enable_sounds=enable_sounds
    )
    jervis = JervisMode(config)
    jervis.tts = EdgeTTSEngine(voice=voice)
    return jervis


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    console.print("[bold cyan]Testing Jervis Mode...[/bold cyan]\n")
    
    # Test basic functionality
    def test_callback(user_input: str) -> str:
        return f"I heard you say: {user_input}. This is a test response."
    
    jervis = create_jervis(
        wake_word="hey crytonix",
        enable_wake_word=False,  # Disable for quick testing
        enable_sounds=True
    )
    
    if jervis.enabled:
        # Test single interaction
        jervis.speak("Hello! Jervis mode is working. Say something.")
        text = jervis.listen("Go ahead...")
        if text:
            jervis.speak(f"You said: {text}")
        
        console.print("\n[green]✓ Jervis mode test complete![/green]")
    else:
        console.print("[red]✗ Jervis mode initialization failed.[/red]")
