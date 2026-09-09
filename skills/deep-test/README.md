# Deep-test skill — how to get this

This folder is a free, ready-to-use **Claude Code skill** for testing an
NL2SQL plugin against the real core. Here's exactly how to grab it.

## 1. Download it

You're looking at one folder inside a bigger repo, and GitHub can't zip up
just one folder on its own — so download the whole repo, then keep only
this part:

1. Go to the repo's main page: https://github.com/alex-tykhon-gh/nl2sql_documentation
2. Click the green **Code** button → **Download ZIP**
3. Extract the ZIP anywhere (e.g. your Desktop)
4. Inside it, find **`skills\deep-test\`** — that's this exact folder, with
   these 3 files: `README.md` (this one), `SKILL.md`, `deep_test_kit.py`

(Comfortable with git instead? `git clone https://github.com/alex-tykhon-gh/nl2sql_documentation.git` does the same thing.)

## 2. Save it into your own project

Copy that whole `deep-test` folder into a `skills` folder Claude Code
already looks in — pick one:

- **Just this project:** `<your project root>\.claude\skills\deep-test\`
- **Every project you open:** `%USERPROFILE%\.claude\skills\deep-test\`

(Create the `.claude\skills\` folder yourself if it doesn't exist yet.)

## 3. Use it

Open Claude Code in your own plugin's project (or restart it if it was
already open) and just ask it to test your plugin — e.g. *"deep-test my
plugin before I submit it."* Full detail on what it actually checks is in
`SKILL.md`, next to this file.
