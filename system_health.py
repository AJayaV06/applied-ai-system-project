import logging
from pawpal_system import run_system_health_check

logging.basicConfig(
    filename="pawpal.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main() -> None:
    health = run_system_health_check()
    print(health["health_text"])
    print(f"Status: {health['status']}")
    for result in health["results"]:
        prefix = "PASS" if result["passed"] else "FAIL"
        print(f"{prefix}: {result['name']} - {result['details']}")


if __name__ == "__main__":
    main()