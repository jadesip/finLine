#!/bin/bash

# kill-servers.sh - Find and gracefully kill finLine dev servers
# Usage: ./scripts/kill-servers.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  finLine Server Cleanup Utility${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Arrays to store found processes
declare -a PIDS
declare -a DESCRIPTIONS

# Function to find processes on a specific port
find_port_processes() {
    local port=$1
    local desc=$2
    local pids=$(lsof -ti :$port 2>/dev/null || true)

    if [ -n "$pids" ]; then
        for pid in $pids; do
            local cmd=$(ps -p $pid -o command= 2>/dev/null | head -c 80 || echo "unknown")

            # Skip browsers and other non-server processes
            if [[ "$cmd" == *"Chrome"* ]] || [[ "$cmd" == *"Safari"* ]] || [[ "$cmd" == *"Firefox"* ]] || [[ "$cmd" == *"Brave"* ]]; then
                continue
            fi

            PIDS+=("$pid")
            DESCRIPTIONS+=("Port $port ($desc): PID $pid - $cmd")
        done
    fi
}

# Function to find processes by name pattern
find_named_processes() {
    local pattern=$1
    local desc=$2
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)

    if [ -n "$pids" ]; then
        for pid in $pids; do
            # Skip if already in list
            if [[ " ${PIDS[*]} " =~ " ${pid} " ]]; then
                continue
            fi
            local cmd=$(ps -p $pid -o command= 2>/dev/null | head -c 60 || echo "unknown")
            PIDS+=("$pid")
            DESCRIPTIONS+=("$desc: PID $pid - $cmd")
        done
    fi
}

echo -e "${YELLOW}Scanning for running servers...${NC}"
echo ""

# Find frontend servers (Next.js typically on 3000)
find_port_processes 3000 "Frontend/Next.js"
find_port_processes 3001 "Frontend alternate"

# Find backend servers (FastAPI/Uvicorn typically on 8000)
find_port_processes 8000 "Backend/FastAPI"
find_port_processes 8001 "Backend alternate"

# Find by process patterns (in case ports are different)
find_named_processes "next-server" "Next.js server"
find_named_processes "next dev" "Next.js dev"
find_named_processes "uvicorn.*finline" "Uvicorn/finLine"
find_named_processes "uvicorn.*main:app" "Uvicorn main"
find_named_processes "python.*uvicorn" "Python Uvicorn"

# Check if any processes found
if [ ${#PIDS[@]} -eq 0 ]; then
    echo -e "${GREEN}No running finLine servers found.${NC}"
    exit 0
fi

# Display found processes
echo -e "${YELLOW}Found ${#PIDS[@]} server process(es):${NC}"
echo ""
for i in "${!DESCRIPTIONS[@]}"; do
    echo -e "  ${RED}[$((i+1))]${NC} ${DESCRIPTIONS[$i]}"
done
echo ""

# Ask for confirmation
echo -e "${YELLOW}Options:${NC}"
echo "  [a] Kill ALL listed processes"
echo "  [n] Cancel - don't kill anything"
echo "  [1-9] Kill specific process by number"
echo ""
read -p "Your choice: " choice

case $choice in
    a|A|all|ALL)
        echo ""
        echo -e "${YELLOW}Sending SIGTERM to all processes...${NC}"
        for pid in "${PIDS[@]}"; do
            if kill -0 $pid 2>/dev/null; then
                echo -e "  Killing PID $pid..."
                kill -TERM $pid 2>/dev/null || true
            fi
        done

        # Wait a moment and check if they're gone
        sleep 2

        still_running=0
        for pid in "${PIDS[@]}"; do
            if kill -0 $pid 2>/dev/null; then
                still_running=$((still_running + 1))
            fi
        done

        if [ $still_running -gt 0 ]; then
            echo ""
            echo -e "${YELLOW}$still_running process(es) still running. Force kill? [y/N]${NC}"
            read -p "" force
            if [[ $force =~ ^[Yy]$ ]]; then
                for pid in "${PIDS[@]}"; do
                    if kill -0 $pid 2>/dev/null; then
                        echo -e "  Force killing PID $pid..."
                        kill -9 $pid 2>/dev/null || true
                    fi
                done
            fi
        fi

        echo ""
        echo -e "${GREEN}Done! All servers stopped.${NC}"
        ;;

    n|N|no|NO)
        echo ""
        echo -e "${BLUE}Cancelled. No processes killed.${NC}"
        exit 0
        ;;

    [1-9])
        idx=$((choice - 1))
        if [ $idx -lt ${#PIDS[@]} ]; then
            pid=${PIDS[$idx]}
            echo ""
            echo -e "${YELLOW}Killing PID $pid...${NC}"
            kill -TERM $pid 2>/dev/null || true
            sleep 1
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}Process still running. Force kill? [y/N]${NC}"
                read -p "" force
                if [[ $force =~ ^[Yy]$ ]]; then
                    kill -9 $pid 2>/dev/null || true
                fi
            fi
            echo -e "${GREEN}Done!${NC}"
        else
            echo -e "${RED}Invalid selection.${NC}"
            exit 1
        fi
        ;;

    *)
        echo -e "${RED}Invalid option.${NC}"
        exit 1
        ;;
esac
