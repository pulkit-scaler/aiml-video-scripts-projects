# Video 8: Masterclass Part 2, the deep dive and the role it leads to

*Shooting script, as of 14 Oct 2026.*

**Length:** 25-35 min (20-30 min deep dive, about 5 min role segment) ·

**Goal:** turn masterclass curiosity into a career decision

**Topic:** RAG, following the masterclass "Build your first RAG system". The demo is in `video08-rag-deep-dive/`. Run `python demo.py warm` the day before, so every beat replays instantly on camera.

## 0:00 Hook (2 min)

SAY: "A lot of you told us the same thing after the masterclass. 'Great overview. Now we want to go deeper.'"

SAY: "So this is part two. No overview. We go deep."

SAY: "We take the topic from the masterclass, RAG, and build it properly, with a real demo. Then I'll show you where it fits in the full path. I'll answer your top questions. And I'll finish with the part that matters most: what job this actually leads to."

## 2:00 Recap in 90 seconds (1.5 min)

SAY: "Quick recap, in case it's been a couple of days."

SAY: "RAG stands for retrieval-augmented generation. First, the system finds the right pieces of your documents. Then the language model writes the answer from those pieces, instead of guessing."

SAY: "To find the right pieces, we cut the documents into small chunks. Each chunk becomes an embedding: a list of numbers that captures its meaning. Harry Potter sits close to magic. James Bond sits close to spy. The chunks go into a vector database."

SAY: "When a question comes in, we look for the chunks closest in meaning, not just the ones with the same words. Remember the apple example? 'Health benefits of eating apples' should find 'an apple a day keeps the doctor away', not the iPhone. That's how we built the virtual insurance agent that answers from its study guides."

SAY: "Got that? Good. That's the version everyone shows. At the end of the masterclass, we said what comes next: better chunking and better ranking. That's today. Now let's see why the simple version breaks."

## 3:30 The deep dive, live (15-20 min)

SAY: "In the masterclass, you saw this at thirty thousand feet. Now we land."

**Beat 1: the basic version, and where it breaks.** Run `python demo.py beat1`. It asks Northwind Cloud's help-centre documents: "How long does a customer on an annual plan have to request a refund?" The answer says 7 days, the rule for monthly plans. The real answer is 30 days.

SAY: "Sounds confident, doesn't it? It's wrong. This is what most first attempts look like. And most teams ship this."

**Beat 2: fix problem one.** Run `python demo.py beat2`. Documents are now split one section per chunk, instead of every 50 words. Same question, and the answer is 30 days.

SAY: "The answer was in the document all along. The system just cut the page in the wrong place. Watch what happens when I fix that."

**Beat 3: fix problem two.** Run `python demo.py beat3`. "What uptime does the Enterprise plan guarantee?" Keyword search finds the Team plan's paragraph (99.5%), and the answer comes out wrong. Hybrid search, keywords plus meaning, also finds the Enterprise SLA, and the answer is right: 99.95%.

SAY: "Better. Now it finds the right paragraph, not just a similar-sounding one."

**Beat 4: measure it.** Run `python demo.py beat4`. 14 test questions with known answers. For each version, the table shows how often the right passage was found, how often the answer was correct, and how often it made something up. Overall: 57%, then 71%, then 79%, then 93%.

SAY: "And this is the step that separates a demo from something you'd trust in front of a client. We don't say 'looks better'. We measure it."

SAY: "Fifty-seven percent at the start. Ninety-three percent at the end. Now we know it's better, and by how much."

**Beat 5: one production problem.** Run `python demo.py beat5`. "Do you offer an on-premise version?" The documents don't say. Without the guard, it makes something up: "No, we don't provide an on-premise version." With the guard, it says it doesn't know based on our documents.

SAY: "Last one. What happens when someone asks something the documents don't cover? A good system says 'I don't know.' A bad one makes something up. Here's how you make it say 'I don't know.'"

SAY: "So that's one topic, built properly. Now let's zoom out."

**At every beat, say three things in plain words:** what you're doing, why, and what an experienced engineer or manager should take away.

## 20:00 Where this fits in the full path (2-3 min)

SAY: "Here's where what you just saw sits."

SAY: "RAG sits in the AI Engineering module, in part one, next to writing good prompts and protecting the AI from misuse. Before it, you'd cover data and Python basics, the maths of how models learn, machine learning up to transformers, and MLOps. After it, you move on to agents with LangChain and LangGraph. Then memory, Agentic RAG and GraphRAG. Then fine-tuning, running AI in production, and security."

SAY: "One chapter. In a sequence where every step builds on the one before. That's the difference between a masterclass and a path."

SAY: "Before we talk about where this leads, let's get to your questions."

## 23:00 Your questions (4-6 min)

SAY: "You sent in a lot of questions. Here are the four we got most."

Use real ones. Suggested answers:

- **"Isn't this too basic for someone with fifteen years of experience?"**

  SAY: "You just watched it break three ways and get fixed. That's not basic. That's what production looks like."

  Point to Video 2.
- **"Do I need strong coding?"**

  SAY: "No, you don't need coding experience to join. If you're new to code, there's a beginner track first: two months of AI with no coding, then one month of Python from the basics. The main program does include coding. By the end, you'll have built working agents."

  Point to Video 6.
- **"Can't I learn this free online?"**

  SAY: "Pieces of it, yes. And some free material is excellent. What's hard alone is the order, getting your work reviewed, and actually finishing and shipping a project."

  Never knock free resources.
- **"What would I actually do with this at work?"**

  SAY: one concrete use case from the demo's domain. For RAG: "An assistant that answers your team's policy questions in seconds, with the source attached."

## 28:30 Where this leads: the role (about 5 min)

SAY: "Your questions all point at one bigger question. Where does this actually take me?"

SAY: "Now the most important five minutes."

SAY: "Everything you just saw is a skill. A skill on its own is a hobby. A skill attached to a role is a career move."

SAY: "This topic leads to roles like AI engineer and GenAI engineer. An AI engineer builds products on top of AI models: search systems, agents, APIs, and putting them live. A GenAI engineer works closer to the model: testing it, measuring quality, and making the answers better. And RAG is part of most real projects they work on."

SAY: "So where does that leave you? If you're a developer, your next step is the AI engineer path. If you're a manager, it's the AI solutions architect or AI project lead path. If you work in a business domain, it's the applied AI or AI product path. There's a short video for each one, linked below."

SAY: "Here's the real question. Not 'should I learn more AI?' It's 'which role do I want to be credible for, a year from now?' Answer that, and everything else follows."

## 33:30 The decision (1 min)

SAY: "So I'm not leaving you with more content. I'm leaving you with one decision."

SAY: "Pick your target role. Then book a role-mapping call."

SAY: "We'll look at your background and the role you picked, and give you an honest view of the path, and whether this program is the right way to get there. Link below."

**Sequence note for BDAs:** after Video 8, send Video 9 within 48 hours, then the Video 4 persona that matches the lead, then the role-mapping call CTA. One video per message, never more.

**Fill before shoot:** swap in 3-4 real attendee questions if you have them. Confirm the segment for the Consumed → TRO drop with analytics.
