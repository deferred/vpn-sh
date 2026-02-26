# Shell Style Guide — Code Examples

Detailed code examples for each section of the style guide. Load this file when
writing or reviewing shell code and need to see the correct patterns.

## Table of Contents

- [Strict Mode Workarounds](#strict-mode-workarounds)
- [Error Handling](#error-handling)
- [Function Comments](#function-comments)
- [Formatting](#formatting)
- [Quoting and Variable Expansion](#quoting-and-variable-expansion)
- [Tests and Conditionals](#tests-and-conditionals)
- [Arrays](#arrays)
- [Pipes to While](#pipes-to-while)
- [Arithmetic](#arithmetic)
- [Naming and Structure](#naming-and-structure)
- [Builtins over External Commands](#builtins-over-external-commands)

## Strict Mode Workarounds

```shell
#!/usr/bin/env bash
#
# Examples of handling set -euo pipefail edge cases.

set -euo pipefail

# --- Arithmetic evaluating to zero ---
# BAD — (( i++ )) exits when i=0 because result is 0 (falsy)
i=0
(( i++ ))  # EXIT: returns 1

# GOOD — suppress with || true
i=0
(( i++ )) || true
echo "${i}"  # 1

# GOOD — use prefix increment (result is 1, not 0)
i=0
(( ++i ))
echo "${i}"  # 1

# --- Commands expected to fail ---
# BAD — grep returns 1 when no match, set -e exits
count=$(grep -c pattern file)

# GOOD — suppress the exit
count=$(grep -c pattern file || true)

# GOOD — when you need the actual return code
set +e
output=$(some_command 2>&1)
rc=$?
set -e
if (( rc != 0 )); then
  err "some_command failed with code ${rc}: ${output}"
fi

# --- Undefined positional parameters (set -u) ---
# BAD — $1 with no args triggers "unbound variable"
name=$1

# GOOD — provide default value
name=${1:-}
if [[ -z "${name}" ]]; then
  echo "usage: $0 NAME" >&2
  exit 1
fi

# --- Optional variables with defaults ---
# BAD — unset variable triggers set -u
echo "${OPTIONAL_CONFIG}"

# GOOD — use default value syntax
echo "${OPTIONAL_CONFIG:-/etc/default.conf}"

# --- Short-circuit as last line ---
# BAD — exits with 1 if file doesn't exist (last line problem)
[[ -f "${config_file}" ]] && source "${config_file}"

# GOOD — use full if/then/fi
if [[ -f "${config_file}" ]]; then
  source "${config_file}"
fi

# --- Sourcing non-conforming files ---
set +u
source /path/to/venv/bin/activate
set -u

# --- Cleanup on exit (trap) ---
scratch_dir=$(mktemp -d -t tmp.XXXXXXXXXX)
cleanup() {
  rm -rf "${scratch_dir}"
}
trap cleanup EXIT
# Script can now write to ${scratch_dir} safely.
# cleanup runs on normal exit, error exit, or signal.

# --- Chaining three+ commands with && ---
# BAD — if second_task fails, third_task is skipped but script continues
first_task && second_task && third_task
next_task  # runs even if second_task failed

# GOOD — use a block so set -e applies inside it
first_task && {
  second_task
  third_task
}
next_task

# --- local swallowing exit codes ---
# BAD — local returns 0, masking the failure
my_func() {
  local var="$(failing_command)"  # set -e will NOT catch this
}

# GOOD — separate declaration from assignment
my_func() {
  local var
  var="$(failing_command)"  # set -e catches this
}
```

## Error Handling

```shell
# Standard err() helper — use for all error output
err() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*" >&2
}

if ! do_something; then
  err "Unable to do_something"
  exit 1
fi

# Checking return values — direct if preferred
if ! mv "${file_list[@]}" "${dest_dir}/"; then
  echo "Unable to move ${file_list[*]} to ${dest_dir}" >&2
  exit 1
fi

# PIPESTATUS — capture immediately
tar -cf - ./* | ( cd "${dir}" && tar -xf - )
return_codes=( "${PIPESTATUS[@]}" )
if (( return_codes[0] != 0 )); then
  do_something
fi
if (( return_codes[1] != 0 )); then
  do_something_else
fi
```

## Function Comments

```shell
#######################################
# Cleanup files from the backup directory.
# Globals:
#   BACKUP_DIR
#   ORACLE_SID
# Arguments:
#   None
#######################################
cleanup() {
  ...
}

#######################################
# Get configuration directory.
# Globals:
#   SOMEDIR
# Arguments:
#   None
# Outputs:
#   Writes location to stdout
#######################################
get_dir() {
  echo "${SOMEDIR}"
}

#######################################
# Delete a file in a sophisticated manner.
# Arguments:
#   File to delete, a path.
# Returns:
#   0 if thing was deleted, non-zero on error.
#######################################
del_thing() {
  rm "$1"
}
```

## Formatting

### Pipelines

```shell
# Fits on one line — keep it
command1 | command2

# Long — split with \ and | on next line, 2-space indent
command1 \
  | command2 \
  | command3 \
  | command4
```

### Control flow

```shell
local dir
for dir in "${dirs_to_cleanup[@]}"; do
  if [[ -d "${dir}/${SESSION_ID}" ]]; then
    log_date "Cleaning up old files in ${dir}/${SESSION_ID}"
    rm "${dir}/${SESSION_ID}/"* || error_message
  else
    mkdir -p "${dir}/${SESSION_ID}" || error_message
  fi
done

# Always include "in $@" explicitly
for arg in "$@"; do
  echo "argument: ${arg}"
done
```

### Case statements

```shell
# Multi-line alternatives
case "${expression}" in
  a)
    variable="..."
    some_command "${variable}" "${other_expr}"
    ;;
  absolute)
    actions="relative"
    another_command "${actions}" "${other_expr}"
    ;;
  *)
    error "Unexpected expression '${expression}'"
    ;;
esac

# Single-line alternatives (for short option processing)
verbose='false'
aflag=''
bflag=''
files=''
while getopts 'abf:v' flag; do
  case "${flag}" in
    a) aflag='true' ;;
    b) bflag='true' ;;
    f) files="${OPTARG}" ;;
    v) verbose='true' ;;
    *) error "Unexpected option ${flag}" ;;
  esac
done
```

### Long strings

```shell
# Heredoc for long text
cat <<END
I am an exceptionally long
string.
END

# Embedded newlines
long_string="I am an exceptionally
long string."

# Long paths on their own line, use variables for clarity
long_file="/i/am/an/exceptionally/loooooooong_file"
long_string_alt="including ${long_file} in this string"
```

## Quoting and Variable Expansion

```shell
# Preferred: brace-delimit most variables
echo "PATH=${PATH}, PWD=${PWD}, mine=${some_var}"
while read -r f; do
  echo "file=${f}"
done < <(find /tmp)

# Single-character specials: no braces needed
echo "Positional: $1" "$5" "$3"
echo "Specials: !=$!, -=$-, _=$_. ?=$?, #=$# *=$* @=$@ \$=$$"

# Braces necessary for disambiguation
set -- a b c
echo "${1}0${2}0${3}0"

# Arrays with quoted expansion for command flags
declare -a FLAGS
FLAGS=( --foo --bar='baz' )
readonly FLAGS
mybinary "${FLAGS[@]}"

# Command substitutions always quoted
flag="$(some_command and its args "$@" 'quoted separately')"
echo "${flag}"

# Integer variables — ok to not quote
if (( $# > 3 )); then
  echo "ppid=${PPID}"
fi

# Always quote command substitutions even for integers
number="$(generate_number)"

# Conditional cc expansion
git send-email --to "${reviewers}" ${ccs:+"--cc" "${ccs}"}

# $@ vs $*: always prefer "$@"
# "$@" preserves arguments as-is
# "$*" joins all args into one string
```

## Tests and Conditionals

```shell
# Use [[ ]] — supports regex and pattern matching
if [[ "filename" =~ ^[[:alnum:]]+name ]]; then
  echo "Match"
fi

# String comparison — use == not =
if [[ "${my_var}" == "some_string" ]]; then
  do_something
fi

# Empty/non-empty — use -z and -n explicitly
if [[ -z "${my_var}" ]]; then
  do_something  # var is empty
fi
if [[ -n "${my_var}" ]]; then
  do_something  # var is non-empty
fi

# Numeric comparison — use (( )) not [[ > ]]
if (( my_var > 3 )); then
  do_something
fi
```

## Arrays

```shell
# Declare and build arrays with +=()
declare -a flags
flags=(--foo --bar='baz')
flags+=(--greeting="Hello ${name}")
mybinary "${flags[@]}"

# WRONG — string-based flags break on spaces
flags='--foo --bar=baz'
flags+=' --greeting="Hello world"'  # Breaks
mybinary ${flags}

# WRONG — unquoted command expansion in array assignment
declare -a files=($(ls /directory))  # Globbing/splitting issues
```

## Pipes to While

```shell
# WRONG — pipe creates subshell, variable changes lost
last_line='NULL'
your_command | while read -r line; do
  if [[ -n "${line}" ]]; then
    last_line="${line}"
  fi
done
echo "${last_line}"  # Always 'NULL'!

# CORRECT — process substitution
last_line='NULL'
while read -r line; do
  if [[ -n "${line}" ]]; then
    last_line="${line}"
  fi
done < <(your_command)
echo "${last_line}"  # Actual last line

# CORRECT — readarray (bash 4+)
last_line='NULL'
readarray -t lines < <(your_command)
for line in "${lines[@]}"; do
  if [[ -n "${line}" ]]; then
    last_line="${line}"
  fi
done
echo "${last_line}"
```

## Arithmetic

```shell
# Use $(( )) and (( ))
echo "$(( 2 + 2 )) is 4"

if (( a < b )); then
  echo "a is less"
fi

(( i = 10 * j + 400 ))

# Omit ${} inside $(( )) — cleaner
local -i hundred="$(( 10 * 10 ))"
declare -i five="$(( 10 / 2 ))"
# With set -e: use || true when result could be zero
(( i += 3 ))
(( i -= 5 ))
(( i++ )) || true  # safe when i could be 0

hr=2; min=5; sec=30
echo "$(( hr * 3600 + min * 60 + sec ))"  # 7530

# WRONG — deprecated or external
i=$[2 * 10]          # Non-portable
let i="2 + 2"        # Subject to globbing
i=$( expr 4 + 4 )    # External process, slow
```

## Naming and Structure

```shell
#!/usr/bin/env bash
#
# Script description.

set -euo pipefail

# Constants at top
readonly CONFIG_DIR='/etc/myapp'
readonly LOG_FILE='/var/log/myapp.log'

#######################################
# Helper function.
# Arguments:
#   $1 - message
# Outputs:
#   Writes timestamped message to stderr
#######################################
err() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*" >&2
}

#######################################
# Process a single item.
# Arguments:
#   $1 - item path
# Returns:
#   0 on success, 1 on error.
#######################################
process_item() {
  local item_path="$1"

  # Separate declaration from command substitution
  local result
  result="$(compute_something "${item_path}")"
  (( $? == 0 )) || return 1

  echo "${result}"
}

#######################################
# Main entry point.
# Globals:
#   CONFIG_DIR
#   LOG_FILE
# Arguments:
#   Command-line args via "$@"
#######################################
main() {
  local -a items=()

  while read -r item; do
    items+=("${item}")
  done < <(find "${CONFIG_DIR}" -name '*.conf')

  local item
  for item in "${items[@]}"; do
    if ! process_item "${item}"; then
      err "Failed to process ${item}"
    fi
  done
}

main "$@"
```

## Builtins over External Commands

```shell
# Prefer builtins
addition="$(( X + Y ))"
substitution="${string/#foo/bar}"
if [[ "${string}" =~ foo:([0-9]+) ]]; then
  extraction="${BASH_REMATCH[1]}"
fi

# Avoid external commands for simple operations
addition="$(expr "${X}" + "${Y}")"                          # Slow
substitution="$(echo "${string}" | sed -e 's/^foo/bar/')"   # Unnecessary
extraction="$(echo "${string}" | sed -e 's/foo:\([0-9]\)/\1/')"  # Overkill
```
