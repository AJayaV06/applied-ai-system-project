from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any


class TaskCategory(Enum):
    WALK = "walk"
    FEED = "feed"
    MEDS = "meds"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"
    OTHER = "other"


@dataclass
class Task:
    title: str
    description: str
    duration_minutes: int
    priority: int
    pet_name: Optional[str] = None
    category: TaskCategory = TaskCategory.OTHER
    preferred_time: Optional[time] = None
    repeat_rule: Optional[str] = None
    due_date: Optional[date] = None
    flexible: bool = True
    completed: bool = False
    scheduled_start: Optional[time] = None

    def validate(self) -> bool:
        if not self.title.strip():
            return False
        if self.duration_minutes <= 0:
            return False
        if not (1 <= self.priority <= 5):
            return False
        if self.preferred_time and not isinstance(self.preferred_time, time):
            return False
        if self.due_date and not isinstance(self.due_date, date):
            return False
        if not isinstance(self.category, TaskCategory):
            return False
        return True

    def is_repeat_due(self, current_date: date) -> bool:
        if self.due_date and current_date < self.due_date:
            return False

        if not self.repeat_rule:
            return True

        rule = self.repeat_rule.strip().lower()
        if rule == "daily":
            return True
        if rule == "weekly":
            if self.due_date:
                return current_date >= self.due_date
            return True
        if rule == "weekdays":
            return current_date.weekday() < 5
        if rule == "weekends":
            return current_date.weekday() >= 5
        return True

    def set_completed(self, value: bool = True) -> None:
        """Mark task as completed or not completed."""
        self.completed = value

    def next_due_date(self) -> Optional[date]:
        """Compute the next due date for daily/weekly repeating tasks."""
        if not self.repeat_rule:
            return None

        rule = self.repeat_rule.strip().lower()
        if rule == "daily":
            return date.today() + timedelta(days=1)
        if rule == "weekly":
            return date.today() + timedelta(weeks=1)
        return None

    def clone_for_next_occurrence(self) -> Optional["Task"]:
        """Create a task copy for the next repeating occurrence."""
        next_date = self.next_due_date()
        if next_date is None:
            return None

        clone = Task(
            title=self.title,
            description=self.description,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            pet_name=self.pet_name,
            category=self.category,
            preferred_time=self.preferred_time,
            repeat_rule=self.repeat_rule,
            due_date=next_date,
            flexible=self.flexible,
            completed=False,
            scheduled_start=None,
        )
        return clone

    def get_end_time(self) -> Optional[time]:
        """Return computed task end time based on scheduled start and duration."""
        if self.scheduled_start is None:
            return None
        start_dt = datetime.combine(date.today(), self.scheduled_start)
        end_dt = start_dt + timedelta(minutes=self.duration_minutes)
        return end_dt.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task data into a dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "pet_name": self.pet_name,
            "category": self.category.value,
            "preferred_time": self.preferred_time.isoformat() if self.preferred_time else None,
            "repeat_rule": self.repeat_rule,
            "flexible": self.flexible,
            "completed": self.completed,
            "scheduled_start": self.scheduled_start.isoformat() if self.scheduled_start else None,
            "scheduled_end": self.get_end_time().isoformat() if self.get_end_time() else None,
        }


@dataclass
class Pet:
    name: str
    age: int
    species: str
    breed: str
    notes: Optional[str] = None
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a validated task to this pet."""
        if task.pet_name and task.pet_name != self.name:
            raise ValueError("Task pet_name does not match this pet")
        task.pet_name = self.name
        if not task.validate():
            raise ValueError("Invalid task")
        self.tasks.append(task)

    def remove_task(self, task_title: str) -> None:
        """Remove tasks matching a title from this pet."""
        self.tasks = [t for t in self.tasks if t.title != task_title]

    def get_tasks(self) -> List[Task]:
        """Return a copy of the pet's task list."""
        return self.tasks.copy()

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "age": self.age,
            "species": self.species,
            "breed": self.breed,
            "notes": self.notes,
            "task_count": len(self.tasks),
        }


@dataclass
class Owner:
    name: str
    age: int
    pets: List[Pet] = field(default_factory=list)
    available_start: time = time(hour=8, minute=0)
    available_end: time = time(hour=17, minute=0)
    preferences: Dict[str, Any] = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner roster."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"Pet '{pet.name}' already exists")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name from owner roster."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Retrieve a pet by name."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> List[Task]:
        """Collect all tasks across all pets."""
        all_tasks: List[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def filter_tasks(self, pet_name: Optional[str] = None, completed: Optional[bool] = None) -> List[Task]:
        """Filter tasks from all pets by pet name and/or completion state."""
        tasks = self.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def mark_task_complete(self, pet_name: str, task_title: str) -> Optional[Task]:
        """Mark a pet task as complete; clone a repeating task for next due date."""
        pet = self.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"Pet '{pet_name}' not found")

        for task in pet.tasks:
            if task.title == task_title and not task.completed:
                task.set_completed(True)
                if task.repeat_rule and task.repeat_rule.strip().lower() in ("daily", "weekly"):
                    new_task = task.clone_for_next_occurrence()
                    if new_task:
                        pet.add_task(new_task)
                        return new_task
                return None

        raise ValueError(f"Task '{task_title}' not found for pet '{pet_name}'")

    def set_availability(self, start: time, end: time) -> None:
        """Set the owner's available planning window for tasks."""
        if datetime.combine(date.today(), end) <= datetime.combine(date.today(), start):
            raise ValueError("Availability end time must be after start time")
        self.available_start = start
        self.available_end = end

    @property
    def available_minutes(self) -> int:
        """Return number of minutes available in owner's availability window."""
        start_dt = datetime.combine(date.today(), self.available_start)
        end_dt = datetime.combine(date.today(), self.available_end)
        return max(int((end_dt - start_dt).total_seconds() / 60), 0)

    def get_profile(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "age": self.age,
            "pets": [pet.get_info() for pet in self.pets],
            "available_start": self.available_start.isoformat(),
            "available_end": self.available_end.isoformat(),
            "available_minutes": self.available_minutes,
            "preferences": self.preferences,
        }


@dataclass
class Scheduler:
    owner: Owner
    date: date
    planned_tasks: List[Task] = field(default_factory=list)

    def retrieve_tasks(self) -> List[Task]:
        """Retrieve all tasks from the owner across all pets."""
        return self.owner.get_all_tasks()

    def generate_daily_plan(self, pet_name: Optional[str] = None, completed: Optional[bool] = False) -> List[Task]:
        tasks = self.owner.filter_tasks(pet_name=pet_name, completed=completed)
        tasks = [t for t in tasks if t.is_repeat_due(self.date) and t.validate()]

        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                -t.priority,
                t.preferred_time or time(23, 59),
                t.duration_minutes,
            ),
        )

        window_start = self.owner.available_start
        window_end = self.owner.available_end
        available_minutes = self.owner.available_minutes

        scheduled: List[Task] = []
        current_time = window_start
        used_minutes = 0

        for task in sorted_tasks:
            if used_minutes + task.duration_minutes > available_minutes:
                continue

            proposed_start = task.preferred_time or current_time
            # Do not force-shift preferred times; we allow conflict detection to detect overlaps
            if proposed_start < window_start:
                proposed_start = window_start

            proposed_end = (datetime.combine(self.date, proposed_start) + timedelta(minutes=task.duration_minutes)).time()
            if proposed_end > window_end:
                continue

            task.scheduled_start = proposed_start
            scheduled.append(task)
            used_minutes += task.duration_minutes

            if proposed_start >= current_time:
                current_time = proposed_end

        self.planned_tasks = scheduled
        return scheduled

    def sort_tasks(self) -> None:
        """Sort planned tasks by priority, start time, and duration."""
        self.planned_tasks.sort(
            key=lambda t: (-t.priority, t.scheduled_start or time(23, 59), t.duration_minutes)
        )

    @staticmethod
    def _time_key(raw_time: Optional[object]) -> tuple:
        """Convert time-like value to sortable tuple for chronology.

        Supports datetime.time and string "HH:MM".
        """
        if isinstance(raw_time, time):
            return (raw_time.hour, raw_time.minute)
        if isinstance(raw_time, str):
            try:
                h, m = map(int, raw_time.split(":"))
                return (h, m)
            except (ValueError, AttributeError):
                return (23, 59)
        return (23, 59)

    def sort_tasks_by_time(self) -> None:
        """Sort planned tasks only by scheduled start time (for timeline view)."""
        self.planned_tasks.sort(key=lambda t: Scheduler._time_key(t.scheduled_start))

    def check_conflicts(self) -> List[str]:
        """Detect and return any conflict descriptions among scheduled tasks."""
        if not self.planned_tasks:
            return []

        conflicts = []
        tasks = [t for t in self.planned_tasks if t.scheduled_start is not None]
        tasks.sort(key=lambda t: t.scheduled_start)

        for i in range(len(tasks) - 1):
            current = tasks[i]
            nxt = tasks[i + 1]

            # same start-time warning (same slot, possibly same or different pets)
            if current.scheduled_start == nxt.scheduled_start:
                conflicts.append(
                    f"WARNING: {current.title} ({current.pet_name}) and {nxt.title} ({nxt.pet_name}) both start at {current.scheduled_start.strftime('%H:%M')}"
                )

            current_end = current.get_end_time()
            if current_end and nxt.scheduled_start:
                if datetime.combine(self.date, nxt.scheduled_start) < datetime.combine(self.date, current_end):
                    conflicts.append(
                        f"WARNING: {current.title} ({current.pet_name}) [{current.scheduled_start.strftime('%H:%M')}-{current_end.strftime('%H:%M')}] overlaps {nxt.title} ({nxt.pet_name}) [{nxt.scheduled_start.strftime('%H:%M')}-{nxt.get_end_time().strftime('%H:%M') if nxt.get_end_time() else '??:??'}]"
                    )

        return conflicts

    def explain_plan(self) -> str:
        if not self.planned_tasks:
            return f"No tasks scheduled for {self.date.isoformat()}"

        lines = [f"Today's Schedule for {self.owner.name} ({self.date.isoformat()}):"]
        for t in self.planned_tasks:
            end = t.get_end_time()
            lines.append(
                f"- {t.scheduled_start.strftime('%H:%M')} to {end.strftime('%H:%M') if end else '??:??'}: {t.title} ({t.pet_name}, priority {t.priority})"
            )

        conflicts = self.check_conflicts()
        if conflicts:
            lines.append("Conflicts:")
            lines.extend(["  " + c for c in conflicts])

        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        total_duration = sum(t.duration_minutes for t in self.planned_tasks)
        return {
            "date": self.date.isoformat(),
            "total_tasks": len(self.planned_tasks),
            "total_duration": total_duration,
            "available_minutes": self.owner.available_minutes,
            "remaining_minutes": self.owner.available_minutes - total_duration,
            "conflicts": self.check_conflicts(),
        }
