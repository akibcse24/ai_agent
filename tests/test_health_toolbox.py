import sys
import os

# Add parent directory to path to import crytonix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crytonix.tools import HealthToolbox

def test_health_toolbox():
    print("Testing HealthToolbox...")

    # 1. Check Posture
    print("\n[Test 1] Check Posture...")
    res = HealthToolbox.check_posture()
    print(res)
    assert "Posture Check" in res

    # 2. Stretch Exercise
    print("\n[Test 2] Stretch Exercise...")
    res = HealthToolbox.stretch_exercise()
    print(res)
    assert "Stretch Time" in res

    # 3. Hydration Reminder
    print("\n[Test 3] Hydration Reminder...")
    res = HealthToolbox.hydration_reminder()
    print(res)
    assert "Hydration Check" in res

    # 4. Take Break
    print("\n[Test 4] Take Break...")
    res = HealthToolbox.take_break(10)
    print(res)
    assert "Time for a break" in res
    assert "10 minutes" in res

    print("\nAll HealthToolbox tests passed!")

if __name__ == "__main__":
    test_health_toolbox()
