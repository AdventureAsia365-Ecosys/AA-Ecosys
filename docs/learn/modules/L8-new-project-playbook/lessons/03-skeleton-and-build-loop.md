# The walking skeleton and the build loop

**Objective:** prove a walking skeleton at gate G3, then move each issue through the Definition of Ready, the right
path and the flow rules.

A walking skeleton is an empty product that already builds, deploys and reports which commit runs, with every guard
switched on from the first commit. Only then does feature work start, as one ordered queue of small, ready issues.
The path of an issue sets how much process it gets, so a small fix does not pay for a feature's ceremony.

Read the four sections shown with this lesson:

1. Setup: the gate G3 questions for the walking skeleton.
2. Build: gate G4, the Definition of Ready checked for every issue.
3. Build: the four paths and the review each one needs.
4. Build: the flow rules (work-in-progress limit, circuit breaker, frozen Done-when, one deliverable per issue).

## Check yourself

- `/health` answers 200 on Dev. Which G3 question is still open if it does not name the commit it runs?
- An issue changes a migration and nothing else a user sees. Which path is it, and what review does it need?
- Halfway through, an issue runs past its appetite. What does the circuit breaker tell you to do?
