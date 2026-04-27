# PawPal+ Project Reflection

## 1. System Design

--Add and edit tasks 
--Generate and view daily schedule 
--Enter owner and pet info

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

-- Classes: pet, owner, task, schedule
-- Pet: name, age, what animal, what breed
    -- stores metadata and can get the information through get_info
-- Owner: name, age, pets list
    -- manages pets, manages schedule availabilty, represents the human user
-- Task: what task, when to do, repeat?, how long does it take
    -- represents the task needed to take care of the pet, validate fields, and checks for repetition of tasks
-- Schedule: list of tasks in the schedule
    -- maintaisn tasks for a single task, sorts by priority, detects conflicts, generates a reasoning, and summary

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

-- Yes, I made a few changes. One major change I made was having a relationship between a task and a pet. Intially, there was no relationship but when mentioned by Copilot I realized that this is a important relationship. If a owner has multiple pets and a task is "feed pet", it might be hard to identify the specific pet. So having a relationship between the 2 classes would help specify the tasks for specific pets.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

-- The scheduler considers time, completion, recurring tasks, and also conflicts.

-- Time is very importnat because daily schedule depends on it. Completion avoides repeated tasks. Recurrence is for routines. And conflicts helps imporve reliability.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

-- The scheduler first fills as many high priority tasks as possible. It uses simple planning which has a quick generation time. Howveer. It can skip lower priority tasks and optimal arrangement of tasks. It may skip over tasks that would fit if the tasks were rescheduled after future entries or used a non greedy scheduling apporach. This is a reasonable trade off because priority is more important than perdect schedule. Advanced rescheduling is harder to verify. And fir this scale of app that has less than 10 tasks per day, this is a reasonable tradeoff.

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

-- I used Copilot to design, generate, and refactor code along with testing and debugging. I used the Inline, agent, and plan mode for different prompts. The most useful prompts I provided were the ones I provided specific code blocks along with the specific problem it had and what can be done to fix it. Our collaboration included looking through the generated code and finding the bugs and letting Copilot fix it. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

--- One time I did not accept Copilot's suggestion was when it suggested to mark all overdue tasks as complete. It should be auto complete because this is a care app and hiding missed actions would affect the wellbeing of the pet. I verfied with manual tests to ensure tasks stayed pending until marked complete.

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

--- I added tasks, removed tasks, and marked tasks as complete. I tested the schedule generator by generating schedules. I tested changing the owners information. All these test are important to main data integrity, ensure the integrity of recurrence, and user trust. These are really important for a care app.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

--- I am fairly confident that the scheduler works because I have tested the main functionality of the app. Core behaviors liek add, remove, complete, generate, filter, etc were tested. If I had more time I would test adding hundreds of tasks at once to see if the app still functions, I would duplicate the tasks for the same pet and see if the right task is being deleted, and I would test recurrence edge cases like month end behaviors. 

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

--- I am most satisfied with the structure of the project. Using the UML diagram really helped guide the code. I also liked how a basic planner turned insto a scheduler with algorithms that help with filtering, recurrence, sorting, etc.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

--- I would improve scheduling algorithm to effciently schedule using priority, pets involved, time, etc. I would redesign task to ahve a unique id so duplicate title may also be handled. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

--- I learned that AI is most effective when provided with context and prompts along with human in the loop process to verfiy information. And complex algorithms may not always be better because other considerations such as readability, time complexity, optimality should also be considered.
