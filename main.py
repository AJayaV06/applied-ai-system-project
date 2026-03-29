from datetime import date, time

from pawpal_system import Owner, Pet, Task, TaskCategory, Scheduler


def main():
    owner = Owner(name="Jay", age=30)

    # Add pets
    dog = Pet(name="Sunny", age=4, species="Dog", breed="Golden Retriever")
    cat = Pet(name="Mittens", age=2, species="Cat", breed="Tabby")
    owner.add_pet(dog)
    owner.add_pet(cat)

    # Add tasks
    dog.add_task(Task(
        title="Morning walk",
        description="30-minute walk around the block",
        duration_minutes=30,
        priority=5,
        category=TaskCategory.WALK,
        preferred_time=time(hour=8, minute=0)
    ))

    dog.add_task(Task(
        title="Evening fetch",
        description="15-minute fetch session",
        duration_minutes=15,
        priority=3,
        category=TaskCategory.ENRICHMENT,
        preferred_time=time(hour=17, minute=30)
    ))

    cat.add_task(Task(
        title="Feeding",
        description="Give wet and dry food",
        duration_minutes=10,
        priority=4,
        category=TaskCategory.FEED,
        preferred_time=time(hour=7, minute=30)
    ))

    cat.add_task(Task(
        title="Litter clean",
        description="Scoop litter box",
        duration_minutes=10,
        priority=2,
        category=TaskCategory.GROOMING,
        preferred_time=time(hour=18, minute=0)
    ))

    # Add recurring tasks (daily/weekly)
    dog.add_task(Task(
        title="Daily meds",
        description="Administer daily pills",
        duration_minutes=5,
        priority=5,
        category=TaskCategory.MEDS,
        repeat_rule="daily",
        due_date=date.today(),
    ))

    cat.add_task(Task(
        title="Weekly grooming",
        description="Brush fur",
        duration_minutes=20,
        priority=3,
        category=TaskCategory.GROOMING,
        repeat_rule="weekly",
        due_date=date.today(),
    ))

    # mark one task as completed to test completion filtering and recurrence
    new_repeat_task = owner.mark_task_complete("Mittens", "Weekly grooming")
    print(f"Created recurring task: {new_repeat_task.title} (due {new_repeat_task.due_date})" if new_repeat_task else "No repeat created")

    # Add another out-of-order task schedule entry as a string-based start time
    dog.add_task(Task(
        title="Afternoon tug",
        description="Tug of war for 10 min",
        duration_minutes=10,
        priority=4,
        category=TaskCategory.ENRICHMENT,
        scheduled_start="15:00"
    ))

    # Add same-time tasks for conflict detection
    dog.add_task(Task(
        title="Overlap fetch",
        description="Another task starting same time",
        duration_minutes=20,
        priority=3,
        category=TaskCategory.ENRICHMENT,
        scheduled_start=time(hour=8, minute=0)
    ))

    cat.add_task(Task(
        title="Same-time snack",
        description="Cat treat break",
        duration_minutes=5,
        priority=3,
        category=TaskCategory.FEED,
        scheduled_start=time(hour=8, minute=0)
    ))

    scheduler = Scheduler(owner=owner, date=date.today())
    scheduler.generate_daily_plan()

    print("\n=== Full plan (as generated) ===")
    print(scheduler.explain_plan())

    print("\n=== Sorted by time ===")
    scheduler.sort_tasks_by_time()
    for t in scheduler.planned_tasks:
        print(f"{t.scheduled_start} - {t.title} ({t.pet_name}, {t.duration_minutes}m, completed={t.completed})")

    print("\n=== Filter: pet Mittens ===")
    mittens_tasks = owner.filter_tasks(pet_name="Mittens")
    for t in mittens_tasks:
        print(f"{t.title}, completed={t.completed}, scheduled_start={t.scheduled_start}")

    print("\n=== Filter: completed tasks ===")
    done_tasks = owner.filter_tasks(completed=True)
    for t in done_tasks:
        print(f"{t.title} ({t.pet_name}), scheduled_start={t.scheduled_start}")

    print("\nSummary:", scheduler.get_summary())


if __name__ == "__main__":
    main()
