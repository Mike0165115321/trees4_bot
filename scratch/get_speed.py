from database import get_global_speed
import json

def report_speed():
    stats = get_global_speed()
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    report_speed()
