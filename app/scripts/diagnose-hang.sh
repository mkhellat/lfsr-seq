#!/bin/sh
# diagnose-hang.sh - Reproduce and diagnose an intermittent test hang.
#
# Some bugs in this project only manifest as an intermittent hang under
# pytest -- a loop that spins forever under specific, hard-to-predict
# conditions, or an interaction between SageMath's C-extension internals
# and pytest's own machinery (both have shown up in this project's
# history; see dev-docs/ for the investigations that used this exact
# technique). A single test run either passes quickly or hangs, with no
# guarantee which; a debugger attached from the start would need to
# already be attached before the hang begins, which isn't practical for
# something intermittent.
#
# This script automates the actual technique that found those bugs:
# 1. Run the given pytest target repeatedly in the background.
# 2. After a short grace period, check if the process is still running.
#    If it finished, that was a clean (non-hung) run -- try again.
#    If it's still running past the grace period, treat it as hung.
# 3. On the first hang, take several stack-trace snapshots a few seconds
#    apart using py-spy (with --locals to see live variable values, and
#    a --native dump to see into compiled C/Cython extensions like
#    SageMath's, which a plain Python-level trace can't reach).
# 4. Compare the snapshots: if local variables (e.g. a loop counter or
#    a set that should be growing) are IDENTICAL across snapshots taken
#    seconds apart, the process is genuinely stuck (an infinite loop or
#    a deadlock) rather than just doing slow-but-progressing work.
#
# Requirements:
#   - The project's .venv must exist (make install-dev) with py-spy
#     installed inside it: .venv/bin/pip install py-spy
#   - py-spy needs ptrace access to the target process. On most Linux
#     distributions this means running the dump step (not the reproduce
#     loop) with sudo; see /proc/sys/kernel/yama/ptrace_scope if unsure.
#
# Usage:
#   ./scripts/diagnose-hang.sh [options] -- <pytest args...>
#
# Options:
#   -g, --grace SECONDS     Seconds to wait before treating the process
#                            as hung (default: 8)
#   -n, --attempts N         Max number of reproduction attempts (default: 20)
#   -s, --snapshots N        Number of py-spy dumps to take, spaced 3s
#                            apart, once a hang is caught (default: 3)
#   -h, --help               Show this help message
#
# Examples:
#   # Reproduce and diagnose the exact hang this script was written for:
#   ./scripts/diagnose-hang.sh -- \
#       "tests/test_ml.py::TestPeriodPredictionModel::test_save_and_load_round_trip" \
#       "tests/test_ml.py::TestTrainingPipeline::test_train_period_prediction_model"
#
#   # Diagnose a hang anywhere in a specific test file, with more patience:
#   ./scripts/diagnose-hang.sh --grace 20 --attempts 5 -- tests/test_analysis.py
#
# This script only reproduces and reports; it does not modify any code.
# If it catches a hang, read the "Locals" sections of each py-spy
# snapshot and compare them across snapshots -- values that never
# change across snapshots taken several seconds apart are the strongest
# clue to what's actually stuck.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

GRACE=8
ATTEMPTS=20
SNAPSHOTS=3
PYTEST_ARGS=""

while [ $# -gt 0 ]; do
    case "$1" in
        -g|--grace)
            GRACE="$2"
            shift 2
            ;;
        -n|--attempts)
            ATTEMPTS="$2"
            shift 2
            ;;
        -s|--snapshots)
            SNAPSHOTS="$2"
            shift 2
            ;;
        -h|--help)
            sed -n '2,60p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        --)
            shift
            PYTEST_ARGS="$*"
            break
            ;;
        *)
            echo "Unknown option: $1 (use -- to separate pytest args)" >&2
            exit 1
            ;;
    esac
done

if [ -z "$PYTEST_ARGS" ]; then
    echo "ERROR: no pytest arguments given. Usage: $0 [options] -- <pytest args...>" >&2
    exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "ERROR: .venv not found. Run 'make install-dev' first." >&2
    exit 1
fi

if [ ! -x ".venv/bin/py-spy" ]; then
    echo "ERROR: py-spy not installed in .venv. Run:" >&2
    echo "  .venv/bin/pip install py-spy" >&2
    exit 1
fi

echo "Reproducing (grace=${GRACE}s, up to ${ATTEMPTS} attempts)..."
echo "pytest target(s): $PYTEST_ARGS"
echo ""

i=1
while [ "$i" -le "$ATTEMPTS" ]; do
    LOGFILE="/tmp/diagnose-hang-run-${i}.log"
    # shellcheck disable=SC2086
    .venv/bin/python -m pytest --no-cov -q $PYTEST_ARGS > "$LOGFILE" 2>&1 &
    PYPID=$!
    sleep "$GRACE"

    if kill -0 "$PYPID" 2>/dev/null; then
        echo "=== Reproduced on attempt $i (PID $PYPID) ==="
        echo ""

        if [ "$(id -u)" -ne 0 ]; then
            echo "py-spy needs ptrace access to dump this process's stack."
            echo "In another terminal, run (while this one keeps waiting):"
            echo ""
            echo "  sudo .venv/bin/py-spy dump --pid $PYPID --locals"
            echo ""
            echo "Repeat that command a few times, a few seconds apart, and"
            echo "compare the 'Locals' sections across dumps: values that"
            echo "never change indicate the process is genuinely stuck there"
            echo "(not just doing slow, progressing work)."
            echo ""
            echo "This script will keep PID $PYPID alive for up to 60 more"
            echo "seconds so you have time to run the command above."
            w=0
            while [ "$w" -lt 12 ] && kill -0 "$PYPID" 2>/dev/null; do
                sleep 5
                w=$((w + 1))
            done
        else
            n=1
            while [ "$n" -le "$SNAPSHOTS" ]; do
                echo "--- py-spy dump #$n ---"
                .venv/bin/py-spy dump --pid "$PYPID" --locals || true
                echo ""
                n=$((n + 1))
                [ "$n" -le "$SNAPSHOTS" ] && sleep 3
            done
            echo "--- native stack (reaches into compiled C/Cython frames) ---"
            .venv/bin/py-spy dump --pid "$PYPID" --native || true
        fi

        kill -9 "$PYPID" 2>/dev/null || true
        exit 0
    else
        wait "$PYPID" 2>/dev/null || true
        echo "attempt $i: finished within ${GRACE}s (no hang) -- see $LOGFILE"
        rm -f "$LOGFILE"
    fi
    i=$((i + 1))
done

echo ""
echo "Did not reproduce a hang in $ATTEMPTS attempts."
echo "Try increasing --attempts, or lowering --grace if runs are borderline."
exit 1
