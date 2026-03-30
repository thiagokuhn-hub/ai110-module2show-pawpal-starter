# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the CLI demo

```bash
python main.py
```

## Features

PawPal+ includes the following implemented features:

- **Owner & Pet Management**: Create an owner profile and add multiple pets with species, age, and breed information.
- **Task Scheduling**: Add care tasks with descriptions, times, categories (walk, feeding, medication, appointment, general), and frequency settings.
- **Sorting by Time**: All tasks are automatically sorted chronologically using Python's `sorted()` with a lambda key on the `HH:MM` time string.
- **Filtering**: Filter tasks by pet name, completion status, or category to quickly find what you need.
- **Conflict Detection**: The scheduler scans for overlapping tasks (same time and date) and displays warning messages so the owner can adjust the plan.
- **Daily Recurrence**: When a daily or weekly task is marked complete, a new instance is automatically generated for the next occurrence using `timedelta`.
- **Summary Dashboard**: View at-a-glance metrics including total tasks, pending count, completed count, and number of conflicts.

## Smarter Scheduling

The `Scheduler` class acts as the "brain" of PawPal+. It connects to the `Owner` object to retrieve all tasks across all pets and provides several algorithmic features:

- **Chronological sorting** using `sorted()` with a lambda key that compares `HH:MM` time strings.
- **Priority-based sorting** using a weighted system (High=3, Medium=2, Low=1) that sorts by priority first, then by time within each level.
- **Multi-criteria filtering** by pet name, task category, completion status, and priority level.
- **Conflict detection** using a pairwise comparison algorithm that checks for matching time + date pairs among uncompleted tasks. This is a lightweight O(n²) approach that checks for exact time matches rather than overlapping durations — a reasonable tradeoff for typical household pet schedules with fewer than 50 daily tasks.
- **Next available slot finder** that scans from 7 AM to 9 PM in 30-minute increments and returns the first time with no conflicts — useful for quickly scheduling new tasks.
- **Reschedule suggestions** that pair with conflict detection to recommend alternative times when overlaps are found.
- **Recurring task automation** using Python's `timedelta` to calculate the next due date when a daily or weekly task is completed.
- **Data persistence** via JSON serialization — all pets, tasks, and owner data are automatically saved and restored between sessions.

## Optional Extensions Implemented

- **Challenge 1 — Next Available Slot**: The `find_next_available_slot()` method uses a set-based lookup of occupied times and scans in configurable increments. Agent Mode was used to plan the algorithm.
- **Challenge 2 — Data Persistence**: `save_to_json()` and `load_from_json()` on the `Owner` class, with `to_dict()`/`from_dict()` serialization on all classes. Data auto-saves on every action.
- **Challenge 3 — Priority Scheduling**: Tasks have High/Medium/Low priority. The UI shows color-coded indicators (🔴🟡🟢) and supports toggling between time-based and priority-based schedule views.
- **Challenge 4 — Professional UI**: Category emojis (🚶🍖💊🏥📋), species emojis in the sidebar, priority color coding in filter tables, and conflict reschedule suggestions.
- **Challenge 5 — Multi-Model Comparison**: Documented in `reflection.md` Section 6, comparing Claude vs. GPT-4 approaches to the next-available-slot algorithm.

## System Architecture

The system is built around four core classes:

- **`Task`** (dataclass): Represents a single care activity with description, time, frequency, category, status, and date.
- **`Pet`** (dataclass): Stores pet details and manages a list of associated tasks.
- **`Owner`** (dataclass): Manages multiple pets and provides access to aggregated task data.
- **`Scheduler`**: The orchestration layer that retrieves, sorts, filters, and analyzes tasks across all pets.

See `uml_diagram.mermaid` for the full class diagram, or view the rendered PNG at `uml_final.png`.

## Testing PawPal+

Run the automated test suite with:

```bash
python -m pytest
```

The test suite covers:

- Task creation with correct defaults
- `mark_complete()` status changes
- Recurring task generation (daily and weekly)
- Pet task management (add, remove, pending/completed filters)
- Owner pet management (add, remove, lookup)
- Scheduler sorting correctness (chronological order)
- Conflict detection (same-time tasks flagged)
- Filter accuracy (by pet, status, category)
- Edge cases (empty owner, pet with no tasks, multiple conflicts)

**Confidence Level**: ⭐⭐⭐⭐ (4/5) — The core scheduling logic is thoroughly tested. Additional edge cases around date boundaries and time zone handling would increase confidence further.

## 📸 Demo

Run `streamlit run app.py` to see the full interactive UI with pet management, task scheduling, conflict warnings, filtering, and summary dashboard.
