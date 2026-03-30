"""
PawPal+ Smart Pet Care Management System
=========================================
Core logic layer containing all backend classes for managing pets,
owners, tasks, and intelligent scheduling.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import json
import os


@dataclass
class Task:
    """Represents a single pet care activity with scheduling and status tracking."""

    PRIORITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}

    description: str
    time: str  # "HH:MM" format
    frequency: str = "once"  # "once", "daily", "weekly"
    category: str = "general"  # "feeding", "walk", "medication", "appointment", "general"
    priority: str = "medium"  # "low", "medium", "high"
    completed: bool = False
    pet_name: str = ""
    date: Optional[str] = None  # "YYYY-MM-DD" format

    def __post_init__(self):
        """Set default date to today if not provided."""
        if self.date is None:
            self.date = datetime.now().strftime("%Y-%m-%d")

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as complete and return a new recurring task if applicable."""
        self.completed = True
        if self.frequency in ("daily", "weekly"):
            return self._create_next_occurrence()
        return None

    def _create_next_occurrence(self) -> "Task":
        """Generate the next occurrence of a recurring task."""
        current_date = datetime.strptime(self.date, "%Y-%m-%d")
        if self.frequency == "daily":
            next_date = current_date + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = current_date + timedelta(weeks=1)
        else:
            next_date = current_date

        return Task(
            description=self.description,
            time=self.time,
            frequency=self.frequency,
            category=self.category,
            priority=self.priority,
            completed=False,
            pet_name=self.pet_name,
            date=next_date.strftime("%Y-%m-%d"),
        )

    @property
    def priority_emoji(self) -> str:
        """Return a color-coded emoji for the task's priority level."""
        return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(self.priority, "⚪")

    def to_dict(self) -> dict:
        """Convert task to a JSON-serializable dictionary."""
        return {
            "description": self.description,
            "time": self.time,
            "frequency": self.frequency,
            "category": self.category,
            "priority": self.priority,
            "completed": self.completed,
            "pet_name": self.pet_name,
            "date": self.date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create a Task instance from a dictionary."""
        return cls(
            description=data["description"],
            time=data["time"],
            frequency=data.get("frequency", "once"),
            category=data.get("category", "general"),
            priority=data.get("priority", "medium"),
            completed=data.get("completed", False),
            pet_name=data.get("pet_name", ""),
            date=data.get("date"),
        )

    def __str__(self) -> str:
        """Return a human-readable string representation of the task."""
        status = "✅" if self.completed else "⬜"
        freq = f" ({self.frequency})" if self.frequency != "once" else ""
        return f"{status} {self.priority_emoji} [{self.time}] {self.description}{freq} - {self.category}"


@dataclass
class Pet:
    """Stores pet details and manages a list of associated tasks."""

    name: str
    species: str  # "dog", "cat", "bird", etc.
    age: int
    breed: str = ""
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_index: int) -> bool:
        """Remove a task by index from this pet's task list."""
        if 0 <= task_index < len(self.tasks):
            self.tasks.pop(task_index)
            return True
        return False

    def get_pending_tasks(self) -> list:
        """Return all incomplete tasks for this pet."""
        return [t for t in self.tasks if not t.completed]

    def get_completed_tasks(self) -> list:
        """Return all completed tasks for this pet."""
        return [t for t in self.tasks if t.completed]

    def to_dict(self) -> dict:
        """Convert pet to a JSON-serializable dictionary."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "breed": self.breed,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Create a Pet instance from a dictionary."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            age=data["age"],
            breed=data.get("breed", ""),
        )
        for task_data in data.get("tasks", []):
            task = Task.from_dict(task_data)
            pet.tasks.append(task)
        return pet

    def __str__(self) -> str:
        """Return a human-readable summary of the pet."""
        return f"{self.name} ({self.species}, {self.breed}, age {self.age})"


@dataclass
class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    name: str
    email: str = ""
    pets: list = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's collection."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name from the owner's collection."""
        for i, pet in enumerate(self.pets):
            if pet.name == pet_name:
                self.pets.pop(i)
                return True
        return False

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Retrieve a pet by name."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> list:
        """Retrieve all tasks across all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def to_dict(self) -> dict:
        """Convert owner to a JSON-serializable dictionary."""
        return {
            "name": self.name,
            "email": self.email,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Create an Owner instance from a dictionary."""
        owner = cls(name=data["name"], email=data.get("email", ""))
        for pet_data in data.get("pets", []):
            owner.pets.append(Pet.from_dict(pet_data))
        return owner

    def save_to_json(self, filepath: str = "data.json") -> None:
        """Persist the owner, pets, and all tasks to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str = "data.json") -> Optional["Owner"]:
        """Load an owner from a JSON file, or return None if the file doesn't exist."""
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Return a summary of the owner and their pets."""
        pet_names = ", ".join(p.name for p in self.pets) if self.pets else "No pets"
        return f"{self.name} - Pets: {pet_names}"


class Scheduler:
    """The 'Brain' of PawPal+ that retrieves, organizes, and manages tasks across pets."""

    def __init__(self, owner: Owner):
        """Initialize the scheduler with an owner."""
        self.owner = owner

    def get_all_tasks(self) -> list:
        """Retrieve all tasks from the owner's pets."""
        return self.owner.get_all_tasks()

    def sort_by_time(self, tasks: Optional[list] = None) -> list:
        """Sort tasks chronologically by their scheduled time."""
        if tasks is None:
            tasks = self.get_all_tasks()
        return sorted(tasks, key=lambda t: t.time)

    def sort_by_priority(self, tasks: Optional[list] = None) -> list:
        """Sort tasks by priority (high first), then by time within each priority level."""
        if tasks is None:
            tasks = self.get_all_tasks()
        return sorted(
            tasks,
            key=lambda t: (-Task.PRIORITY_WEIGHT.get(t.priority, 0), t.time),
        )

    def find_next_available_slot(self, date: Optional[str] = None, duration_minutes: int = 30, start_hour: int = 7, end_hour: int = 21) -> Optional[str]:
        """Find the next available time slot on a given date that has no conflicts.

        Scans from start_hour to end_hour in 30-minute increments and returns
        the first HH:MM slot that doesn't overlap with any existing task.
        Returns None if no slot is available.
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        occupied_times = set()
        for task in self.get_all_tasks():
            if task.date == date and not task.completed:
                occupied_times.add(task.time)

        current = datetime.strptime(f"{date} {start_hour:02d}:00", "%Y-%m-%d %H:%M")
        end = datetime.strptime(f"{date} {end_hour:02d}:00", "%Y-%m-%d %H:%M")

        while current < end:
            slot = current.strftime("%H:%M")
            if slot not in occupied_times:
                return slot
            current += timedelta(minutes=duration_minutes)

        return None

    def suggest_reschedule(self, task: Task) -> Optional[str]:
        """Suggest a new time for a task that has a conflict."""
        return self.find_next_available_slot(date=task.date)

    def filter_by_pet(self, pet_name: str) -> list:
        """Filter tasks belonging to a specific pet."""
        return [t for t in self.get_all_tasks() if t.pet_name == pet_name]

    def filter_by_status(self, completed: bool = False) -> list:
        """Filter tasks by their completion status."""
        return [t for t in self.get_all_tasks() if t.completed == completed]

    def filter_by_category(self, category: str) -> list:
        """Filter tasks by their category."""
        return [t for t in self.get_all_tasks() if t.category == category]

    def get_todays_schedule(self, by_priority: bool = False) -> list:
        """Get today's tasks sorted by time or by priority then time."""
        today = datetime.now().strftime("%Y-%m-%d")
        todays_tasks = [t for t in self.get_all_tasks() if t.date == today]
        if by_priority:
            return self.sort_by_priority(todays_tasks)
        return self.sort_by_time(todays_tasks)

    def detect_conflicts(self) -> list:
        """Detect scheduling conflicts where two tasks overlap in time."""
        conflicts = []
        tasks = self.sort_by_time()
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                if tasks[i].time == tasks[j].time and tasks[i].date == tasks[j].date:
                    if not tasks[i].completed and not tasks[j].completed:
                        conflicts.append((tasks[i], tasks[j]))
        return conflicts

    def mark_task_complete(self, pet_name: str, task_index: int) -> Optional[Task]:
        """Mark a task as complete and handle recurrence logic."""
        pet = self.owner.get_pet(pet_name)
        if pet and 0 <= task_index < len(pet.tasks):
            task = pet.tasks[task_index]
            new_task = task.mark_complete()
            if new_task:
                pet.add_task(new_task)
                return new_task
        return None

    def get_summary(self) -> dict:
        """Generate a summary of all tasks across all pets."""
        all_tasks = self.get_all_tasks()
        return {
            "total_tasks": len(all_tasks),
            "completed": sum(1 for t in all_tasks if t.completed),
            "pending": sum(1 for t in all_tasks if not t.completed),
            "conflicts": len(self.detect_conflicts()),
            "pets": len(self.owner.pets),
        }

    def print_schedule(self) -> str:
        """Generate a formatted schedule string for display."""
        schedule = self.get_todays_schedule()
        if not schedule:
            return "No tasks scheduled for today!"

        lines = ["📅 Today's Schedule", "=" * 40]
        for task in schedule:
            lines.append(f"  🐾 {task.pet_name}: {task}")
        lines.append("=" * 40)

        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append(f"\n⚠️  {len(conflicts)} conflict(s) detected:")
            for t1, t2 in conflicts:
                lines.append(
                    f"  ⏰ {t1.pet_name}'s '{t1.description}' conflicts with "
                    f"{t2.pet_name}'s '{t2.description}' at {t1.time}"
                )

        summary = self.get_summary()
        lines.append(f"\n📊 Summary: {summary['pending']} pending, {summary['completed']} completed")

        return "\n".join(lines)
