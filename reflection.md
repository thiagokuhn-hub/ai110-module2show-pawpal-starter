# PawPal+ Project Reflection

## 1. System Design

### a. Initial design

My initial UML design included four core classes: `Task`, `Pet`, `Owner`, and `Scheduler`. The `Task` class (built as a Python dataclass) holds all the details of a single care activity, including description, scheduled time, frequency, category, completion status, and date. The `Pet` class stores pet information (name, species, age, breed) and manages a list of `Task` objects. The `Owner` class manages multiple `Pet` objects and provides a method to aggregate all tasks across pets. Finally, the `Scheduler` class serves as the central "brain" that connects to an `Owner` to retrieve, sort, filter, and analyze all tasks.

I chose to keep relationships simple: an Owner "has" Pets, a Pet "has" Tasks, and a Scheduler "manages" an Owner. This kept the dependency graph flat and easy to reason about.

### b. Design changes

Yes, the design evolved during implementation. The most significant change was adding a `date` field to the `Task` class. My initial design only had a `time` attribute (HH:MM format), but I realized during conflict detection that I needed to distinguish between tasks on different days,especially for recurring tasks. Adding the date field also made `get_todays_schedule()` possible, which filters tasks to only show the current day's plan. I also added a `category` field to `Task` to support filtering by task type (walk, feeding, medication, etc.), which wasn't in my original UML but proved essential for a useful scheduler.

## 2. Scheduling Logic and Tradeoffs

### a. Constraints and priorities

My scheduler considers time (scheduling tasks chronologically), frequency (handling daily/weekly recurrence), and category (allowing filtered views). Time was the primary constraint because pet care tasks are inherently time-bound,medications need to be given at specific times, walks have preferred windows, and feedings follow a routine. I decided time mattered most because a pet owner's daily experience is fundamentally organized around "what do I need to do next?"

### b. Tradeoffs

One key tradeoff is that my conflict detection only checks for exact time matches rather than overlapping time durations. Two tasks at 08:00 and 08:15 won't be flagged as conflicting, even though a 30-minute walk at 08:00 would overlap with a feeding at 08:15. I made this tradeoff because adding duration-based overlap detection would significantly increase complexity (requiring start + end time calculations) for a scenario where most pet care tasks are relatively short. For a typical household with 5-10 daily tasks, exact-match detection catches the most common scheduling mistakes without over-alerting the user.

## 3. AI Collaboration

### a. How you used AI

I used AI tools throughout the project for several purposes:

- **Design brainstorming**: I described the pet care scenario and asked AI to suggest the main classes, their attributes, and methods, which helped me draft the initial UML diagram.
- **Code scaffolding**: I used AI to generate class skeletons from my UML design, including Python dataclass decorators and type hints.
- **Mermaid.js generation**: I asked AI to create the UML class diagram in Mermaid syntax based on my class descriptions.
- **Test generation**: I described the behaviors I wanted to verify, and AI helped draft pytest test functions with appropriate fixtures and assertions.
- **Debugging**: When my recurring task logic wasn't creating the correct next date, I shared the code with AI and it identified that I needed to use `timedelta` properly.

The most helpful prompts were specific ones that referenced my actual code, like "Based on my Task class, how should mark_complete handle daily recurrence?" rather than vague requests.

### b. Judgment and verification

One moment where I modified an AI suggestion was during test generation. The AI initially suggested testing conflict detection with mock objects, but I chose to use real `Task`, `Pet`, and `Owner` instances instead. This was because mock objects would have hidden potential integration bugs,for example, if `Pet.add_task()` failed to set `pet_name`, the conflict detection test with mocks would still pass but the real system would break. By using real objects in tests, I verified the full chain of interactions, which gave me higher confidence in the system's correctness.

## 4. Testing and Verification

### a. What you tested

I tested the following core behaviors:

- **Task completion**: Verifying that `mark_complete()` changes the status and that one-time tasks return `None` while recurring tasks return a new `Task`.
- **Recurrence logic**: Confirming that daily tasks generate a new task for tomorrow and weekly tasks for next week, with correct dates calculated via `timedelta`.
- **Sorting correctness**: Ensuring tasks come back in chronological order regardless of insertion order.
- **Conflict detection**: Verifying that tasks at the same time on the same day are flagged, and that different-time tasks are not.
- **Edge cases**: Empty owners with no pets, pets with no tasks, and multiple tasks at the same time.

These tests were important because they verify the algorithmic "brain" of the system,if sorting or conflict detection is wrong, the entire user experience breaks.

### b. Confidence

I am fairly confident (4 out of 5 stars) that the scheduler works correctly for typical use cases. The areas I would test next with more time include: date boundary edge cases (tasks spanning midnight), time zone handling, very large task lists (performance testing), and the interaction between completing a recurring task and the conflict detection of its newly generated successor.

## 5. Reflection

### a. What went well

I'm most satisfied with the clean separation between the logic layer (`pawpal_system.py`) and the UI (`app.py`). Building and verifying everything through the CLI demo (`main.py`) first meant that by the time I connected the Streamlit UI, I was confident the backend worked correctly. The dataclass approach for `Task` and `Pet` kept the code clean and readable.

### b. What you would improve

If I had another iteration, I would add duration-based conflict detection instead of just exact-time matching (checking for overlapping time ranges rather than just exact matches). I'd also explore adding notifications or reminders that alert the owner before a task is due, and potentially a mobile-friendly interface.

### c. Key takeaway

The most important thing I learned is that designing the system architecture before writing code saves enormous time. By drafting the UML diagram first and thinking through class relationships, I avoided several redesigns that would have been painful to fix later. Working with AI was most effective when I treated it as a collaborator rather than a solution generator,giving it specific context about my existing code and asking targeted questions produced much better results than vague requests.

## 6. Optional Extensions

### a. Advanced Algorithmic Capability,Next Available Slot

I added a `find_next_available_slot()` method to the Scheduler that scans from 07:00 to 21:00 in 30-minute increments and returns the first time that doesn't conflict with any existing task. I used Agent Mode by describing the desired behavior: "Add a method to `Scheduler` in `#file:pawpal_system.py` that finds the next open 30-minute time slot on a given date, scanning from 7 AM to 9 PM." The AI generated a clean implementation using `timedelta` for iteration and a set of occupied times for O(1) lookups, which I then integrated into the UI to show a "Next available slot" suggestion. I also added a `suggest_reschedule()` method that pairs with conflict detection to recommend alternative times.

### b. Data Persistence

I added `save_to_json()` and `load_from_json()` methods to the `Owner` class, along with `to_dict()` and `from_dict()` serialization methods on all three data classes (`Task`, `Pet`, `Owner`). This allows the app to remember pets and tasks between Streamlit sessions. I chose manual dictionary conversion over a library like `marshmallow` because the data model is simple enough that custom serialization keeps the code self-contained with no extra dependencies.

### c. Priority-Based Scheduling

I added a `priority` field to the `Task` class (high, medium, low) with a `PRIORITY_WEIGHT` dictionary that assigns numeric weights (3, 2, 1). The `sort_by_priority()` method sorts first by priority weight (descending) then by time, so high-priority tasks always appear first. In the Streamlit UI, priorities are color-coded with emojis: red for High, yellow for Medium, green for Low. A radio toggle lets the user switch between time-based and priority-based schedule views.

### d. Professional UI Formatting

I added category-specific emojis (walk, feeding, medication, appointment, general) and species emojis in the sidebar (dog, cat, bird, rabbit). The filter table now shows priority colors and category emojis inline, and conflict warnings include AI-suggested reschedule times.

### Prompt Comparison (Multi-Model)

I compared how two different AI models approached the "next available slot" algorithm:

**Prompt given to both**: "Write a Python method for a Scheduler class that finds the next available 30-minute time slot on a given date, scanning from 7 AM to 9 PM, avoiding any times already occupied by existing tasks."

**Claude's approach**: Generated a solution using a `set` of occupied time strings and a `while` loop with `timedelta` increments. The code was concise (15 lines) and Pythonic, using `strftime` for formatting and set membership for O(1) lookups. It handled the edge case of no available slots by returning `None`.

**GPT-4's approach**: Generated a similar solution but used a `for` loop over `range(start_hour * 60, end_hour * 60, 30)` to iterate in minutes, then converted minutes back to hours and minutes with `divmod()`. It also returned a list of all available slots rather than just the first one.

**Evaluation**: I preferred Claude's approach for this specific use case because returning a single "next available" slot is more actionable for the UI,a pet owner wants to know "when can I schedule this?" not "here are all 28 possible slots." However, GPT-4's approach of returning all slots would be more flexible if I later wanted to let the user pick from a dropdown of available times. I ended up implementing Claude's single-slot version for the MVP and noted the multi-slot idea as a future enhancement. This comparison taught me that different models optimize for different assumptions about how the output will be used, and the "better" solution depends entirely on the product context.
