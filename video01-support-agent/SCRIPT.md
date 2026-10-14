# Video 1: Watch me build an AI agent in 15 minutes

*Shooting script, as of 14 Oct 2026.*

**Length:** 13-15 min · **Goal:** prove the program is hands-on, not theory

**The build:** a support-ticket agent for a fictional company, Northwind Cloud. It reads each ticket, summarises it, sets urgency to high, medium or low, checks the company policy, alerts Slack when it's urgent, and drafts a reply. The full project is in `video01-support-agent/`, and every command below comes from its README.

**Prep:** project open in the editor, `.env` filled in, Slack test channel visible, and the finished `agent.py` running in a second terminal as a safety net. Do a full dry run the day before.

## 0:00 Hook (30 sec)

SAY: "Someone asked us this last week. Will you actually build AI agents, or is it just theory?"

SAY: "So I'm not going to answer with slides. I'm going to build one. Right now. From an empty folder. Fifteen minutes. If I get stuck, you'll see that too."

SAY: "First, let me show you the problem we're solving."

## 0:30 The problem (1 min)

SAY: "Every company has this problem. Hundreds of support tickets a day. Somebody reads each one, decides how serious it is, checks the policy, and works out what to do next."

SAY: "That's slow. It's repetitive. And it's exactly the kind of job an agent is built for."

SAY: "Quick definition, because the word gets thrown around a lot. A chatbot answers questions. An agent decides what to do next, and uses tools to actually do it."

SAY: "Five steps. Give it a brain. Give it tools. Connect it to our data. Test it properly. Deploy it. Let's go."

## 1:30 Step 1: the brain (2 min)

SAY: "First, the brain. That's a large language model, and I'm calling it through an API. I tell it its job in one plain sentence: you triage support tickets."

SAY: "Now here's the first thing that separates a demo from a real system. I'm not asking for a nice paragraph. I'm asking for structured output. A summary, an urgency, and a recommended action, in fixed fields."

SAY: "Why does that matter? Because in a real company, the next thing to read this answer isn't a person. It's another piece of software."

SAY: "One ticket in. Clean, structured answer out. That's the brain."

SAY: "But a brain that can only talk isn't an agent yet. It needs to act."

## 3:30 Step 2: tools (2.5 min)

SAY: "A model on its own can only talk. Tools are what let it act. I'm giving it three."

SAY: "`lookup_policy`, to check the rules. `post_to_slack`, to alert the team. And `save_draft_reply`, to write back to the customer."

SAY: "Look at these descriptions. They aren't comments for humans. The model reads them to decide when to use each tool. Write a vague description and you get wrong decisions. That's one of the first things you end up debugging on a real project."

SAY: "Watch it work. It reads the ticket. It decides it needs the policy. It looks it up. Then it decides what to do. Nobody wrote an if-statement for that. The model chose."

SAY: "There's just one catch. It's choosing based on what it knows. And it doesn't know our company yet."

## 6:00 Step 3: our data (2 min 15 sec)

SAY: "Problem. This model has never seen Northwind's refund policy. It doesn't know our rules, so it would just guess. And a confident guess is worse than no answer."

SAY: "And this has really happened. In 2024, Air Canada's chatbot gave a customer the wrong refund rules. A tribunal made the airline pay, because the chatbot is part of the airline's website. So the airline is responsible for what it says."

SAY: "So I'll load the policy, cut it into small pieces, and make it searchable. When a ticket comes in, the agent finds the right piece first, then answers."

SAY: "This pattern is called RAG, retrieval-augmented generation. Think of a new hire who checks the handbook before replying to a customer. Same idea."

SAY: "I ask about a locked account. Back comes the exact paragraph on lockouts. That's the agent reading our rules, not making them up."

SAY: "So it reads our rules. But does it make the right call? There's only one way to know."

## 8:15 Step 4: test it, find the failure (2.5 min)

SAY: "Now the part most demos skip. Let's see where it's wrong."

SAY: "Twenty tickets. Expected answer versus the agent's answer. Twelve right. Eight wrong."

SAY: "Read this one. 'Quick question when you have a moment.' But their backups have failed three nights in a row, and they have an audit tomorrow at nine. The agent marked it medium. Because it was polite."

SAY: "That's a real failure. In real life, that's a failed audit and a very angry client."

SAY: "And it fails the other way too. A furious customer with a blurry logo? Marked high. The agent is reading the mood, not the problem."

SAY: "One rule fixes it. Judge urgency by business impact and deadlines, not by tone. Now re-run."

SAY: "Fixed. Nineteen out of twenty, up from twelve. And notice how I found it. Not by trying one example and saying 'looks good'. By testing on a set and measuring. That's evaluation, and it's what makes a system you can trust. In the program, this is a core skill, not a footnote."

SAY: "A tested agent is great. But right now, it only lives on my laptop."

## 10:45 Step 5: deploy (2 min)

SAY: "An agent on my laptop helps nobody. Let's put it online so any system can call it."

SAY: "I wrap it in a small web service. One address. Send it a ticket, get back the decision."

SAY: "It's live. A real link, on the internet."

SAY: "Now let's prove the whole thing works, end to end."

## 12:45 The whole loop (1 min)

SAY: "Let's send it a fresh ticket it has never seen."

SAY: "Ticket in. The agent understands it. Checks the policy. Alerts the team on Slack. Drafts the reply. Running on a live link."

SAY: "Empty folder to a working, tested, deployed agent."

SAY: "So what does that mean for you?"

## 13:45 Close (1 min)

SAY: "And here's the thing. This is one project. In the program you build several. An AI study companion for Scaler learners. And a video classifier that spots adult content, the kind of check every video platform needs, taken all the way to a live system."

SAY: "You don't watch them. You build them, you test them, you deploy them. Just like you saw today."

SAY: "If you want to see how the full program is put together, the link is below."

## Ad cuts (30-45 sec each)

- **Cut A, "Not theory":** the hook question, then a jump to the finished loop at 12:45.
- **Cut B, "The polite ticket":** the T-12 failure and the one-line fix. Open on "The agent marked it medium. Because it was polite."
- **Cut C, "It's live":** the deploy and the Slack alert firing.

**Fill before shoot:** the project grid.
