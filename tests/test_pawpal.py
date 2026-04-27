from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Task, TaskCategory, Scheduler


def test_filtering_tasks_by_pet_name_works():
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

    rex_tasks = owner.filter_tasks(pet_name="Rex")
    assert len(rex_tasks) == 2
    assert all(t.pet_name == "Rex" for t in rex_tasks)

    done_tasks = owner.filter_tasks(completed=True)
    assert len(done_tasks) == 1
    assert done_tasks[0].title == "Feed"


def test_high_priority_tasks_are_scheduled_before_low_priority_when_flexible():
    owner = Owner(name="Alex", age=34)
    pet = Pet(name="Buddy", age=2, species="dog", breed="poodle")
    owner.add_pet(pet)
    owner.set_availability(time(7, 0), time(9, 0))

    high = Task(title="Medication", description="Give meds", duration_minutes=15, priority=5, pet_name="Buddy", category=TaskCategory.MEDS)
    low = Task(title="Brush coat", description="Light grooming", duration_minutes=15, priority=1, pet_name="Buddy", category=TaskCategory.GROOMING)

    pet.add_task(low)
    pet.add_task(high)

    scheduler = Scheduler(owner=owner, date=date.today())
    plan = scheduler.generate_daily_plan(pet_name="Buddy")
    assert len(plan) == 2
    assert plan[0].title == "Medication"
    assert plan[1].title == "Brush coat"


def test_tasks_outside_owner_availability_are_not_scheduled():
    owner = Owner(name="Jamie", age=31)
    pet = Pet(name="Max", age=3, species="dog", breed="mixed")
    owner.add_pet(pet)

    owner.set_availability_windows([
        (time(7, 0), time(7, 30)),
        (time(18, 0), time(18, 30)),
    ])

    pet.add_task(Task(title="Walk", description="Walk", duration_minutes=40, priority=4, pet_name="Max", category=TaskCategory.WALK))
    pet.add_task(Task(title="Feed", description="Feed", duration_minutes=10, priority=5, pet_name="Max", category=TaskCategory.FEED))

    scheduler = Scheduler(owner=owner, date=date.today())
    plan = scheduler.generate_daily_plan(pet_name="Max")

    assert len(plan) == 1
    assert plan[0].title == "Feed"
    assert len(scheduler.unscheduled_tasks) == 1
    assert scheduler.unscheduled_tasks[0].title == "Walk"


def test_overlapping_tasks_create_conflict_warnings():
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


def test_daily_plan_summary_is_generated_with_ai_outputs():
    owner = Owner(name="Jordan", age=30)
    pet = Pet(name="Max", age=3, species="dog", breed="mixed")
    owner.add_pet(pet)
    owner.set_availability_windows([
        (time(7, 0), time(9, 0)),
        (time(18, 0), time(21, 0)),
    ])

    pet.add_task(Task(title="Walk", description="Morning walk", duration_minutes=30, priority=5, pet_name="Max", category=TaskCategory.WALK))
    pet.add_task(Task(title="Feed", description="Breakfast", duration_minutes=15, priority=4, pet_name="Max", category=TaskCategory.FEED))

    scheduler = Scheduler(owner=owner, date=date.today())
    scheduler.generate_daily_plan(pet_name="Max")

    summary = scheduler.get_summary()
    explanation = scheduler.explain_plan()

    assert summary["total_tasks"] == 2
    assert isinstance(summary["daily_summary"], str)
    assert "planned task" in summary["daily_summary"]
    assert "Why: I placed this task here because" in explanation
