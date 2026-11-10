#!/bin/sh
# AI Workforce send lock (launcher). Claude runs this before a connected-app tool is used.
# It hands the hook input to send_lock.py, next to this file, which decides.
#   exit 2 = refuse the tool call (the reason goes to Claude on standard error)
#   exit 0 = let it through
# If Python isn't available, or anything goes wrong, the call goes through:
# the lock can't run there, and the team's written rules still apply.
dir=$(dirname "$0")
input=$(cat)
for py in python3 python; do
  command -v "$py" >/dev/null 2>&1 || continue
  reason=$(printf '%s' "$input" | "$py" "$dir/send_lock.py" 2>&1 >/dev/null)
  code=$?
  if [ "$code" -eq 2 ]; then
    printf '%s\n' "$reason" >&2
    exit 2
  fi
  [ "$code" -eq 0 ] && exit 0
done
exit 0
