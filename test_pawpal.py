"""
PawPal+ Automated Test Suite
==============================
Tests for core classes, scheduling algorithms, conflict detection,
and recurring task logic.
"""

import pytest
import os
import json
from datetime import datetime, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def today():
    """Return today's date string."""
    return datetime.now().strftime("%Y-%m-%d")


@pytest.fixture
def sample_owner(today):
    """Create a sample owner with two pets and several tasks."""
    owner = Owner(name="Jordan", email="jordan@example.com")

    mochi = Pet(name="Mochi", species="dog", age=3, breed="Golden Retriever")
    whiskers = Pet(name="Whiskers", species="cat", age=5, breed="Siamese")

    mochi.add_task(Task(description="Morning walk", time="07:30", frequency="daily", category="walk", date=today))
    mochi.add_task(Task(description="Breakfast", time="08:00", frequency="daily", category="feeding", date=today))
    mochi.add_task(Task(description="Evening walk", time="18:00", frequency="daily", category="walk", date=today))

    whiskers.add_task(Task(description="Morning feeding", time="07:30", frequency="daily", category="feeding", date=today))
    whiskers.add_task(Task(description="Flea medication", time="09:00", frequency="weekly", category="medication", date=today))

    owner.add_pet(mochi)
    owner.add_pet(whiskers)
    return owner


@pytest.fixture
def scheduler(sample_owner):
    """Create a scheduler from the sample owner."""
    return Scheduler(sample_owner)


# ── Task Tests ────────────────────────────────────────────

class TestTask:
    """Tests for the Task dataclass."""

    def test_task_creation(self, today):
        """Verify a task is created with correct default values."""
        task = Task(description="Walk", time="08:00")
        assert task.description == "Walk"
        assert task.time == "08:00"
        assert task.completed is False
        assert task.frequency == "once"
        assert task.date == today

    def test_mark_complete_changes_status(self):
        """Verify that mark_complete() changes completed to True."""
        task = Task(description="Feed cat", time="09:00")
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_mark_complete_one_time_returns_none(self):
        """Verify that a one-time task returns None on completion."""
        task = Task(description="Vet visit", time="14:00", frequency="once")
        result = task.mark_complete()
        assert result is None

    def test_mark_complete_daily_creates_next(self, today):
        """Verify that completing a daily task creates a new task for tomorrow."""
        task = Task(description="Walk", time="07:30", frequency="daily", date=today)
        new_task = task.mark_complete()
        assert new_task is not None
        assert new_task.completed is False
        assert new_task.description == "Walk"
        expected_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        assert new_task.date == expected_date

    def test_mark_complete_weekly_creates_next(self, today):
        """Verify that completing a weekly task creates a new task for next week."""
        task = Task(description="Flea med", time="09:00", frequency="weekly", date=today)
        new_task = task.mark_complete()
        assert new_task is not None
        expected_date = (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
        assert new_task.date == expected_date

    def test_task_str_representation(self):
        """Verify the string representation shows status and details."""
        task = Task(description="Walk", time="08:00", frequency="daily", category="walk")
        text = str(task)
        assert "08:00" in text
        assert "Walk" in text
        assert "daily" in text

    def test_priority_default(self):
        """Verify default priority is medium."""
        task = Task(description="Walk", time="08:00")
        assert task.priority == "medium"

    def test_priority_emoji(self):
        """Verify priority emojis are correct."""
        assert Task(description="x", time="08:00", priority="high").priority_emoji == "🔴"
        assert Task(description="x", time="08:00", priority="medium").priority_emoji == "🟡"
        assert Task(description="x", time="08:00", priority="low").priority_emoji == "🟢"

    def test_recurrence_preserves_priority(self, today):
        """Verify that recurring tasks keep the original priority."""
        task = Task(description="Med", time="09:00", frequency="daily", priority="high", date=today)
        new_task = task.mark_complete()
        assert new_task.priority == "high"

    def test_task_to_dict_and_from_dict(self, today):
        """Verify JSON serialization roundtrip for Task."""
        task = Task(description="Walk", time="08:00", priority="high", category="walk", frequency="daily", date=today)
        d = task.to_dict()
        restored = Task.from_dict(d)
        assert restored.description == "Walk"
        assert restored.priority == "high"
        assert restored.category == "walk"
        assert restored.frequency == "daily"


# ── Pet Tests ─────────────────────────────────────────────

class TestPet:
    """Tests for the Pet dataclass."""

    def test_add_task_increases_count(self):
        """Verify adding a task increases the pet's task list."""
        pet = Pet(name="Buddy", species="dog", age=2)
        assert len(pet.tasks) == 0
        pet.add_task(Task(description="Walk", time="08:00"))
        assert len(pet.tasks) == 1

    def test_add_task_sets_pet_name(self):
        """Verify that add_task sets the task's pet_name."""
        pet = Pet(name="Buddy", species="dog", age=2)
        task = Task(description="Walk", time="08:00")
        pet.add_task(task)
        assert task.pet_name == "Buddy"

    def test_remove_task_valid_index(self):
        """Verify removing a task by valid index works."""
        pet = Pet(name="Buddy", species="dog", age=2)
        pet.add_task(Task(description="Walk", time="08:00"))
        assert pet.remove_task(0) is True
        assert len(pet.tasks) == 0

    def test_remove_task_invalid_index(self):
        """Verify removing a task by invalid index returns False."""
        pet = Pet(name="Buddy", species="dog", age=2)
        assert pet.remove_task(5) is False

    def test_get_pending_tasks(self):
        """Verify filtering for pending tasks."""
        pet = Pet(name="Buddy", species="dog", age=2)
        pet.add_task(Task(description="Walk", time="08:00"))
        pet.add_task(Task(description="Feed", time="09:00"))
        pet.tasks[0].mark_complete()
        assert len(pet.get_pending_tasks()) == 1
        assert len(pet.get_completed_tasks()) == 1

    def test_pet_with_no_tasks(self):
        """Verify a pet with no tasks returns empty lists."""
        pet = Pet(name="Ghost", species="cat", age=1)
        assert pet.get_pending_tasks() == []
        assert pet.get_completed_tasks() == []


# ── Owner Tests ───────────────────────────────────────────

class TestOwner:
    """Tests for the Owner dataclass."""

    def test_add_and_get_pet(self):
        """Verify adding and retrieving a pet by name."""
        owner = Owner(name="Jordan")
        pet = Pet(name="Mochi", species="dog", age=3)
        owner.add_pet(pet)
        assert owner.get_pet("Mochi") is pet

    def test_get_pet_not_found(self):
        """Verify None is returned for a non-existent pet."""
        owner = Owner(name="Jordan")
        assert owner.get_pet("Ghost") is None

    def test_remove_pet(self):
        """Verify removing a pet by name."""
        owner = Owner(name="Jordan")
        owner.add_pet(Pet(name="Mochi", species="dog", age=3))
        assert owner.remove_pet("Mochi") is True
        assert len(owner.pets) == 0

    def test_get_all_tasks(self, sample_owner):
        """Verify retrieving all tasks across all pets."""
        all_tasks = sample_owner.get_all_tasks()
        assert len(all_tasks) == 5  # 3 from Mochi + 2 from Whiskers


# ── Scheduler Tests ───────────────────────────────────────

class TestScheduler:
    """Tests for the Scheduler class."""

    def test_sort_by_time(self, scheduler):
        """Verify tasks are returned in chronological order."""
        sorted_tasks = scheduler.sort_by_time()
        times = [t.time for t in sorted_tasks]
        assert times == sorted(times)

    def test_sort_preserves_all_tasks(self, scheduler):
        """Verify sorting doesn't lose any tasks."""
        all_tasks = scheduler.get_all_tasks()
        sorted_tasks = scheduler.sort_by_time()
        assert len(sorted_tasks) == len(all_tasks)

    def test_filter_by_pet(self, scheduler):
        """Verify filtering tasks by pet name."""
        mochi_tasks = scheduler.filter_by_pet("Mochi")
        assert len(mochi_tasks) == 3
        assert all(t.pet_name == "Mochi" for t in mochi_tasks)

    def test_filter_by_status(self, scheduler):
        """Verify filtering tasks by completion status."""
        pending = scheduler.filter_by_status(completed=False)
        assert len(pending) == 5  # All tasks start pending

    def test_filter_by_category(self, scheduler):
        """Verify filtering tasks by category."""
        walks = scheduler.filter_by_category("walk")
        assert len(walks) == 2
        assert all(t.category == "walk" for t in walks)

    def test_detect_conflicts(self, scheduler):
        """Verify conflict detection finds tasks at the same time."""
        conflicts = scheduler.detect_conflicts()
        # Mochi's "Morning walk" at 07:30 conflicts with Whiskers' "Morning feeding" at 07:30
        assert len(conflicts) >= 1
        times = [(t1.time, t2.time) for t1, t2 in conflicts]
        assert any(t1 == "07:30" and t2 == "07:30" for t1, t2 in times)

    def test_no_conflicts_when_different_times(self, today):
        """Verify no conflicts when all tasks are at different times."""
        owner = Owner(name="Test")
        pet = Pet(name="Buddy", species="dog", age=2)
        pet.add_task(Task(description="Walk", time="07:00", date=today))
        pet.add_task(Task(description="Feed", time="08:00", date=today))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler.detect_conflicts() == []

    def test_mark_task_complete_recurrence(self, scheduler):
        """Verify completing a recurring task creates a new one."""
        # Mochi's first task (Evening walk, daily)
        new_task = scheduler.mark_task_complete("Mochi", 0)
        assert new_task is not None
        assert new_task.completed is False
        # Mochi should now have 4 tasks (3 original + 1 new)
        mochi = scheduler.owner.get_pet("Mochi")
        assert len(mochi.tasks) == 4

    def test_mark_task_complete_invalid_pet(self, scheduler):
        """Verify None is returned for invalid pet name."""
        result = scheduler.mark_task_complete("NonExistent", 0)
        assert result is None

    def test_get_summary(self, scheduler):
        """Verify the summary dictionary has correct keys and values."""
        summary = scheduler.get_summary()
        assert summary["total_tasks"] == 5
        assert summary["pending"] == 5
        assert summary["completed"] == 0
        assert summary["pets"] == 2

    def test_get_todays_schedule(self, scheduler):
        """Verify today's schedule returns only today's tasks sorted."""
        schedule = scheduler.get_todays_schedule()
        assert len(schedule) > 0
        times = [t.time for t in schedule]
        assert times == sorted(times)

    def test_print_schedule_format(self, scheduler):
        """Verify the formatted schedule contains expected elements."""
        output = scheduler.print_schedule()
        assert "Today's Schedule" in output
        assert "Summary" in output


# ── Edge Case Tests ───────────────────────────────────────

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_owner_no_tasks(self):
        """Verify scheduler handles an owner with no pets."""
        owner = Owner(name="Empty")
        scheduler = Scheduler(owner)
        assert scheduler.get_all_tasks() == []
        assert scheduler.detect_conflicts() == []
        assert scheduler.get_summary()["total_tasks"] == 0

    def test_pet_with_no_tasks_in_schedule(self):
        """Verify scheduler handles a pet with zero tasks."""
        owner = Owner(name="Test")
        owner.add_pet(Pet(name="Lazy", species="cat", age=10))
        scheduler = Scheduler(owner)
        assert scheduler.filter_by_pet("Lazy") == []

    def test_multiple_conflicts_same_time(self, today):
        """Verify detection of multiple tasks at the same time."""
        owner = Owner(name="Busy")
        pet = Pet(name="Buddy", species="dog", age=2)
        pet.add_task(Task(description="Walk", time="08:00", date=today))
        pet.add_task(Task(description="Feed", time="08:00", date=today))
        pet.add_task(Task(description="Groom", time="08:00", date=today))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_conflicts()
        # 3 tasks at same time = 3 conflict pairs (Walk-Feed, Walk-Groom, Feed-Groom)
        assert len(conflicts) == 3


# ── Priority Sorting Tests ────────────────────────────────

class TestPrioritySorting:
    """Tests for priority-based scheduling (Challenge 3)."""

    def test_sort_by_priority(self, today):
        """Verify tasks are sorted by priority (high first) then time."""
        owner = Owner(name="Test")
        pet = Pet(name="Dog", species="dog", age=2)
        pet.add_task(Task(description="Low", time="08:00", priority="low", date=today))
        pet.add_task(Task(description="High", time="09:00", priority="high", date=today))
        pet.add_task(Task(description="Med", time="07:00", priority="medium", date=today))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        result = scheduler.sort_by_priority()
        assert result[0].priority == "high"
        assert result[-1].priority == "low"

    def test_todays_schedule_by_priority(self, today):
        """Verify get_todays_schedule supports priority mode."""
        owner = Owner(name="Test")
        pet = Pet(name="Dog", species="dog", age=2)
        pet.add_task(Task(description="Low early", time="06:00", priority="low", date=today))
        pet.add_task(Task(description="High late", time="20:00", priority="high", date=today))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        by_pri = scheduler.get_todays_schedule(by_priority=True)
        assert by_pri[0].priority == "high"
        by_time = scheduler.get_todays_schedule(by_priority=False)
        assert by_time[0].time == "06:00"


# ── Next Available Slot Tests ─────────────────────────────

class TestNextAvailableSlot:
    """Tests for the next available slot algorithm (Challenge 1)."""

    def test_finds_open_slot(self, today):
        """Verify it finds the first open 30-min slot."""
        owner = Owner(name="Test")
        pet = Pet(name="Dog", species="dog", age=2)
        pet.add_task(Task(description="A", time="07:00", date=today))
        pet.add_task(Task(description="B", time="07:30", date=today))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        slot = scheduler.find_next_available_slot(date=today, start_hour=7)
        assert slot == "08:00"

    def test_returns_none_when_full(self, today):
        """Verify None is returned when all slots are taken."""
        owner = Owner(name="Busy")
        pet = Pet(name="Dog", species="dog", age=1)
        for h in range(7, 21):
            for m in [0, 30]:
                pet.add_task(Task(description=f"t{h}{m}", time=f"{h:02d}:{m:02d}", date=today))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler.find_next_available_slot(date=today) is None

    def test_suggest_reschedule(self, today):
        """Verify suggest_reschedule returns a non-conflicting time."""
        owner = Owner(name="Test")
        pet = Pet(name="P", species="cat", age=2)
        task = Task(description="Conflict", time="07:00", date=today)
        pet.add_task(Task(description="Existing", time="07:00", date=today))
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        suggestion = scheduler.suggest_reschedule(task)
        assert suggestion is not None
        assert suggestion != "07:00"


# ── JSON Persistence Tests ────────────────────────────────

class TestPersistence:
    """Tests for JSON save/load (Challenge 2)."""

    def test_save_and_load(self, today):
        """Verify full roundtrip persistence."""
        owner = Owner(name="TestOwner", email="test@test.com")
        pet = Pet(name="Rex", species="dog", age=4, breed="Lab")
        pet.add_task(Task(description="Walk", time="08:00", priority="high", frequency="daily", date=today))
        owner.add_pet(pet)

        filepath = "/tmp/test_pawpal_persist.json"
        owner.save_to_json(filepath)
        assert os.path.exists(filepath)

        loaded = Owner.load_from_json(filepath)
        assert loaded.name == "TestOwner"
        assert loaded.email == "test@test.com"
        assert len(loaded.pets) == 1
        assert loaded.pets[0].name == "Rex"
        assert loaded.pets[0].breed == "Lab"
        assert len(loaded.pets[0].tasks) == 1
        assert loaded.pets[0].tasks[0].priority == "high"
        assert loaded.pets[0].tasks[0].frequency == "daily"

        os.remove(filepath)

    def test_load_nonexistent_returns_none(self):
        """Verify loading from a nonexistent file returns None."""
        assert Owner.load_from_json("/tmp/nonexistent_pawpal_test.json") is None

    def test_pet_to_dict_and_from_dict(self, today):
        """Verify Pet serialization roundtrip."""
        pet = Pet(name="Buddy", species="dog", age=3, breed="Poodle")
        pet.add_task(Task(description="Walk", time="09:00", priority="low", date=today))
        d = pet.to_dict()
        restored = Pet.from_dict(d)
        assert restored.name == "Buddy"
        assert restored.breed == "Poodle"
        assert len(restored.tasks) == 1
