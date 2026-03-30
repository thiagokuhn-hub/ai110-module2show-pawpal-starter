"""
PawPal+ CLI Demo Script
========================
A standalone script to verify the backend logic works correctly
before connecting it to the Streamlit UI. Demonstrates all features
including priority sorting, conflict detection, next-available-slot,
recurring tasks, and JSON persistence.
"""

from pawpal_system import Task, Pet, Owner, Scheduler
from datetime import datetime


def main():
    today = datetime.now().strftime("%Y-%m-%d")

    # --- Create an Owner ---
    owner = Owner(name="Jordan", email="jordan@example.com")
    print(f"Created owner: {owner.name}\n")

    # --- Create Pets ---
    mochi = Pet(name="Mochi", species="dog", age=3, breed="Golden Retriever")
    whiskers = Pet(name="Whiskers", species="cat", age=5, breed="Siamese")

    owner.add_pet(mochi)
    owner.add_pet(whiskers)
    print(f"Added pet: {mochi}")
    print(f"Added pet: {whiskers}\n")

    # --- Add Tasks (intentionally out of chronological order, with priorities) ---
    mochi.add_task(Task(
        description="Evening walk",
        time="18:00",
        frequency="daily",
        category="walk",
        priority="medium",
        date=today,
    ))
    mochi.add_task(Task(
        description="Morning walk",
        time="07:30",
        frequency="daily",
        category="walk",
        priority="high",
        date=today,
    ))
    mochi.add_task(Task(
        description="Breakfast",
        time="08:00",
        frequency="daily",
        category="feeding",
        priority="high",
        date=today,
    ))
    mochi.add_task(Task(
        description="Vet appointment",
        time="14:00",
        frequency="once",
        category="appointment",
        priority="high",
        date=today,
    ))

    whiskers.add_task(Task(
        description="Morning feeding",
        time="07:30",
        frequency="daily",
        category="feeding",
        priority="high",
        date=today,
    ))
    whiskers.add_task(Task(
        description="Flea medication",
        time="09:00",
        frequency="weekly",
        category="medication",
        priority="medium",
        date=today,
    ))
    whiskers.add_task(Task(
        description="Play session",
        time="14:00",
        frequency="daily",
        category="general",
        priority="low",
        date=today,
    ))

    # --- Initialize Scheduler ---
    scheduler = Scheduler(owner)

    # --- Print Today's Schedule (sorted by time) ---
    print(scheduler.print_schedule())

    # --- Demonstrate Priority Sorting ---
    print("\n\nSchedule Sorted by PRIORITY (high first):")
    print("-" * 40)
    for task in scheduler.sort_by_priority():
        print(f"  {task}")

    # --- Demonstrate Filtering ---
    print("\n\nFilter: Mochi's tasks only")
    print("-" * 30)
    for task in scheduler.filter_by_pet("Mochi"):
        print(f"  {task}")

    print("\nFilter: High priority tasks only")
    print("-" * 30)
    for task in scheduler.get_all_tasks():
        if task.priority == "high":
            print(f"  {task}")

    # --- Next Available Slot ---
    next_slot = scheduler.find_next_available_slot()
    print(f"\n\nNext available slot today: {next_slot}")

    # --- Demonstrate Completing a Task + Recurrence ---
    print("\nMarking Mochi's 'Morning walk' as complete...")
    new_task = scheduler.mark_task_complete("Mochi", 1)
    if new_task:
        print(f"  Completed! New recurring task created: {new_task}")
        print(f"     Scheduled for: {new_task.date}")
        print(f"     Priority preserved: {new_task.priority}")

    # --- JSON Persistence Demo ---
    print("\n\nSaving data to data.json...")
    owner.save_to_json("data.json")
    print("  Saved!")

    loaded = Owner.load_from_json("data.json")
    print(f"  Loaded owner: {loaded.name}, {len(loaded.pets)} pets, "
          f"{len(loaded.get_all_tasks())} tasks")

    # --- Print Updated Summary ---
    print("\nFinal Summary:")
    summary = scheduler.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Cleanup
    import os
    os.remove("data.json")


if __name__ == "__main__":
    main()
