# LinkedIn Post: Forrester Agentic AI Response
**Posted:** 2026-08-11
**Channel:** #linkedin-posts (1518731579067728003)
**Category:** digital_transformation
**Word count:** 459
**Source article:** https://www.forrester.com/blogs/the-state-of-agentic-ai-in-2026-companies-are-chasing-few-are-catching/
**Message IDs:** 1536942598294339624, 1536942603604328519

---

Forrester just published a piece titled "The State Of Agentic AI In 2026: Companies Are Chasing, Few Are Catching." Brian Hopkins and his team report that three-quarters of enterprise leaders say they're adopting agentic AI, but only a small minority have it running in meaningful production beyond "agentish" chatbots. Their framing is sharp: the technology is a runaway train, and the enterprise is the heavy load it has to pull.

I'd say they're right about the gap, but for Salesforce teams specifically, there's a layer underneath what Forrester describes that doesn't get enough attention. Forrester says to invest in orchestration before adding agents, redesign the work, and treat every agent as a governed identity. All true. But in the Salesforce world, the heaviest load isn't orchestration or identity. It's the data. Agentforce agents run on your CRM data, and if that data has the 30 to 40% quality issues that multiple implementation guides cite as typical for mature orgs, no amount of orchestration fixes the output.

Here's what happens. You follow Forrester's advice. You invest in orchestration. You redesign a high-friction workflow around autonomy. You give your agent a governed identity with least privilege and full logging. Then the agent reads your case history, finds 12,000 overlapping records (realistic for an org running 8+ years without a cleanup pass), and can't tell that Case A and Case B are the same customer. It serves a redundant resolution. The customer gets frustrated. The agent looks dumb. Your team loses trust. The orchestration was perfect. The identity was governed. BUT the data was garbage.

Forrester says "agents bolted onto human-paced legacy workflows produce task savings, not step-change value." I'd take that further: agents bolted onto dirty data produce negative value, because they amplify bad information at machine speed. The 67% implementation failure rate that Codleo reported in July isn't about agent capability or orchestration gaps. It's about teams deploying agents on foundations they haven't assessed.

With Dreamforce 2026 coming September 15-17, we'll hear about new agent types, cross-cloud capabilities, marketplace expansion. But the one thing I hope Salesforce addresses: make data readiness a first-class platform feature, not a consulting exercise. When you go to deploy an agent, the platform should scan your foundation and say, "here are the 3 data clusters, the 2 missing-field patterns, and the 1 stale-data zone this agent would run into." A readiness check scoped to the specific agent, not a general dashboard.

Forrester is right that the companies pulling ahead are laying the track, not just adding agents. BUT the track starts with data. If you're sitting on Agentforce licenses and not sure where to start, reach out. We help teams assess readiness, clean the foundation, and deploy on data they can trust. We're real friendly.
