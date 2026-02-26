---
name: shell-style
description: >
  Enforce Google Shell Style Guide conventions when writing, reviewing, or modifying
  shell scripts. Use when working with .sh files, bash scripts, files with #!/usr/bin/env bash
  shebang, or any shell scripting task including creating new scripts, editing existing
  ones, reviewing shell code, or fixing shell-related bugs.
---

# Shell Style Guide

Apply Google Shell Style Guide rules to all shell code in this project.
For detailed code examples, see [references/examples.md](references/examples.md).

## Background

- Use Bash exclusively (`#!/usr/bin/env bash`). No POSIX-only sh, zsh, fish, etc.
- Use `set` for shell options (not flags on the shebang line) so `bash script_name` works.
- Shell is for small utilities and simple wrappers only. Rewrite in a structured language if:
  - Script exceeds ~100 lines
  - Non-straightforward control flow is needed
  - Performance matters

## Strict Mode

Every script must enable strict mode immediately after the shebang and file header comment:

```shell
#!/usr/bin/env bash
#
# Brief description.

set -euo pipefail
```

- `set -e` — exit on any command failure (non-zero exit status)
- `set -u` — exit on undefined variable references (catches typos)
- `set -o pipefail` — pipeline fails if any command in it fails, not just the last

### Strict mode pitfalls and workarounds

**Arithmetic evaluating to zero** — `(( i++ ))` when `i=0` returns exit code 1, triggering `set -e`:

```shell
(( i++ )) || true       # suppress the exit
# or use prefix increment:
(( ++i ))
```

**Commands expected to fail** — use `|| true` or capture the code:

```shell
count=$(grep -c pattern file || true)

# or when you need the return code:
set +e
result=$(some_command)
rc=$?
set -e
```

**`local` swallows exit codes** — always separate declaration from assignment (already required by this guide):

```shell
local my_var
my_var="$(failing_command)"  # set -e catches this
```

**Short-circuit as last line** — `[[ cond ]] && cmd` as the final line exits non-zero if cond is false. Use full `if/then/fi` instead:

```shell
# BAD — script exits 1 if file doesn't exist
[[ -f "$file" ]] && echo "found"

# GOOD
if [[ -f "$file" ]]; then
  echo "found"
fi
```

**Undefined positional params** — use default values with `${1:-}`:

```shell
name=${1:-}
if [[ -z "${name}" ]]; then
  echo "usage: $0 NAME" >&2
  exit 1
fi
```

**Sourcing non-conforming files** — temporarily disable `set -u`:

```shell
set +u
source /path/to/third_party.env
set -u
```

**Cleanup on exit** — use `trap` to ensure resources are released even on error:

```shell
cleanup() {
  rm -rf "${scratch_dir}"
}
trap cleanup EXIT
```

**SIGPIPE with `pipefail`** — `cmd | head -n1` may fail if `cmd` outputs more than the pipe buffer. Accept this or handle it explicitly.

## File Conventions

- Executables: `.sh` extension (if build rule renames) or no extension (if on `PATH`)
- Libraries: always `.sh` extension, must not be executable
- SUID/SGID is forbidden. Use `sudo` for elevated access.

## Error Handling

- All error messages to STDERR. Use an `err()` helper function.
- Always check return values. Use `if ! command` or check `$?`.
- Use `PIPESTATUS` for pipe error checking. Capture it immediately — any subsequent command overwrites it.

## Comments

### File header (required)

```shell
#!/usr/bin/env bash
#
# Brief description of what this script does.

set -euo pipefail
```

### Function header (required unless function is both obvious and short)

```shell
#######################################
# Brief description.
# Globals:
#   VAR_NAME
# Arguments:
#   $1 - description
# Outputs:
#   Writes to STDOUT/STDERR
# Returns:
#   0 on success, non-zero on error.
#######################################
```

### TODO format

```shell
# TODO(username): Description of what needs doing (bug ####)
```

## Formatting

- **Indentation**: 2 spaces. No tabs. Exception: `<<-` heredoc body uses tabs.
- **Line length**: 80 characters max. Use heredocs or embedded newlines for long strings.
- **Pipelines**: One line if short. Otherwise split with `\` and `|` on the next line, indented 2 spaces.
- **Control flow**: `; then` / `; do` on same line as `if` / `for` / `while`. `else`, `fi`, `done` on own lines.
- **Case statements**: Indent alternatives 2 spaces. One-line alternatives: `pattern) action ;;`. Multi-line: pattern, actions, `;;` on separate lines.
- **Variable expansion**: Prefer `"${var}"` over `"$var"`. Do not brace-delimit single-character specials (`$1`, `$?`, `$@`) unless necessary.
- **Quoting**: Always quote strings with variables, command substitutions, spaces, or metacharacters. Use arrays for argument lists. Use `"$@"` not `$*`.

## Features and Bugs

- **ShellCheck**: Run `shellcheck` on all scripts. Install via `brew install shellcheck`.
- **Command substitution**: `$(command)` not backticks.
- **Tests**: `[[ ... ]]` not `[ ... ]` or `test`.
- **String testing**: Use `-z` / `-n` explicitly. Use `==` for equality (not `=`). Use `(( ))` or `-lt`/`-gt` for numeric comparison — never `<`/`>` inside `[[ ]]` for numbers.
- **Wildcard expansion**: Use `./*` not `*` to avoid filenames starting with `-`.
- **Eval**: Forbidden.
- **Arrays**: Use arrays for lists of elements, especially command-line flags. Expand with `"${array[@]}"`.
- **Pipes to while**: Use process substitution (`< <(command)`) or `readarray` instead of piping to `while`. Pipe creates a subshell — variable changes won't propagate.
- **Arithmetic**: Use `(( ))` or `$(( ))`. Never `let`, `$[ ]`, or `expr`. Inside `$(( ))`, omit `${}`  on variable names.
- **Aliases**: Forbidden in scripts. Use functions instead.

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | `lower_snake_case` | `my_func()` |
| Package functions | `package::func` | `mylib::parse()` |
| Variables | `lower_snake_case` | `my_var` |
| Loop variables | Named for the iterated collection | `for zone in "${zones[@]}"` |
| Constants / exports | `UPPER_SNAKE_CASE`, declared at top of file | `readonly PATH_TO_FILES='/some/path'` |
| Source filenames | `lowercase` or `lower_snake_case` | `make_template` not `make-template` |

### Local variables

- Declare function-local variables with `local`.
- **Separate declaration from command-substitution assignment** — `local` swallows exit codes:

```shell
local my_var
my_var="$(my_func)"
(( $? == 0 )) || return
```

### Function and code structure

- All functions together near the top, below constants. No executable code between functions.
- Use a `main` function for scripts with at least one other function. Last line: `main "$@"`.
- Use `readonly` or `export` over equivalent `declare` commands for clarity.

## Calling Commands

- Prefer shell builtins over external commands: parameter expansion over `sed`, `(( ))` over `expr`, `[[ =~ ]]` over `grep` for simple matches.

## Validation Checklist

Before finalizing any shell script:

1. Run `shellcheck <script>` and resolve all warnings
2. Verify `#!/usr/bin/env bash` shebang followed by `set -euo pipefail`
3. Confirm all functions have header comments (Globals/Arguments/Outputs/Returns)
4. Check quoting — all variables in double quotes, arrays expanded with `"${arr[@]}"`
5. Verify error messages go to STDERR
6. Confirm no bare `(( i++ ))` without `|| true`, no short-circuit `&&` as last line
7. Verify `local` declarations are separate from command-substitution assignments
