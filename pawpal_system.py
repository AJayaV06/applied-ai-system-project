from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import List, Optional, Dict, Any


@dataclass
class Pet:
    name: str
    age: int
    species: str
    breed: str
    notes: Optional[str] = None

    def get_info(self) -> Dict[str, Any]:
        """Return a summary dictionary of pet details."""
        raise NotImplementedError


@dataclass
class Owner:
    name: str
    age: int
    pets: List[Pet] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError

    def remove_pet(self, pet_name: str) -> None:
        raise NotImplementedError

    def set_availability(self, start: time, end: time) -> None:
        raise NotImplementedError

    def get_profile(self) -> Dict[str, Any]:
        raise NotImplementedError


@dataclass
class Task:
    title: str
    description: str
    duration_minutes: int
    priority: int
    preferred_time: Optional[time] = None
    repeat_rule: Optional[str] = None
    flexible: bool = True

    def validate(self) -> bool:
        """Check task data is valid (duration positive, priority in expected range, etc.)."""
        raise NotImplementedError

    def is_repeat_due(self, current_date: date) -> bool:
        """Determine whether task should occur for a given date based on repeat_rule."""
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError


@dataclass
class Schedule:
    date: date
    tasks: List[Task] = field(default_factory=list)
    total_available_minutes: int = 8 * 60

    def add_task(self, task: Task) -> None:
        raise NotImplementedError

    def edit_task(self, task_index: int, updated: Dict[str, Any]) -> None:
        raise NotImplementedError

    def remove_task(self, task_index: int) -> None:
        raise NotImplementedError

    def generate(self, tasks_pool: List[Task]) -> List[Task]:
        """Generate a daily plan from a pool of candidate tasks."""
        raise NotImplementedError

    def sort_by_priority(self) -> None:
        raise NotImplementedError

    def check_conflicts(self) -> List[str]:
        raise NotImplementedError

    def explain_plan(self) -> str:
        raise NotImplementedError

    def get_daily_summary(self) -> Dict[str, Any]:
        raise NotImplementedError
