# Video 10: Why DS/ML fundamentals are what get you the AI job

*Shooting script, as of 14 Oct 2026.*

**Length:** 7-7.5 min ·

**Goal:** reframe the foundation as what makes you hireable, not as a hurdle

## 0:00 Hook (25 sec)

SAY: "The objection we hear most: 'I want to learn agents. Not data science.'"

SAY: "I get it. Agents are the exciting part."

SAY: "But I'm going to argue something that sounds backwards. The part you're trying to skip is the part that gets you hired."

SAY: "Let me back that up."

## 0:25 Who actually gets paid (100 sec)

SAY: "Look at who gets paid to build AI systems that run in production."

SAY: "It's not the person with the cleverest prompt. Almost everyone is learning to prompt."

SAY: "Prompting is a useful skill. But when everyone has it, it stops being the thing that gets you hired."

SAY: "It's the person who can answer three questions. Is this system actually any good? How do I measure that? And why did it fail?"

SAY: "That's evaluation, measurement and debugging. They come from understanding data and how models behave. That's what 'DS and ML fundamentals' really means. Not becoming a statistician. Becoming the person who knows when the AI is wrong."

SAY: "And with agents, this matters even more. There's a book called *AI Engineering*, by Chip Huyen, published by O'Reilly. It gives a simple example. Say your agent gets each step right ninety-five times out of a hundred. Sounds good. But a real task has ten steps. Now the whole task comes out right only about six times out of ten. With a hundred steps, it's right less than once in a hundred tries."

SAY: "Every step is one more chance to go wrong. So if you want to build agents, testing them isn't a side job. It is the job."

## 2:05 The demo: 95% accurate and still broken (150 sec)

SAY: "Let me show you what happens to someone who only learned to build the agent."

**Setup:** the demo is in `video10-eval-breakdown/`. An agent sorts Northwind Cloud's finance inbox (invoices, refund requests, billing questions, renewals) and routes each message. Run `python demo.py warm` the day before, so the numbers on screen match this script.

**Beat 1.** Run `python demo.py beat1`: 5 hand-picked messages, 5 out of 5 correct.

SAY: "Five out of five. Looks great. Ship it, right?"

**Beat 2.** Run `python demo.py beat2`: all 80 messages. Overall accuracy still looks high: 93.8% (75 of 80).

SAY: "Bigger test. Still about ninety-four percent. Still looks great."

**Beat 3.** Run `python demo.py beat3`: accuracy per message type, worst first. Payment disputes, the chargebacks from the bank, are 0 out of 5. Every other type is 100%.

SAY: "Now watch. Split it by type. This category? It fails every single time. The overall number hid it, because it's rare."

SAY: "And in real life, the rare case is often the expensive one. The fraud. The legal clause. The VIP customer."

SAY: "A fraud model that's right ninety-nine percent of the time can still miss most of the fraud. If fraud is rare, the average barely notices."

**Beat 4.** Run `python demo.py beat4`. All five chargebacks were filed somewhere else: three as support questions, one as a refund request, one as an invoice. The cause: the label list was built from five easy examples, so it had no place for a chargeback. v2 adds a payment_dispute label, and the re-run is 100%.

SAY: "The agent-only builder ships after step one and thinks they're done. The person with data and ML understanding catches step three. Because they know one average can hide a disaster."

SAY: "And notice what the fix took. Not a cleverer prompt first. First, splitting the results, reading the failures, and finding the pattern. That's error analysis. It's a data skill, and it's the fastest way to make any AI system better."

SAY: "That's the difference in production."

SAY: "So how much of this do you actually need to learn?"

## 4:35 How much DS/ML, honestly (85 sec)

SAY: "Now let me be clear about how much. I'm not asking you to do a data science degree."

SAY: "The same book says you no longer must know ML to build AI apps. That's fair. You don't need to train a model from scratch to build an agent. But she also says ML knowledge is still extremely valuable. It helps you find the problem when a model doesn't work as expected. That is what this foundation is for."

SAY: "In this program, the foundation is two months. Data Foundations, one month: working with real, messy data, and basic probability. Mathematical Foundations of AI, one month: how a model learns, and why it gets things wrong."

SAY: "Why that much and no more? Because that's exactly what you need to test and debug the systems you'll build. If you wanted to become a research scientist, you'd need far more. And we'd tell you."

SAY: "And here's the good part. Those skills don't expire. Models change every few months. The ability to measure a system and find out why it's wrong works on every one of them."

## 6:00 The reframe (65 sec)

SAY: "So think of it differently. This isn't a box to tick before the fun part."

SAY: "Picture two people. Both can build an agent. One uses AI. The other gets paid to build it. The difference? The second one can prove it works, and fix it when it doesn't."

SAY: "In an interview, that difference shows up in one question. 'How do you know your system works?' One candidate talks about the demo. The other talks about the test set, the breakdown, and the failure they found and fixed. You want to be the second candidate."

SAY: "So when you see the data and ML part of the program, don't see a detour. See the part that turns you from someone who can build an agent into someone who gets trusted with one."

## 7:05 Close (15 sec)

SAY: "Not sure how much of this you need for the role you want? Ask us. We'll tell you plainly. Link below."

## Ad cut (45 sec)

**"95% and still broken":** Beats 1 to 3 of the demo, then the line after Beat 4 (cut Beat 4's terminal output). Open on "Five out of five. Looks great." End on "one average can hide a disaster."

**Before shoot:** run `python demo.py warm`, then `beat2` and `beat4`, and check both match the lines above. Keep the existing `.cache/` folder and copy it to the shoot machine: a fresh re-warm can change Beat 4's split.
