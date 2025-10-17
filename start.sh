#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Display usage
usage() {
    echo -e "${CYAN}Usage:${NC}"
    echo -e "  ./start.sh [option]"
    echo -e ""
    echo -e "${CYAN}Options:${NC}"
    echo -e "  ${GREEN}setup${NC}    - Install dependencies and configure environment"
    echo -e "  ${GREEN}run${NC}      - Start the application (runs setup if needed)"
    echo -e "  ${GREEN}help${NC}     - Show this help message"
    echo -e ""
    echo -e "${CYAN}Examples:${NC}"
    echo -e "  ./start.sh setup   # First-time setup"
    echo -e "  ./start.sh run     # Start the app"
    echo -e "  ./start.sh         # Same as 'run' (default)"
}

# Setup function
setup() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}LLM Based Curriculum Analyzer - Setup${NC}"
    echo -e "${GREEN}========================================${NC}\n"

    # Check if .env exists in backend
    if [ ! -f "backend/.env" ]; then
        echo -e "${YELLOW}Backend .env file not found. Creating from template...${NC}"
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
        else
            echo "GOOGLE_API_KEY=your_api_key_here" > backend/.env
        fi
        echo -e "${RED}⚠️  Please edit backend/.env and add your GOOGLE_API_KEY${NC}"
        echo -e "${RED}⚠️  Get your API key from: https://aistudio.google.com/app/apikey${NC}\n"
    fi

    # Check if .env.local exists in frontend
    if [ ! -f "frontend/.env.local" ]; then
        echo -e "${YELLOW}Frontend .env.local file not found. Creating from template...${NC}"
        if [ -f "frontend/.env.example" ]; then
            cp frontend/.env.example frontend/.env.local
        else
            echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" > frontend/.env.local
        fi
        echo -e "${GREEN}✓ Frontend environment configured${NC}\n"
    fi

    # Check if virtual environment exists
    if [ ! -d "backend/venv" ]; then
        echo -e "${YELLOW}Creating Python virtual environment...${NC}"
        cd backend
        python3 -m venv venv
        cd ..
        echo -e "${GREEN}✓ Virtual environment created${NC}\n"
    fi

    # Install backend dependencies
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    cd backend
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    deactivate
    cd ..
    echo -e "${GREEN}✓ Backend dependencies installed${NC}\n"

    # Check if node_modules exists in frontend
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        cd frontend
        if command -v pnpm &> /dev/null; then
            pnpm install
        elif command -v npm &> /dev/null; then
            echo -e "${YELLOW}pnpm not found, using npm instead...${NC}"
            npm install
        else
            echo -e "${RED}Error: Neither pnpm nor npm found. Please install Node.js${NC}"
            exit 1
        fi
        cd ..
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}\n"
    fi

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}\n"
}

# Run function
run() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Starting LLM Based Curriculum Analyzer${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    # Check if setup has been run
    NEEDS_SETUP=false
    if [ ! -f "backend/.env" ]; then
        NEEDS_SETUP=true
    fi
    if [ ! -d "backend/venv" ]; then
        NEEDS_SETUP=true
    fi
    if [ ! -d "frontend/node_modules" ]; then
        NEEDS_SETUP=true
    fi

    if [ "$NEEDS_SETUP" = true ]; then
        echo -e "${YELLOW}First-time setup required...${NC}\n"
        setup
        echo -e "\n${YELLOW}Setup complete! Starting servers...${NC}\n"
    fi

    # Verify API key is set
    if grep -q "your_api_key_here" backend/.env 2>/dev/null || ! grep -q "GOOGLE_API_KEY=" backend/.env 2>/dev/null; then
        echo -e "${RED}Error: GOOGLE_API_KEY not configured in backend/.env${NC}"
        echo -e "${YELLOW}Please edit backend/.env and add your API key${NC}"
        echo -e "${YELLOW}Get your API key from: https://aistudio.google.com/app/apikey${NC}\n"
        exit 1
    fi

    # Trap to cleanup background processes on exit
    cleanup() {
        echo -e "\n${YELLOW}Shutting down servers...${NC}"
        kill $BACKEND_PID 2>/dev/null
        kill $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}Servers stopped${NC}"
        exit 0
    }
    trap cleanup SIGINT SIGTERM

    # Start backend
    echo -e "${YELLOW}Starting backend server...${NC}"
    cd backend
    source venv/bin/activate
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..

    # Wait a bit for backend to start
    sleep 3

    # Check if backend started successfully
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Error: Backend failed to start. Check backend.log for details${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Backend running (PID: $BACKEND_PID)${NC}"

    # Start frontend
    echo -e "${YELLOW}Starting frontend server...${NC}"
    cd frontend
    if command -v pnpm &> /dev/null; then
        pnpm dev > ../frontend.log 2>&1 &
    else
        npm run dev > ../frontend.log 2>&1 &
    fi
    FRONTEND_PID=$!
    cd ..

    # Wait a bit for frontend to start
    sleep 3

    # Check if frontend started successfully
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}Error: Frontend failed to start. Check frontend.log for details${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    echo -e "${GREEN}✓ Frontend running (PID: $FRONTEND_PID)${NC}"

    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Application is running!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
    echo -e "${BLUE}Backend:${NC}  http://localhost:8000"
    echo -e "${BLUE}API Docs:${NC} http://localhost:8000/docs"
    echo -e "\n${CYAN}Logs:${NC}"
    echo -e "  Backend:  tail -f backend.log"
    echo -e "  Frontend: tail -f frontend.log"
    echo -e "\n${YELLOW}Press Ctrl+C to stop all servers${NC}\n"

    # Wait for processes
    wait
}

# Main script logic
case "${1:-run}" in
    setup)
        setup
        ;;
    run|start)
        run
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}\n"
        usage
        exit 1
        ;;
esac
