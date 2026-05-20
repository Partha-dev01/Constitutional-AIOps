"""Strip all Claude references from commit messages.

Lines removed (any case variant of 'Claude' or 'CLAUDE'):
  - Co-Authored-By: Claude ...
  - Generated with [Claude Code] ...
  - any bullet/line that mentions CLAUDE.md, Claude Code, etc.

Trailing blank lines are trimmed. Otherwise messages are byte-preserved.
"""
import git_filter_repo as fr


def clean_message(commit, metadata):
    msg = commit.message.decode("utf-8", errors="replace")
    out = []
    for line in msg.split("\n"):
        if "claude" in line.lower():
            continue
        out.append(line)
    while out and not out[-1].strip():
        out.pop()
    commit.message = ("\n".join(out) + "\n").encode("utf-8")


args = fr.FilteringOptions.parse_args(["--force"])
filter_obj = fr.RepoFilter(args, commit_callback=clean_message)
filter_obj.run()
