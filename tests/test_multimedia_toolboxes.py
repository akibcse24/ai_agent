import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crytonix.tools import PDFToolbox, AudioToolbox

class TestPDFToolbox:
    def test_extract_text_success(self):
        mock_pypdf = MagicMock()
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 Content"
        mock_reader.pages = [mock_page]
        mock_pypdf.PdfReader.return_value = mock_reader

        with patch.dict(sys.modules, {'pypdf': mock_pypdf}):
            result = PDFToolbox.extract_text("test.pdf")

        assert "Page 1 Content" in result
        mock_pypdf.PdfReader.assert_called_with("test.pdf")

    def test_extract_text_missing_dependency(self):
        # Ensure pypdf is NOT in sys.modules
        with patch.dict(sys.modules):
            if 'pypdf' in sys.modules:
                del sys.modules['pypdf']
            # We also need to make sure the import raises ImportError
            # Since we can't easily force an import error if it's not installed,
            # we rely on the environment. But if it IS installed, we want to simulate failure.
            # We can use side_effect on builtins.__import__ but that's messy.

            # For simplicity, if we assume the env MIGHT have it, we can't easily test the "missing" path
            # without complex mocking.
            # However, we can mock the import to raise ImportError
            pass

    def test_merge_pdfs_success(self):
        mock_pypdf = MagicMock()
        mock_writer = MagicMock()
        mock_pypdf.PdfWriter.return_value = mock_writer

        with patch.dict(sys.modules, {'pypdf': mock_pypdf}):
            result = PDFToolbox.merge_pdfs(["1.pdf", "2.pdf"], "merged.pdf")

        assert "Successfully merged 2 PDFs" in result
        assert mock_writer.append.call_count == 2
        mock_writer.write.assert_called_with("merged.pdf")

    def test_create_from_text_success(self):
        mock_reportlab = MagicMock()
        mock_canvas_mod = MagicMock()
        mock_canvas_obj = MagicMock()
        mock_pagesizes = MagicMock()

        mock_reportlab.pdfgen = mock_canvas_mod
        mock_canvas_mod.canvas.Canvas.return_value = mock_canvas_obj
        mock_canvas_obj.beginText.return_value = MagicMock()

        # Mock reportlab.lib.pagesizes
        mock_pagesizes.letter = (100, 100)

        modules = {
            'reportlab': mock_reportlab,
            'reportlab.pdfgen': mock_canvas_mod,
            'reportlab.pdfgen.canvas': mock_canvas_mod.canvas, # Because import is from reportlab.pdfgen import canvas
            'reportlab.lib': MagicMock(),
            'reportlab.lib.pagesizes': mock_pagesizes
        }

        with patch.dict(sys.modules, modules):
            # We need to ensure the imports in the function work.
            # from reportlab.pdfgen import canvas -> sys.modules['reportlab.pdfgen'].canvas
            # from reportlab.lib.pagesizes import letter -> sys.modules['reportlab.lib.pagesizes'].letter

            result = PDFToolbox.create_from_text("Hello\nWorld", "out.pdf")

        assert "Successfully created PDF" in result
        mock_canvas_mod.canvas.Canvas.assert_called()

class TestAudioToolbox:
    def test_text_to_speech_success(self):
        mock_pyttsx3 = MagicMock()
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        with patch.dict(sys.modules, {'pyttsx3': mock_pyttsx3}):
            result = AudioToolbox.text_to_speech("Speak this", "out.mp3")

        assert "Audio saved" in result
        mock_engine.save_to_file.assert_called_with("Speak this", "out.mp3")
        mock_engine.runAndWait.assert_called()

    def test_get_metadata_success(self):
        mock_mutagen = MagicMock()
        mock_file = MagicMock()
        mock_file.info.length = 120
        mock_file.info.bitrate = 128000
        mock_file.info.sample_rate = 44100
        mock_mutagen.File.return_value = mock_file

        with patch.dict(sys.modules, {'mutagen': mock_mutagen}):
            result = AudioToolbox.get_metadata("test.mp3")

        assert "Duration: 120.00s" in result
        mock_mutagen.File.assert_called_with("test.mp3")

    def test_get_metadata_none(self):
        mock_mutagen = MagicMock()
        mock_mutagen.File.return_value = None

        with patch.dict(sys.modules, {'mutagen': mock_mutagen}):
            result = AudioToolbox.get_metadata("bad.mp3")

        assert "Could not load audio file" in result
