import pytest
from crytonix.tools import HealthToolbox

def test_check_posture():
    """Test that check_posture returns a valid string."""
    result = HealthToolbox.check_posture()
    assert isinstance(result, str)
    assert result.startswith("🧘 Posture Check:")
    assert len(result) > 20

def test_stretch_exercise():
    """Test that stretch_exercise returns a valid string."""
    result = HealthToolbox.stretch_exercise()
    assert isinstance(result, str)
    assert result.startswith("🤸 Stretch Time:")
    assert len(result) > 20

def test_health_toolbox_methods_exist():
    """Test that methods exist in the toolbox class."""
    assert hasattr(HealthToolbox, "check_posture")
    assert hasattr(HealthToolbox, "stretch_exercise")
