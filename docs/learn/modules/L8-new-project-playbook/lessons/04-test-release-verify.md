# Test, release and prove it live

**Objective:** pass gate G5 before a merge, deploy in the order that keeps the old and the new shape working, and
close an issue only at gate G6, when the change is verified on the live environment.

Merged and green is not done. The test phase proves the change before users see it; the release phase moves it to
the live environment in a safe order and proves it there. Who may merge depends on the phase of the whole project,
not on the size of the change.

Read the four sections shown with this lesson:

1. Test: the gate G5 questions (release ready).
2. Release: the deploy order, the job gate and the rollback rule.
3. Release: gate G6, the Definition of Done verified live.
4. Release: merge rights in the dev phase and from the first prod or first paying tenant.

## Check yourself

- Every required check is green but one optional check is red. Does the change pass G5?
- Why does the expand migration go out before the code, and the contract migration only after every reader moved?
- The pull request merged an hour ago. What evidence must exist before the issue is closed?
