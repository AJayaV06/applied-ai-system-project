from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from pathlib import Path
import copy
import json
import logging
from typing import List, Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


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
        if self.scheduled_start is not None and self._coerce_time(self.scheduled_start) is None:
            return False
        return True

    @staticmethod
    def _coerce_time(raw_time: Optional[object]) -> Optional[time]:
        if raw_time is None:
            return None
        if isinstance(raw_time, time):
            return raw_time
        if isinstance(raw_time, str):
            try:
                parsed = datetime.strptime(raw_time.strip(), "%H:%M")
                return parsed.time()
            except ValueError:
                return None
        return None

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
        start_time = self._coerce_time(self.scheduled_start)
        if start_time is None:
            return None
        start_dt = datetime.combine(date.today(), start_time)
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
            "scheduled_start": self._coerce_time(self.scheduled_start).isoformat() if self._coerce_time(self.scheduled_start) else None,
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
            logger.warning("Task '%s' pet_name '%s' does not match pet '%s'", task.title, task.pet_name, self.name)
            raise ValueError("Task pet_name does not match this pet")
        task.pet_name = self.name
        if not task.validate():
            logger.warning("Task '%s' failed validation for pet '%s'", task.title, self.name)
            raise ValueError("Invalid task")
        self.tasks.append(task)
        logger.info("Task '%s' added to pet '%s'", task.title, self.name)

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
    availability_windows: List[Tuple[time, time]] = field(default_factory=list)

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
            logger.error("Cannot complete task '%s': pet '%s' not found", task_title, pet_name)
            raise ValueError(f"Pet '{pet_name}' not found")

        for task in pet.tasks:
            if task.title == task_title and not task.completed:
                task.set_completed(True)
                logger.info("Task '%s' marked complete for pet '%s'", task_title, pet_name)
                if task.repeat_rule and task.repeat_rule.strip().lower() in ("daily", "weekly"):
                    new_task = task.clone_for_next_occurrence()
                    if new_task:
                        pet.add_task(new_task)
                        logger.info("Recurring task '%s' rescheduled for %s", task_title, new_task.due_date)
                        return new_task
                return None

        logger.warning("Task '%s' not found or already completed for pet '%s'", task_title, pet_name)
        raise ValueError(f"Task '{task_title}' not found for pet '{pet_name}'")

    def set_availability(self, start: time, end: time) -> None:
        """Set the owner's available planning window for tasks."""
        if datetime.combine(date.today(), end) <= datetime.combine(date.today(), start):
            raise ValueError("Availability end time must be after start time")
        self.available_start = start
        self.available_end = end

    def set_availability_windows(self, windows: List[Tuple[time, time]]) -> None:
        """Set owner availability using one or more time windows in a day."""
        validated: List[Tuple[time, time]] = []
        for start, end in windows:
            if datetime.combine(date.today(), end) <= datetime.combine(date.today(), start):
                raise ValueError("Each availability window must have end time after start time")
            validated.append((start, end))
        self.availability_windows = sorted(validated, key=lambda w: (w[0].hour, w[0].minute))

    def get_availability_windows(self) -> List[Tuple[time, time]]:
        """Return configured availability windows or the default single window."""
        if self.availability_windows:
            return self.availability_windows.copy()
        return [(self.available_start, self.available_end)]

    def remove_task(self, pet_name: str, task_title: str) -> None:
        """Remove a task by title from a specific pet."""
        pet = self.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"Pet '{pet_name}' not found")
        if not any(t.title == task_title for t in pet.tasks):
            raise ValueError(f"Task '{task_title}' not found for pet '{pet_name}'")
        pet.remove_task(task_title)

    @property
    def available_minutes(self) -> int:
        """Return number of minutes available in owner's availability window."""
        total = 0
        for start, end in self.get_availability_windows():
            start_dt = datetime.combine(date.today(), start)
            end_dt = datetime.combine(date.today(), end)
            total += max(int((end_dt - start_dt).total_seconds() / 60), 0)
        return total

    def get_profile(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "age": self.age,
            "pets": [pet.get_info() for pet in self.pets],
            "available_start": self.available_start.isoformat(),
            "available_end": self.available_end.isoformat(),
            "availability_windows": [
                {"start": start.isoformat(), "end": end.isoformat()} for start, end in self.get_availability_windows()
            ],
            "available_minutes": self.available_minutes,
            "preferences": self.preferences,
        }


@dataclass
class Scheduler:
    owner: Owner
    date: date
    planned_tasks: List[Task] = field(default_factory=list)
    unscheduled_tasks: List[Task] = field(default_factory=list)
    knowledge_base: List[Dict[str, Any]] = field(default_factory=list)
    rag_warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.load_knowledge_base()

    def retrieve_tasks(self) -> List[Task]:
        """Retrieve all tasks from the owner across all pets."""
        return self.owner.get_all_tasks()

    def load_knowledge_base(self, kb_path: Optional[Path] = None) -> None:
        """Load pet-care guidance notes used for retrieval-augmented explanations."""
        default_path = Path(__file__).resolve().parent / "assets" / "pet_care_notes.json"
        resolved_path = kb_path or default_path
        if resolved_path.exists():
            with resolved_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
                if isinstance(payload, list):
                    self.knowledge_base = payload
                    logger.info("Knowledge base loaded from %s (%d entries)", resolved_path, len(self.knowledge_base))
                    return

        logger.warning("Knowledge base file not found at %s; using built-in fallback entries", resolved_path)
        self.knowledge_base = [
            {
                "id": "walk_before_meal_dog",
                "species": "dog",
                "categories": ["walk", "feed"],
                "requires": ["feed"],
                "min_age": 0,
                "max_age": 25,
                "guidance": "Dogs often do better with moderate activity before meals rather than intense play immediately after eating.",
            },
            {
                "id": "medication_consistency",
                "species": "any",
                "categories": ["meds"],
                "min_age": 0,
                "max_age": 25,
                "guidance": "Medication tasks should be treated as high urgency and done consistently at stable times.",
            },
            {
                "id": "senior_pet_pacing",
                "species": "any",
                "categories": ["walk", "enrichment", "grooming"],
                "min_age": 8,
                "max_age": 30,
                "guidance": "Senior pets benefit from shorter, predictable routines and low-impact enrichment.",
            },
            {
                "id": "puppy_training",
                "species": "dog",
                "categories": ["walk", "enrichment"],
                "min_age": 0,
                "max_age": 2,
                "guidance": "Younger dogs do best with frequent short activities and enrichment to avoid overstimulation.",
            },
            {
                "id": "cat_enrichment",
                "species": "cat",
                "categories": ["enrichment", "grooming"],
                "min_age": 0,
                "max_age": 25,
                "guidance": "Cats often respond well to evening enrichment and short grooming routines when calm.",
            },
        ]

    def _retrieve_guidance(self, task: Task, pet_categories: Optional[set] = None) -> List[str]:
        pet = self.owner.get_pet(task.pet_name) if task.pet_name else None
        species = pet.species.lower() if pet else "any"
        age = pet.age if pet else 0
        category = task.category.value
        known_categories = pet_categories or {category}

        scored: List[Tuple[int, str]] = []
        for note in self.knowledge_base:
            note_species = str(note.get("species", "any")).lower()
            categories = [str(c).lower() for c in note.get("categories", [])]
            requires = [str(c).lower() for c in note.get("requires", [])]
            min_age = int(note.get("min_age", 0))
            max_age = int(note.get("max_age", 30))
            guidance = str(note.get("guidance", "")).strip()
            if not guidance:
                continue

            if not (min_age <= age <= max_age):
                continue

            if requires and not all(r in known_categories for r in requires):
                continue

            if note_species != "any" and note_species != species:
                continue

            score = 0
            if note_species == species:
                score += 3
            elif note_species == "any":
                score += 1

            if category in categories:
                score += 3

            if score > 0:
                scored.append((score, guidance))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_guidance: List[str] = []
        for _, guidance in scored:
            if guidance not in top_guidance:
                top_guidance.append(guidance)
            if len(top_guidance) >= 2:
                break
        return top_guidance

    def _apply_rag_adjustments(self, tasks: List[Task]) -> Tuple[List[Task], List[str]]:
        """Apply behavioral changes driven by knowledge base content.

        Three rules derived from retrieved notes:
        1. Walk-before-feed: boost walk priority for pets that also have a feed task.
        2. Senior pet duration: flag walk/enrichment/grooming tasks over 30 min for pets aged 8+.
        3. Medication consistency: warn if a meds task has no fixed scheduled time.
        """
        warnings: List[str] = []

        has_walk_feed_note = any(
            "walk" in [str(c).lower() for c in note.get("categories", [])]
            and "feed" in [str(c).lower() for c in note.get("categories", [])]
            for note in self.knowledge_base
        )
        has_senior_note = any(
            int(note.get("min_age", 0)) >= 7 or int(note.get("max_age", 0)) >= 8
            for note in self.knowledge_base
            if "walk" in [str(c).lower() for c in note.get("categories", [])]
        )
        has_meds_note = any(
            "meds" in [str(c).lower() for c in note.get("categories", [])]
            for note in self.knowledge_base
        )

        # Build per-task effective priority without mutating the task itself.
        effective: Dict[int, int] = {id(t): t.priority for t in tasks}

        # Rule 1 — walk-before-feed priority boost.
        if has_walk_feed_note:
            pets_with_feed = {t.pet_name for t in tasks if t.category == TaskCategory.FEED}
            for t in tasks:
                if t.category == TaskCategory.WALK and t.pet_name in pets_with_feed:
                    pet = self.owner.get_pet(t.pet_name)
                    feed_priority = max(
                        (x.priority for x in tasks if x.pet_name == t.pet_name and x.category == TaskCategory.FEED),
                        default=t.priority,
                    )
                    boosted = min(feed_priority + 1, 5)
                    if boosted > effective[id(t)]:
                        old = effective[id(t)]
                        effective[id(t)] = boosted
                        msg = (
                            f"RAG (walk-before-feed): '{t.title}' ({t.pet_name}) priority "
                            f"boosted {old} → {boosted} so it schedules before the feed task."
                        )
                        warnings.append(msg)
                        logger.info("RAG walk-before-feed: '%s' priority %d → %d", t.title, old, boosted)

        # Rule 2 — senior pet duration flag.
        SENIOR_AGE = 8
        SENIOR_MAX_MIN = 30
        SENIOR_CATEGORIES = {TaskCategory.WALK, TaskCategory.ENRICHMENT, TaskCategory.GROOMING}
        if has_senior_note:
            for t in tasks:
                pet = self.owner.get_pet(t.pet_name) if t.pet_name else None
                if pet and pet.age >= SENIOR_AGE and t.category in SENIOR_CATEGORIES and t.duration_minutes > SENIOR_MAX_MIN:
                    msg = (
                        f"RAG (senior pet): '{t.title}' ({t.pet_name}, age {pet.age}) is "
                        f"{t.duration_minutes} min — consider shortening to ≤{SENIOR_MAX_MIN} min for a senior pet."
                    )
                    warnings.append(msg)
                    logger.warning("RAG senior pet: '%s' (%s age %d) %d min exceeds recommendation", t.title, t.pet_name, pet.age, t.duration_minutes)

        # Rule 3 — medication consistency: flag meds tasks with no fixed time.
        if has_meds_note:
            for t in tasks:
                if t.category == TaskCategory.MEDS:
                    fixed = Task._coerce_time(t.scheduled_start) or t.preferred_time
                    if fixed is None:
                        msg = (
                            f"RAG (medication consistency): '{t.title}' ({t.pet_name}) has no fixed time — "
                            f"set a consistent daily time to avoid missed doses."
                        )
                        warnings.append(msg)
                        logger.warning("RAG meds consistency: '%s' (%s) has no fixed scheduled time", t.title, t.pet_name)

        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                -effective[id(t)],
                t.preferred_time or time(23, 59),
                t.duration_minutes,
            ),
        )
        return sorted_tasks, warnings

    @staticmethod
    def _add_minutes(start_time: time, minutes: int, plan_date: date) -> time:
        return (datetime.combine(plan_date, start_time) + timedelta(minutes=minutes)).time()

    @staticmethod
    def _coerce_time(raw_time: Optional[object]) -> Optional[time]:
        return Task._coerce_time(raw_time)

    def generate_daily_plan(self, pet_name: Optional[str] = None, completed: Optional[bool] = False) -> List[Task]:
        tasks = self.owner.filter_tasks(pet_name=pet_name, completed=completed)
        tasks = [t for t in tasks if t.is_repeat_due(self.date) and t.validate()]

        # Deduplicate by object identity so accidental double-adds don't produce duplicate schedule entries.
        seen_ids: set = set()
        deduped: List[Task] = []
        for t in tasks:
            if id(t) not in seen_ids:
                seen_ids.add(id(t))
                deduped.append(t)
        tasks = deduped

        sorted_tasks, rag_warnings = self._apply_rag_adjustments(tasks)
        self.rag_warnings = rag_warnings

        windows = self.owner.get_availability_windows()
        window_cursors: List[time] = [window[0] for window in windows]

        scheduled: List[Task] = []
        unscheduled: List[Task] = []

        for task in sorted_tasks:
            # Work on a shallow copy so scheduling never mutates the original task stored in pet.tasks.
            scheduled_task = copy.copy(task)
            preferred_or_fixed = self._coerce_time(task.scheduled_start) or task.preferred_time
            placed = False

            # First pass: honor preferred/fixed start if it fits any window.
            if preferred_or_fixed is not None:
                proposed_end = self._add_minutes(preferred_or_fixed, task.duration_minutes, self.date)
                for window_start, window_end in windows:
                    if preferred_or_fixed >= window_start and proposed_end <= window_end:
                        scheduled_task.scheduled_start = preferred_or_fixed
                        scheduled.append(scheduled_task)
                        placed = True
                        break

            # Second pass: place flexible tasks in the earliest available slot across windows.
            if not placed and task.flexible:
                for idx, (window_start, window_end) in enumerate(windows):
                    proposed_start = window_cursors[idx]
                    if proposed_start < window_start:
                        proposed_start = window_start
                    proposed_end = self._add_minutes(proposed_start, task.duration_minutes, self.date)
                    if proposed_end <= window_end:
                        scheduled_task.scheduled_start = proposed_start
                        scheduled.append(scheduled_task)
                        window_cursors[idx] = proposed_end
                        placed = True
                        break

            if not placed:
                unscheduled.append(task)

        self.planned_tasks = scheduled
        self.unscheduled_tasks = unscheduled
        logger.info(
            "Daily plan generated for %s: %d scheduled, %d unscheduled",
            self.date.isoformat(), len(scheduled), len(unscheduled),
        )
        for t in unscheduled:
            logger.warning("Task '%s' (%s) could not be scheduled — no fitting availability window", t.title, t.pet_name)
        return scheduled

    def generate_agentic_plan(self, pet_name: Optional[str] = None, completed: Optional[bool] = False) -> Dict[str, Any]:
        """Generate a plan with explicit planning, review, and revision steps.

        This makes the multi-step workflow visible for the UI and for evaluation.
        """
        steps: List[str] = []

        steps.append("Read owner availability and pet tasks.")
        available_tasks = self.owner.filter_tasks(pet_name=pet_name, completed=completed)
        available_tasks = [t for t in available_tasks if t.is_repeat_due(self.date) and t.validate()]
        steps.append(f"Found {len(available_tasks)} eligible task(s) to schedule.")

        steps.append("Create a first schedule.")
        draft_plan = self.generate_daily_plan(pet_name=pet_name, completed=completed)
        draft_conflicts = self.check_conflicts()
        draft_unscheduled = [f"{t.title} ({t.pet_name})" for t in self.unscheduled_tasks]
        steps.append(
            f"Initial schedule contains {len(draft_plan)} task(s), {len(draft_conflicts)} conflict(s), and {len(draft_unscheduled)} unscheduled task(s)."
        )

        if self.rag_warnings:
            steps.append(f"Applied {len(self.rag_warnings)} RAG-driven adjustment(s) from knowledge base.")

        if draft_conflicts or draft_unscheduled:
            steps.append("Check for conflicts, availability violations, and missing recurring tasks.")
            steps.append("Fix the schedule automatically by keeping the best-fitting tasks and explaining the remaining issues.")
            final_plan_text = self.explain_plan()
        else:
            steps.append("No conflicts or availability issues were found.")
            final_plan_text = self.explain_plan()

        steps.append("Explain the final plan.")

        return {
            "steps": steps,
            "draft_plan": draft_plan,
            "draft_conflicts": draft_conflicts,
            "draft_unscheduled": draft_unscheduled,
            "rag_warnings": self.rag_warnings,
            "final_plan": self.planned_tasks,
            "final_plan_text": final_plan_text,
            "summary": self.get_summary(),
        }

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
        tasks = [t for t in self.planned_tasks if self._coerce_time(t.scheduled_start) is not None]
        tasks.sort(key=lambda t: Scheduler._time_key(self._coerce_time(t.scheduled_start)))

        for i in range(len(tasks) - 1):
            current = tasks[i]
            nxt = tasks[i + 1]

            # same start-time warning (same slot, possibly same or different pets)
            current_start = self._coerce_time(current.scheduled_start)
            next_start = self._coerce_time(nxt.scheduled_start)
            if current_start is None or next_start is None:
                continue

            if current_start == next_start:
                msg = f"WARNING: {current.title} ({current.pet_name}) and {nxt.title} ({nxt.pet_name}) both start at {current_start.strftime('%H:%M')}"
                conflicts.append(msg)
                logger.warning("Scheduling conflict: %s", msg)

            current_end = current.get_end_time()
            if current_end and next_start:
                if datetime.combine(self.date, next_start) < datetime.combine(self.date, current_end):
                    msg = f"WARNING: {current.title} ({current.pet_name}) [{current_start.strftime('%H:%M')}-{current_end.strftime('%H:%M')}] overlaps {nxt.title} ({nxt.pet_name}) [{next_start.strftime('%H:%M')}-{nxt.get_end_time().strftime('%H:%M') if nxt.get_end_time() else '??:??'}]"
                    conflicts.append(msg)
                    logger.warning("Scheduling conflict: %s", msg)

        return conflicts

    def generate_care_suggestions(self) -> List[str]:
        """Generate concise pet-specific care tips based on retrieved guidance."""
        suggestions: List[str] = []
        for pet in self.owner.pets:
            sample_task = Task(
                title="care_suggestion",
                description="",
                duration_minutes=1,
                priority=1,
                pet_name=pet.name,
                category=TaskCategory.ENRICHMENT,
            )
            guidance = self._retrieve_guidance(sample_task)
            if guidance:
                suggestions.append(f"{pet.name}: {guidance[0]}")
        return suggestions

    def explain_plan(self) -> str:
        if not self.planned_tasks:
            return f"No tasks scheduled for {self.date.isoformat()}"

        pet_categories: Dict[str, set] = {}
        for t in self.planned_tasks:
            pet_categories.setdefault(t.pet_name or "", set()).add(t.category.value)

        lines = [f"Today's Schedule for {self.owner.name} ({self.date.isoformat()}):"]
        for t in self.planned_tasks:
            start_time = self._coerce_time(t.scheduled_start)
            end = t.get_end_time()
            guidance = self._retrieve_guidance(t, pet_categories.get(t.pet_name or "", set()))
            reason_parts = []

            if t.priority >= 4:
                reason_parts.append("it is a high-priority care task")
            elif t.priority == 3:
                reason_parts.append("it has medium priority")
            else:
                reason_parts.append("it has lower urgency")

            if t.repeat_rule:
                reason_parts.append(f"it follows a {t.repeat_rule} routine")

            if guidance:
                reason_parts.append(guidance[0])

            reason = "; ".join(reason_parts)
            lines.append(
                f"- {start_time.strftime('%H:%M') if start_time else '??:??'} to {end.strftime('%H:%M') if end else '??:??'}: {t.title} ({t.pet_name}, priority {t.priority})"
            )
            lines.append(f"  Why: I placed this task here because {reason}.")

        if self.unscheduled_tasks:
            lines.append("Unscheduled tasks (outside availability or no fitting slot):")
            for t in self.unscheduled_tasks:
                lines.append(f"- {t.title} ({t.pet_name}, {t.duration_minutes} min)")

        conflicts = self.check_conflicts()
        if conflicts:
            lines.append("Conflicts:")
            lines.extend(["  " + c for c in conflicts])

        suggestions = self.generate_care_suggestions()
        if suggestions:
            lines.append("Care suggestions:")
            for suggestion in suggestions:
                lines.append(f"- {suggestion}")

        if self.rag_warnings:
            lines.append("RAG-driven adjustments and warnings:")
            for w in self.rag_warnings:
                lines.append(f"  {w}")

        return "\n".join(lines)

    def summarize_plan_simple(self) -> str:
        """Return a short natural-language summary of the current day's plan."""
        if not self.planned_tasks:
            return "No tasks were scheduled today. Try expanding your availability windows or shortening task durations."

        total = len(self.planned_tasks)
        total_minutes = sum(t.duration_minutes for t in self.planned_tasks)
        pet_names = sorted({t.pet_name for t in self.planned_tasks if t.pet_name})
        pet_part = ", ".join(pet_names) if pet_names else "your pets"
        return (
            f"You have {total} planned task(s) for {pet_part}, totaling {total_minutes} minutes. "
            f"{len(self.unscheduled_tasks)} task(s) could not be scheduled in the available time windows."
        )

    def get_summary(self) -> Dict[str, Any]:
        total_duration = sum(t.duration_minutes for t in self.planned_tasks)
        return {
            "date": self.date.isoformat(),
            "total_tasks": len(self.planned_tasks),
            "total_duration": total_duration,
            "available_minutes": self.owner.available_minutes,
            "remaining_minutes": self.owner.available_minutes - total_duration,
            "conflicts": self.check_conflicts(),
            "unscheduled_tasks": [f"{t.title} ({t.pet_name})" for t in self.unscheduled_tasks],
            "rag_warnings": self.rag_warnings,
            "daily_summary": self.summarize_plan_simple(),
        }


def run_system_health_check() -> Dict[str, Any]:
    """Run a small built-in evaluation suite and return a report."""
    from datetime import date as _date, time as _time

    results: List[Dict[str, Any]] = []

    def add_result(name: str, passed: bool, details: str) -> None:
        results.append({"name": name, "passed": passed, "details": details})
        if passed:
            logger.info("Health check PASS: %s — %s", name, details)
        else:
            logger.warning("Health check FAIL: %s — %s", name, details)

    owner = Owner(name="Health Check", age=30)
    pet = Pet(name="Rex", age=5, species="dog", breed="beagle")
    owner.add_pet(pet)
    owner.set_availability(_time(7, 0), _time(9, 0))

    pet.add_task(Task(title="High priority meds", description="Medicine", duration_minutes=10, priority=5, pet_name="Rex", category=TaskCategory.MEDS))
    pet.add_task(Task(title="Low priority brush", description="Brush coat", duration_minutes=20, priority=1, pet_name="Rex", category=TaskCategory.GROOMING))

    scheduler = Scheduler(owner=owner, date=_date.today())
    plan = scheduler.generate_daily_plan(pet_name="Rex")
    add_result("High priority scheduling", len(plan) == 2 and plan[0].title == "High priority meds", f"Scheduled {len(plan)} task(s).")

    owner2 = Owner(name="Health Check 2", age=30)
    dog = Pet(name="Bolt", age=5, species="dog", breed="labrador")
    cat = Pet(name="Pixel", age=3, species="cat", breed="siamese")
    owner2.add_pet(dog)
    owner2.add_pet(cat)
    dog.add_task(Task(title="Dog walk", description="Walk", duration_minutes=30, priority=4, pet_name="Bolt", scheduled_start=_time(8, 0)))
    cat.add_task(Task(title="Cat feed", description="Feed", duration_minutes=10, priority=4, pet_name="Pixel", scheduled_start=_time(8, 0)))
    scheduler2 = Scheduler(owner=owner2, date=_date.today())
    scheduler2.planned_tasks = [dog.tasks[0], cat.tasks[0]]
    conflicts = scheduler2.check_conflicts()
    add_result("Conflict detection", len(conflicts) >= 1, f"Found {len(conflicts)} conflict warning(s).")

    owner3 = Owner(name="Health Check 3", age=30)
    pet3 = Pet(name="Max", age=3, species="dog", breed="mixed")
    owner3.add_pet(pet3)
    owner3.set_availability_windows([(_time(7, 0), _time(7, 30)), (_time(18, 0), _time(18, 30))])
    pet3.add_task(Task(title="Walk", description="Walk", duration_minutes=40, priority=4, pet_name="Max", category=TaskCategory.WALK))
    pet3.add_task(Task(title="Feed", description="Feed", duration_minutes=10, priority=5, pet_name="Max", category=TaskCategory.FEED))
    scheduler3 = Scheduler(owner=owner3, date=_date.today())
    scheduler3.generate_daily_plan(pet_name="Max")
    add_result("Availability handling", len(scheduler3.unscheduled_tasks) == 1 and scheduler3.unscheduled_tasks[0].title == "Walk", f"Unscheduled {len(scheduler3.unscheduled_tasks)} task(s).")

    passed_count = sum(1 for result in results if result["passed"])
    logger.info("System health check complete: %d/%d passed", passed_count, len(results))
    return {
        "total": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        "results": results,
        "health_text": f"{passed_count}/{len(results)} scheduler tests passed",
        "status": "healthy" if passed_count == len(results) else "needs attention",
    }
