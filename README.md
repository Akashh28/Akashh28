name: Metrics
on:
  schedule: [{cron: "0 0 * * *"}]
  workflow_dispatch:
  push: {branches: ["main", "master"]}

jobs:
  github-metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: lowlighter/metrics@latest
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

          user: Akashh28

          template: classic
          base: header, activity, community, repositories
          config_timezone: Asia/Kolkata

          plugin_isocalendar: yes

          plugin_languages: yes
          plugin_languages_details: yes

          plugin_achievements: yes

          plugin_habits: yes
          plugin_habits_from: 200
          plugin_habits_days: 14

          plugin_stars: yes

          plugin_followup: yes