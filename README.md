# AI Workforce for Claude

**You run the business. Your team handles the work.**

A ready-made AI team: a Chief of Staff and five team members (Operations, Marketing, Sales, Client Success, Finance). They learn your business, take work off your plate, and ask before anything leaves your hands. Everything they know lives in your own Notion.

**What you need**
- **Required:** a paid Claude plan that includes plugins and scheduled tasks, and a Notion account. Notion's free plan works: the team reads your workspace through saved views, which keep working when the free plan's query allowance runs out (existing workspaces: say "update my team workspace" once to add them).
- **Optional:** email, calendar and files (Gmail and Google, or Outlook and Microsoft 365). Without them the team works from what you paste in.
- **Usage:** how much of your Claude plan the team uses depends on how many recurring tasks you turn on. We haven't measured yet whether the Pro plan covers daily use, so start with one recurring task (the daily briefing) and add more once you've seen the usage.

## Install

**Option A (recommended, gets updates):** in Claude, open **Customize → Plugins → Add → Add marketplace**, paste `https://github.com/reedfloren/ai-workforce`, then install **AI Workforce**. Turn on **Sync automatically**.

**Option B (file):** download [ai-workforce.plugin](https://github.com/reedfloren/ai-workforce/raw/main/download/ai-workforce.plugin), then in Claude open **Customize → Plugins**, choose the upload option and select the file.

Claude Code: `/plugin install ai-workforce --marketplace reedfloren/ai-workforce`

## Then

1. Optional: connect Notion and your email and calendar apps now. If you skip this, setup asks what you use and walks you through connecting each one, waiting until it works. Only Notion is required.
2. Start a **new** chat and send: `Set up my AI team. My website is [your website].`

In one sitting, your Chief of Staff connects your apps, learns your business from your website, and has the team do its first real job with you. After that, just talk to your team: "Have Marketing work on this", "What's waiting for my approval?", "What's my team been working on?", "Can someone handle this every Friday?"

Full details: [plugins/ai-workforce/README.md](plugins/ai-workforce/README.md)
