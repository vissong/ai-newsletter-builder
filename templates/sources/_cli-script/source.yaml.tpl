name: {{name}}
type: script
enabled: true
language: {{language}}
priority: 2
time_window_hours: 24
recent_hours: 24
timeout_seconds: 30

script: fetch.sh
runtime: bash

check:
  binary: {{binary}}
  install_hint: "{{install_hint}}"

args: {}
