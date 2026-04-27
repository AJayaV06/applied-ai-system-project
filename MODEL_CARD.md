# 🐾 Model Card: PawPal+ Scheduler

## 1. Model Name

PawPal+ Scheduler 1.0

## 2. Intended Use

PawPal+ is a pet care task scheduling system designed to help pet owners plan daily care activities. It generates a daily schedule based on pet tasks, owner availability, task priority, and pet-specific care guidance. This system is intended for educational exploration and personal pet planning, not for medical, veterinary, or safety-critical decisions. The planner assumes that the owner will review the schedule and make the final decision about task order and timing.

## 3. How the Model Works

The scheduler uses a rule-based approach that combines several signals to decide when and whether to schedule a task.

First, the system reads all tasks for the owner's pets and filters out any that are already completed or not due. Then it sorts tasks by priority (high-priority tasks first), preferred time, and duration.

Next, the scheduler places each task into the owner's available time windows (for example, morning 7:00–9:00 and evening 6:00–9:00). If a task has a fixed start time, it tries to honor that. If a task is flexible, it finds the first available slot. If a task does not fit in any window, it goes on an unscheduled list.

Finally, the system retrieves pet-specific guidance (for example, "dogs do well with activity before meals") and uses it to explain why each task was placed at that time. It also checks for conflicts and flags them so the human can review them.

I changed the starter logic to make retrieval-based explanations fully visible in the UI, to add an explicit agentic workflow that drafts and reviews the plan, and to include a built-in health-check script.

## 4. Data

PawPal+ uses two types of data:

**Pet care knowledge base:** A small JSON file (`assets/pet_care_notes.json`) with 5 guidance entries covering dogs, cats, puppies, senior pets, and medication consistency. Each entry specifies species, age range, task category, and a short recommendation. This is a static, local knowledge base.

**User input:** Owner name, age, availability windows, pet names, ages, species, breed, and task details (title, description, duration, priority, category, repeat rule, preferred start time).

The knowledge base is intentionally small and covers common pet categories. It does not represent all pet types, all medical conditions, or all behavioral scenarios. The system works best with clear, complete task information and well-defined availability windows.

## 5. Strengths

PawPal+ works well when the user's preferences are clear and the task list is moderate in size (5–15 tasks per day).

- **Priority handling:** The system correctly prioritizes high-urgency tasks (medication, walks) over lower-priority ones (grooming, enrichment).
- **Availability enforcement:** It respects the owner's time windows and does not schedule tasks outside them.
- **Clarity and transparency:** The planner shows its work, including intermediate planning steps, conflict warnings, and unscheduled tasks, so the owner can always understand why the plan looks the way it does.
- **Recurring task support:** Daily and weekly tasks are automatically rescheduled after completion, reducing manual re-entry.
- **Conflict detection:** The system flags overlapping or simultaneous tasks so the human can review them.

## 6. Limitations and Bias

PawPal+ has several known limitations and biases.

- **Rule-based, not optimized:** The scheduler uses a greedy algorithm that fills time windows in priority order. It does not try to find a globally optimal schedule; this means it can leave lower-priority tasks unscheduled even if a small rearrangement would fit them.
- **Small knowledge base:** The pet-care guidance covers only 5 common scenarios. It does not account for breed-specific needs, medical conditions, behavioral issues, or individual pet quirks.
- **Single-language guidance:** All recommendations are in English and may not reflect diverse cultural pet-care practices.
- **Bias toward exact matches:** The scoring heavily rewards exact genre, species, or mood matches, which can favor well-represented categories and disadvantage edge cases.
- **No learning:** The system does not adapt based on how the owner actually uses the schedule or whether the pet responds well to it. Feedback is not collected or used to improve future recommendations.
- **Assumes clear task data:** If task titles, durations, or priority levels are vague or missing, the planner may make poor decisions.

## 7. Evaluation

I tested PawPal+ on six core scenarios:

1. **Task filtering by pet:** Added tasks for multiple pets and verified that filtering returned only the correct pet's tasks.
2. **Priority-based scheduling:** Created a mix of high and low-priority tasks and confirmed that high-priority ones were scheduled first.
3. **Availability window enforcement:** Set narrow availability windows and verified that tasks longer than the window were marked unscheduled.
4. **Conflict detection:** Scheduled two tasks at the same start time and confirmed that the system flagged the overlap.
5. **Recurring task rescheduling:** Marked a daily task as complete and confirmed that a new occurrence was created for the next day.
6. **Agentic workflow:** Ran the multi-step planner and confirmed that all intermediate steps were visible (draft, review, final explanation).

I looked for schedules that made intuitive sense. I was surprised that a few simple scoring rules produced recommendations that felt reasonably aligned with the user's vibe, especially when the top tasks matched the priority and availability. I ran a system health check and confirmed 3/3 checks passed (priority scheduling, conflict detection, availability handling).

## 8. Future Work

If I continued this project, I would:

- **Expand the knowledge base:** Add more pet types, age ranges, medical conditions, and behavioral scenarios.
- **Add more task features:** Include acousticness, valence, and danceability equivalents for pets, such as noise level, physical exertion, and social interaction.
- **Improve diversity in recommendations:** Add a diversity penalty so the top results do not feel too similar or repetitive.
- **Collect user feedback:** Log which tasks the owner actually completed and in what order, then use that to refine the scoring over time.
- **Handle complex user preferences:** Support tasks that have dependencies (for example, "feed before playtime") or soft constraints (for example, "prefer afternoon walks when possible").

## 9. Personal Reflection

My biggest learning was realizing that a simple, rule-based system can still produce usable recommendations if the rules are grounded in clear user intent and the human stays in control. I was surprised how much clarity came from just showing the intermediate steps (draft → review → final explanation) instead of hiding the reasoning. AI tools helped me move faster in designing the classes and testing edge cases, but I still had to manually verify the scoring logic and run sanity checks on the final schedules. If I kept going, I would collect real user feedback, expand the knowledge base, and improve the algorithm to handle edge cases like conflicting priorities or multi-pet coordination. The biggest takeaway is that AI systems are most effective when they remain transparent and put the human in charge of the final decision.
