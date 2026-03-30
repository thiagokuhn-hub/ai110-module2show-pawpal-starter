import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler
from datetime import datetime

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ── Category Emojis & Priority Colors ─────────────────────

CATEGORY_EMOJI = {
    "walk": "🚶",
    "feeding": "🍖",
    "medication": "💊",
    "appointment": "🏥",
    "general": "📋",
}

PRIORITY_COLOR = {
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢",
}

DATA_FILE = "data.json"

# ── Session State + Persistence ───────────────────────────

if "owner" not in st.session_state:
    loaded = Owner.load_from_json(DATA_FILE)
    if loaded:
        st.session_state.owner = loaded
    else:
        st.session_state.owner = Owner(name="Jordan", email="jordan@example.com")

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)

owner = st.session_state.owner
scheduler = st.session_state.scheduler


def save_data():
    """Persist current state to JSON file."""
    owner.save_to_json(DATA_FILE)


# ── Header ────────────────────────────────────────────────

st.title("🐾 PawPal+")
st.markdown("A smart pet care management system that helps you keep your furry friends happy and healthy.")

# ── Sidebar: Owner & Pet Management ──────────────────────

with st.sidebar:
    st.header("👤 Owner Profile")
    new_name = st.text_input("Owner name", value=owner.name)
    if new_name != owner.name:
        owner.name = new_name
        save_data()

    st.divider()
    st.header("🐾 Add a Pet")
    with st.form("add_pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet name", value="")
        col1, col2 = st.columns(2)
        with col1:
            species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
        with col2:
            age = st.number_input("Age", min_value=0, max_value=30, value=1)
        breed = st.text_input("Breed (optional)", value="")
        add_pet_btn = st.form_submit_button("Add Pet")

        if add_pet_btn and pet_name:
            if owner.get_pet(pet_name) is None:
                new_pet = Pet(name=pet_name, species=species, age=age, breed=breed)
                owner.add_pet(new_pet)
                save_data()
                st.success(f"Added {pet_name}!")
            else:
                st.error(f"A pet named '{pet_name}' already exists.")

    if owner.pets:
        st.divider()
        st.header("🗂️ Your Pets")
        for pet in owner.pets:
            pending = len(pet.get_pending_tasks())
            species_emoji = {"dog": "🐕", "cat": "🐈", "bird": "🐦", "rabbit": "🐇"}.get(pet.species, "🐾")
            st.markdown(f"{species_emoji} **{pet.name}** ({pet.breed or pet.species}, age {pet.age}) — {pending} pending")

    st.divider()
    st.caption("💾 Data is auto-saved to `data.json`")

# ── Main Content: Task Scheduling ─────────────────────────

if not owner.pets:
    st.info("👈 Add a pet using the sidebar to get started!")
else:
    # ── Add Task Section ──
    st.subheader("📝 Schedule a Task")
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_pet = st.selectbox("Pet", [p.name for p in owner.pets])
        with col2:
            category = st.selectbox("Category", ["walk", "feeding", "medication", "appointment", "general"])

        task_desc = st.text_input("Task description", value="")

        col3, col4, col5, col6 = st.columns(4)
        with col3:
            task_time = st.time_input("Time", value=None)
        with col4:
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        with col5:
            priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)
        with col6:
            task_date = st.date_input("Date", value=datetime.now().date())

        add_task_btn = st.form_submit_button("Add Task")

        if add_task_btn and task_desc and task_time:
            pet = owner.get_pet(selected_pet)
            if pet:
                new_task = Task(
                    description=task_desc,
                    time=task_time.strftime("%H:%M"),
                    frequency=frequency,
                    category=category,
                    priority=priority,
                    date=task_date.strftime("%Y-%m-%d"),
                )
                pet.add_task(new_task)
                save_data()
                st.success(f"Added '{task_desc}' for {selected_pet} at {task_time.strftime('%H:%M')}!")

    st.divider()

    # ── Conflict Warnings with Suggested Reschedule ──
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.warning(f"⚠️ {len(conflicts)} scheduling conflict(s) detected!")
        for t1, t2 in conflicts:
            suggested = scheduler.suggest_reschedule(t2)
            msg = (
                f"⏰ {t1.pet_name}'s '{t1.description}' conflicts with "
                f"{t2.pet_name}'s '{t2.description}' at {t1.time}"
            )
            if suggested:
                msg += f" — 💡 Try rescheduling to **{suggested}**"
            st.caption(msg)

    # ── Next Available Slot ──
    next_slot = scheduler.find_next_available_slot()
    if next_slot:
        st.success(f"💡 Next available slot today: **{next_slot}**")

    # ── Today's Schedule ──
    st.subheader("📅 Today's Schedule")

    sort_mode = st.radio("Sort by", ["Time", "Priority"], horizontal=True, label_visibility="collapsed")
    by_priority = sort_mode == "Priority"
    todays_tasks = scheduler.get_todays_schedule(by_priority=by_priority)

    if todays_tasks:
        for i, task in enumerate(todays_tasks):
            col1, col2 = st.columns([4, 1])
            with col1:
                status_icon = "✅" if task.completed else "⬜"
                freq_label = f" ({task.frequency})" if task.frequency != "once" else ""
                cat_emoji = CATEGORY_EMOJI.get(task.category, "📋")
                pri_emoji = PRIORITY_COLOR.get(task.priority, "⚪")

                st.markdown(
                    f"{status_icon} {pri_emoji} **[{task.time}]** {cat_emoji} {task.description}{freq_label} "
                    f"— *{task.pet_name}*"
                )
            with col2:
                if not task.completed:
                    pet = owner.get_pet(task.pet_name)
                    if pet:
                        task_idx = pet.tasks.index(task)
                        if st.button("✓ Done", key=f"done_{task.pet_name}_{task_idx}_{task.time}"):
                            new_task = scheduler.mark_task_complete(task.pet_name, task_idx)
                            save_data()
                            if new_task:
                                st.toast(f"Recurring task created for {new_task.date}")
                            st.rerun()
    else:
        st.info("No tasks scheduled for today. Add some above!")

    # ── Filtering ──
    st.divider()
    st.subheader("🔍 Filter Tasks")

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_pet = st.selectbox("Filter by pet", ["All"] + [p.name for p in owner.pets], key="filter_pet")
    with col2:
        filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"], key="filter_status")
    with col3:
        filter_priority = st.selectbox("Filter by priority", ["All", "High", "Medium", "Low"], key="filter_priority")

    filtered = scheduler.get_all_tasks()
    if filter_pet != "All":
        filtered = [t for t in filtered if t.pet_name == filter_pet]
    if filter_status == "Pending":
        filtered = [t for t in filtered if not t.completed]
    elif filter_status == "Completed":
        filtered = [t for t in filtered if t.completed]
    if filter_priority != "All":
        filtered = [t for t in filtered if t.priority == filter_priority.lower()]

    filtered = sorted(filtered, key=lambda t: (-Task.PRIORITY_WEIGHT.get(t.priority, 0), t.time))

    if filtered:
        table_data = []
        for t in filtered:
            table_data.append({
                "Status": "✅" if t.completed else "⬜",
                "Priority": PRIORITY_COLOR.get(t.priority, "⚪") + " " + t.priority.capitalize(),
                "Time": t.time,
                "Task": CATEGORY_EMOJI.get(t.category, "") + " " + t.description,
                "Pet": t.pet_name,
                "Freq": t.frequency,
            })
        st.table(table_data)
    else:
        st.info("No tasks match the selected filters.")

    # ── Summary Dashboard ──
    st.divider()
    st.subheader("📊 Summary")
    summary = scheduler.get_summary()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tasks", summary["total_tasks"])
    col2.metric("Pending", summary["pending"])
    col3.metric("Completed", summary["completed"])
    col4.metric("Conflicts", summary["conflicts"])
