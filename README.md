# AI Workforce for Claude

**You run the business. Your team handles the work.**

A ready-made AI team: a Chief of Staff and five team members (Operations, Marketing, Sales, Client Success, Finance). They learn your business, take work off your plate, and ask before anything leaves your hands. Everything they know lives in your own Notion.

**What you need**
- **Required:** a paid Claude plan that includes plugins and scheduled tasks, and a Notion account. Notion's free plan works: the team reads your workspace through saved views, which keep working when the free plan's query allowance runs out (existing workspaces: say "update my team workspace" once to add them).
- **Optional:** email, calendar and files (Gmail and Google, or Outlook and Microsoft 365). Without them the team works from what you paste in.
- **Usage:** how much of your Claude plan the team uses depends on how many recurring tasks you turn on. We haven't measured yet whether the Pro plan covers daily use, so start with one recurring task (the daily briefing, which also checks your inbox) and add more once you've seen the usage.

## Install

**Option A (recommended):** in the Claude desktop app, open **Customize** in the left sidebar (in Cowork, open the Cowork tab first) and go to the **Plugins** tab. Under **Personal plugins**, click **+** → **Add marketplace** → **Add from a repository**, and enter `https://github.com/ai-workforce-installer/ai-workforce`. Then click **Browse plugins** and **Install** next to **AI Workforce**. (Claude's menus change from time to time; if yours look different, see Anthropic's guide, [Use plugins in Claude](https://support.claude.com/en/articles/13837440).)

**Option B (file):** download [ai-workforce.plugin](https://github.com/ai-workforce-installer/ai-workforce/raw/main/download/ai-workforce.plugin), then in **Customize → Plugins** use the option to upload a plugin file. A file install doesn't update itself: upload the new file for each release.

Claude Code: `/plugin install ai-workforce --marketplace ai-workforce-installer/ai-workforce`

## Then

1. Optional: connect Notion and your email and calendar apps now. If you skip this, setup asks what you use and walks you through connecting each one, waiting until it works. Only Notion is required.
2. Start a **new** chat and send: `Set up my AI team. My website is [your website].`

In one sitting, your Chief of Staff connects your apps, learns your business from your website, and has the team do its first real job with you. After that, just talk to your team: "Clear my desk" (everything waiting on you, one card at a time), "Have Marketing work on this", "What's my team been working on?", "Can someone handle this every Friday?"

AI Workforce is in beta. Your recurring tasks always follow the version of AI Workforce you have installed, so after you update the plugin they work the new way on their next run; the tasks themselves never change. When your team runs on its own, a built-in lock refuses the tools that send, delete, share or book (still being proven live in scheduled runs). A reply is sent for you only if you switch that on, and then only on your yes to that reply in a chat you are in. For what's enforced, what's been tested live and what hasn't yet, see [What you can rely on](plugins/ai-workforce/README.md#what-you-can-rely-on-and-how-we-know).

Full details: [plugins/ai-workforce/README.md](plugins/ai-workforce/README.md)
