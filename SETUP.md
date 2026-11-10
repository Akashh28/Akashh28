# Animated GitHub profile cards

Copy these files into the root of the Akashh28/Akashh28 repository, preserving the folder structure.

1. Create a GitHub token with the read:user scope.
2. In the profile repository, open Settings → Secrets and variables → Actions.
3. Add a repository secret named PROFILE_STATS_TOKEN and paste the token.
4. Commit the files, then run Actions → Refresh animated profile cards → Run workflow.

The workflow runs daily at 02:17 UTC, fetches contribution data through GitHub GraphQL, renders the SVG cards and commits changed files.

## Local static screenshot mode

Install Python 3.10+ and run:

    python -m pip install fonttools
    STATIC=1 python scripts/render_profile_cards.py

The output is in cards/. Static mode produces final-frame SVGs without animation. Normal mode uses CSS keyframes and SMIL; prefers-reduced-motion disables both.

Optional portrait: set PROFILE_PORTRAIT_URL to a public image URL before running the script. If omitted, the hero uses an AK monogram.
