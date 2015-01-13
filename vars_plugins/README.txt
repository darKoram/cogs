README.txt

The easiest way to understand deploy_vars.py is to diff it with group_vars.py in the ansible distro.  You should see 
very minor changes.

This allows hierarchical folder match as you collect group vars rather than first-folder-match-only that ansible ships with.