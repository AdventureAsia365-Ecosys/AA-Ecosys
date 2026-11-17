# Decide to build, then design the boundaries

**Objective:** run gate G1 (go or no-go) at the end of discovery and gate G2 (design accepted) at the end of
architecture, and avoid the mistakes both phase pages list.

Discovery exists to decide whether to build at all; stopping there is a valid result, not a failure. Architecture
then fixes the boundaries that are expensive to reverse (who writes which data, how apps read each other, how secure
each area must be) before any feature code exists. Both gates are short lists rated red, amber or green.

Read the four sections shown with this lesson:

1. Discovery: the gate G1 questions, then its common mistakes.
2. Architecture: the gate G2 questions, then its common mistakes.

## Check yourself

- A sponsor says "we need a CRM". Which G1 question does that statement fail, and how do you restate it?
- Why is the monthly running cost of the Dev skeleton asked for at G1, before any design exists?
- Two services need to update the same table. Which G2 question does that break, and what is the usual fix?
