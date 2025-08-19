#!/bin/bash

# Claude User Input Logger - Installation Script
# Author: Claude & Cristian Bucurenciu
# Version: 1.0.0

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Installation paths
CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
HOOK_FILE="$HOOKS_DIR/log-user-inputs.py"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════╗"
    echo "║      Claude User Input Logger            ║"
    echo "║           Installation Script            ║"
    echo "╚══════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_dependencies() {
    print_info "Checking dependencies..."
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not found. Please install Python 3.6+ first."
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python ${python_version} found"
    
    # Check if jq is available (optional)
    if ! command -v jq &> /dev/null; then
        print_warning "jq not found. JSON viewing commands in README won't work."
        print_info "Install with: sudo apt install jq  # or  brew install jq"
    fi
}

create_directories() {
    print_info "Creating necessary directories..."
    
    # Create .claude directory if it doesn't exist
    if [ ! -d "$CLAUDE_DIR" ]; then
        mkdir -p "$CLAUDE_DIR"
        print_success "Created $CLAUDE_DIR"
    else
        print_success "$CLAUDE_DIR already exists"
    fi
    
    # Create hooks directory if it doesn't exist
    if [ ! -d "$HOOKS_DIR" ]; then
        mkdir -p "$HOOKS_DIR"
        print_success "Created $HOOKS_DIR"
    else
        print_success "$HOOKS_DIR already exists"
    fi
}

install_hook() {
    print_info "Installing hook file..."
    
    # Check if source file exists
    if [ ! -f "$SCRIPT_DIR/log-user-inputs.py" ]; then
        print_error "Hook file not found: $SCRIPT_DIR/log-user-inputs.py"
        exit 1
    fi
    
    # Copy hook file
    cp "$SCRIPT_DIR/log-user-inputs.py" "$HOOK_FILE"
    chmod +x "$HOOK_FILE"
    print_success "Hook installed to $HOOK_FILE"
}

backup_settings() {
    if [ -f "$SETTINGS_FILE" ]; then
        backup_file="${SETTINGS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$SETTINGS_FILE" "$backup_file"
        print_success "Settings backed up to $backup_file"
        return 0
    fi
    return 1
}

update_settings() {
    print_info "Updating Claude Code settings..."
    
    # Backup existing settings
    backup_settings
    
    # Hook configuration to add
    hook_config='{
      "hooks": [
        {
          "command": "~/.claude/hooks/log-user-inputs.py",
          "type": "command"
        }
      ],
      "matcher": ".*"
    }'
    
    if [ -f "$SETTINGS_FILE" ]; then
        # Settings file exists, merge configuration
        print_info "Existing settings.json found, merging configuration..."
        
        # Check if jq is available for JSON manipulation
        if command -v jq &> /dev/null; then
            # Use jq to merge settings
            temp_file=$(mktemp)
            
            # Add hook to PreToolUse array or create it
            jq --argjson hook "$hook_config" '
                if .hooks.PreToolUse then
                    .hooks.PreToolUse += [$hook]
                else
                    .hooks.PreToolUse = [$hook]
                end
            ' "$SETTINGS_FILE" > "$temp_file"
            
            mv "$temp_file" "$SETTINGS_FILE"
            print_success "Settings updated with hook configuration"
        else
            # Manual instructions without jq
            print_warning "jq not available for automatic settings merge"
            print_info "Please manually add this to your $SETTINGS_FILE:"
            echo ""
            echo "Add to the 'PreToolUse' array in 'hooks':"
            echo "$hook_config"
            echo ""
            print_info "Or run the installation again after installing jq"
        fi
    else
        # Create new settings file
        print_info "Creating new settings.json..."
        cat > "$SETTINGS_FILE" << EOF
{
  "hooks": {
    "PreToolUse": [
      $hook_config
    ]
  }
}
EOF
        print_success "Created $SETTINGS_FILE with hook configuration"
    fi
}

verify_installation() {
    print_info "Verifying installation..."
    
    # Check if hook file exists and is executable
    if [ -f "$HOOK_FILE" ] && [ -x "$HOOK_FILE" ]; then
        print_success "Hook file is installed and executable"
    else
        print_error "Hook file installation failed"
        return 1
    fi
    
    # Check if settings file exists
    if [ -f "$SETTINGS_FILE" ]; then
        print_success "Settings file exists"
    else
        print_error "Settings file not found"
        return 1
    fi
    
    # Test hook execution
    if echo '{"tool_name":"test","session_id":"install-test"}' | "$HOOK_FILE" > /dev/null 2>&1; then
        print_success "Hook executes successfully"
    else
        print_warning "Hook test execution failed (may work with actual Claude Code data)"
    fi
    
    return 0
}

print_completion_info() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════╗"
    echo "║     Installation Completed Successfully! ║"
    echo "╚══════════════════════════════════════════╝${NC}"
    echo ""
    print_info "Next steps:"
    echo "  1. Restart Claude Code to activate the hook"
    echo "  2. Start using Claude Code normally"
    echo "  3. Check your logs:"
    echo "     📁 Main log: ~/.claude/user-inputs-log.txt"
    echo "     📅 Daily logs: ~/.claude/hooks/user-inputs-YYYY-MM-DD.log"
    echo "     📊 Statistics: ~/.claude/hooks/user-input-stats.json"
    echo ""
    print_info "Quick commands:"
    echo "  🔍 View recent messages:"
    echo "     grep \"User Context:\" ~/.claude/user-inputs-log.txt | tail -5"
    echo ""
    echo "  📈 View statistics (requires jq):"
    echo "     cat ~/.claude/hooks/user-input-stats.json | jq ."
    echo ""
    echo -e "${GREEN}Happy logging! 🎉${NC}"
}

print_uninstall_info() {
    echo ""
    print_info "To uninstall:"
    echo "  1. Remove hook: rm ~/.claude/hooks/log-user-inputs.py"
    echo "  2. Edit ~/.claude/settings.json to remove hook configuration"
    echo "  3. Restart Claude Code"
}

# Main installation process
main() {
    print_header
    
    # Confirm installation
    echo "This script will install the Claude User Input Logger hook."
    echo "It will:"
    echo "  • Copy the hook to ~/.claude/hooks/"
    echo "  • Update your Claude Code settings"
    echo "  • Create necessary directories"
    echo ""
    read -p "Continue with installation? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled."
        exit 0
    fi
    
    echo ""
    
    # Run installation steps
    check_dependencies
    create_directories
    install_hook
    update_settings
    
    if verify_installation; then
        print_completion_info
        print_uninstall_info
    else
        print_error "Installation verification failed. Please check the errors above."
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Claude User Input Logger Installation Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --force        Force installation without confirmation"
        echo "  --uninstall    Remove the hook (not implemented yet)"
        echo ""
        exit 0
        ;;
    --force)
        print_header
        check_dependencies
        create_directories
        install_hook
        update_settings
        verify_installation && print_completion_info
        ;;
    --uninstall)
        print_error "Uninstall functionality not implemented yet."
        print_uninstall_info
        exit 1
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information."
        exit 1
        ;;
esac