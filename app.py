import streamlit as st
from pawpal_system import Owner, Pet, Task, TaskCategory, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
PawPal+ is a pet care planning assistant. It helps a pet owner plan care tasks for their pet(s)
based on constraints like time, priority, and preferences.
"""
)

# Step 2: Manage the app memory via session_state
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", age=30)

owner: Owner = st.session_state.owner

st.sidebar.header("Owner")
st.sidebar.write(owner.get_profile())

with st.sidebar.expander("Edit Owner Info", expanded=False):
    new_owner_name = st.text_input("Owner name", value=owner.name)
    new_owner_age = st.number_input("Owner age", min_value=0, max_value=120, value=owner.age)
    new_available_start = st.time_input("Available start", value=owner.available_start)
    new_available_end = st.time_input("Available end", value=owner.available_end)

    if st.button("Save owner info", key="save_owner_info"):
        owner.name = new_owner_name.strip() or owner.name
        owner.age = new_owner_age
        owner.available_start = new_available_start
        owner.available_end = new_available_end
        st.sidebar.success("Owner info and availability updated")
        # Keep owner in session state updated
        st.session_state.owner = owner

# Pet creation form
with st.form(key="add_pet_form"):
    st.subheader("Add a Pet")
    new_pet_name = st.text_input("Pet name")
    new_pet_age = st.number_input("Pet age", min_value=0, max_value=30, value=1)
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    new_pet_breed = st.text_input("Breed")
    submitted_pet = st.form_submit_button("Add Pet")

    if submitted_pet:
        if new_pet_name.strip() == "":
            st.warning("Enter a pet name")
        else:
            pet = Pet(
                name=new_pet_name.strip(),
                age=new_pet_age,
                species=new_pet_species,
                breed=new_pet_breed.strip() or "Unknown",
            )
            try:
                owner.add_pet(pet)
                st.success(f"Pet '{pet.name}' added")
            except ValueError as e:
                st.error(str(e))

# Task creation form
with st.form(key="add_task_form"):
    st.subheader("Add a Task")
    selected_pet_name = st.selectbox("Select pet", [p.name for p in owner.pets] or ["(no pets)"])
    task_title = st.text_input("Task title")
    task_description = st.text_area("Description")
    task_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=15)
    task_priority = st.selectbox("Priority", [1, 2, 3, 4, 5], index=3)
    task_category = st.selectbox("Category", list(TaskCategory))
    task_repeat = st.selectbox("Repeat rule", ["", "daily", "weekly", "weekdays", "weekends"])
    task_submitted = st.form_submit_button("Add Task")

    if task_submitted:
        if not owner.pets:
            st.error("Add a pet first")
        elif selected_pet_name == "(no pets)":
            st.error("Select a real pet")
        elif not task_title.strip():
            st.error("Enter a task title")
        else:
            task = Task(
                title=task_title.strip(),
                description=task_description.strip(),
                duration_minutes=task_duration,
                priority=task_priority,
                category=task_category,
                pet_name=selected_pet_name,
                repeat_rule=task_repeat.strip() if task_repeat else None,
                due_date=date.today() if task_repeat else None,
            )
            pet = owner.get_pet(selected_pet_name)
            if pet is not None:
                pet.add_task(task)
                st.success(f"Task '{task.title}' added for {pet.name}")
            else:
                st.error("Selected pet not found")

st.divider()

st.subheader("Current Pets & Tasks")
if owner.pets:
    for p in owner.pets:
        with st.expander(f"{p.name} ({p.species})", expanded=False):
            st.write(p.get_info())
            if p.tasks:
                for t in p.tasks:
                    st.write(
                        f"- {t.title}, {t.duration_minutes}m, priority {t.priority}, category {t.category.value}, completed={t.completed}, repeat={t.repeat_rule}, due={t.due_date}"
                    )

                task_titles = [t.title for t in p.tasks]
                selected_complete = st.selectbox("Mark complete", task_titles, key=f"complete_{p.name}")
                if st.button("Mark selected task complete", key=f"complete_btn_{p.name}"):
                    try:
                        clone = owner.mark_task_complete(p.name, selected_complete)
                        if clone:
                            st.success(f"Task '{selected_complete}' marked complete and next {clone.repeat_rule} task created for {clone.due_date}")
                        else:
                            st.success(f"Task '{selected_complete}' marked complete")
                        # Set a flag to refresh sections without stopping the script.
                        st.session_state["task_completed"] = True
                    except ValueError as e:
                        st.error(str(e))
            else:
                st.info("No tasks for this pet yet.")
else:
    st.info("No pets added yet.")

st.divider()

st.subheader("Build Schedule")
from datetime import date

selected_date = st.session_state.get("selected_date") or st.date_input("Date", value=date.today())
st.session_state.selected_date = selected_date

if st.button("Generate schedule"):
    scheduler = Scheduler(owner=owner, date=selected_date)
    schedule = scheduler.generate_daily_plan()

    if schedule:
        st.success("Schedule generated")
        st.text(scheduler.explain_plan())
    else:
        st.warning("No tasks could be scheduled (check available hours / task duration)")


if st.button("Show schedule summary"):
    scheduler = Scheduler(owner=owner, date=selected_date)
    scheduler.generate_daily_plan()
    st.json(scheduler.get_summary())

