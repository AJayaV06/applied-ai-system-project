import pytest
from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Task, TaskCategory, Scheduler


def test_task_completion_changes_status():
    task = Task(
        title="Walk Dog",
        description="30 minute walk",
        duration_minutes=30,
        priority=4,
        category=TaskCategory.WALK,
        pet_name="Rex",
    )

    assert task.completed is False
    task.set_completed(True)
    assert task.completed is True


def test_add_task_to_pet_increases_task_count():
    pet = Pet(name="Rex", age=5, species="dog", breed="labrador")
    base_count = len(pet.tasks)

    task = Task(
        title="Feed Dog",
        description="Food in bowl",
        duration_minutes=10,
        priority=5,
        category=TaskCategory.FEED,
        pet_name="Rex",
    )

    pet.add_task(task)
    assert len(pet.tasks) == base_count + 1
    assert pet.tasks[-1].title == "Feed Dog"


def test_scheduler_filter_tasks_by_pet_and_completion():
    owner = Owner(name="Taylor", age=29)
    dog = Pet(name="Rex", age=5, species="dog", breed="beagle")
    cat = Pet(name="Nala", age=3, species="cat", breed="siamese")

    t1 = Task(title="Walk", description="Walk Rex", duration_minutes=30, priority=4, pet_name="Rex")
    t2 = Task(title="Feed", description="Feed Nala", duration_minutes=10, priority=5, pet_name="Nala", completed=True)
    t3 = Task(title="Meds", description="Meds Rex", duration_minutes=5, priority=3, pet_name="Rex")

    dog.add_task(t1)
    dog.add_task(t3)
    cat.add_task(t2)
    owner.add_pet(dog)
    owner.add_pet(cat)

    # filter by pet
    rex_tasks = owner.filter_tasks(pet_name="Rex")
    assert len(rex_tasks) == 2

    # filter by completion
    done_tasks = owner.filter_tasks(completed=True)
    assert len(done_tasks) == 1
    assert done_tasks[0].title == "Feed"


def test_scheduler_repeat_and_sort_and_conflict():
    owner = Owner(name="Alex", age=34)
    pet = Pet(name="Buddy", age=2, species="dog", breed="poodle")
    owner.add_pet(pet)

    t1 = Task(title="Morning Walk", description="Daily walk", duration_minutes=30, priority=5, pet_name="Buddy", preferred_time=time(8, 0), repeat_rule="daily")
    t2 = Task(title="Morning Feed", description="Feed", duration_minutes=15, priority=5, pet_name="Buddy", preferred_time=time(8, 15), repeat_rule="daily")
    t3 = Task(title="Evening Play", description="Playtime", duration_minutes=20, priority=3, pet_name="Buddy", preferred_time=time(18, 0), repeat_rule="daily")

    pet.add_task(t1)
    pet.add_task(t2)
    pet.add_task(t3)

    scheduler = Scheduler(owner=owner, date=date.today())
    plan = scheduler.generate_daily_plan()
    assert len(plan) >= 2

    # ensure tasks are sorted by scheduled start time after sorting
    scheduler.sort_tasks_by_time()
    starts = [task.scheduled_start for task in scheduler.planned_tasks]
    assert starts == sorted(starts)

    conflicts = scheduler.check_conflicts()
    assert any("overlaps" in c for c in conflicts)


def test_sort_tasks_by_time_with_string_scheduled_start():
    owner = Owner(name="Sam", age=42)
    pet = Pet(name="Coco", age=1, species="bird", breed="parrot")
    owner.add_pet(pet)

    t1 = Task(title="Late", description="Late task", duration_minutes=10, priority=1, pet_name="Coco", scheduled_start="14:30")
    t2 = Task(title="Early", description="Early task", duration_minutes=10, priority=1, pet_name="Coco", scheduled_start="08:15")

    pet.add_task(t1)
    pet.add_task(t2)

    scheduler = Scheduler(owner=owner, date=date.today())
    scheduler.planned_tasks = [t1, t2]
    scheduler.sort_tasks_by_time()
    assert scheduler.planned_tasks[0].title == "Early"
    assert scheduler.planned_tasks[1].title == "Late"


def test_detect_same_time_conflicts():
    owner = Owner(name="Mia", age=35)
    dog = Pet(name="Bolt", age=5, species="dog", breed="labrador")
    cat = Pet(name="Pixel", age=3, species="cat", breed="siamese")
    owner.add_pet(dog)
    owner.add_pet(cat)

    dog.add_task(Task(title="Dog walk", description="Walk", duration_minutes=30, priority=4, category=TaskCategory.WALK, pet_name="Bolt", scheduled_start=time(8, 0)))
    cat.add_task(Task(title="Cat feed", description="Feed", duration_minutes=10, priority=4, category=TaskCategory.FEED, pet_name="Pixel", scheduled_start=time(8, 0)))

    scheduler = Scheduler(owner=owner, date=date.today())
    scheduler.planned_tasks = [dog.tasks[0], cat.tasks[0]]
    conflicts = scheduler.check_conflicts()
    assert any("both start" in c for c in conflicts)
    assert any("overlaps" in c for c in conflicts)


def test_mark_daily_repeating_task_completes_and_reschedules():
    owner = Owner(name="Simon", age=40)
    pet = Pet(name="Buddy", age=6, species="dog", breed="mixed")
    owner.add_pet(pet)

    task = Task(
        title="Daily meds",
        description="Give medicine",
        duration_minutes=5,
        priority=5,
        category=TaskCategory.MEDS,
        pet_name="Buddy",
        repeat_rule="daily",
        due_date=date.today(),
    )
    pet.add_task(task)

    new_task = owner.mark_task_complete("Buddy", "Daily meds")
    assert task.completed is True
    assert new_task is not None
    assert new_task.repeat_rule == "daily"
    assert new_task.completed is False
    assert new_task.due_date == date.today() + timedelta(days=1)
