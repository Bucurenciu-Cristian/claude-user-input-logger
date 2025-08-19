#!/usr/bin/env python3
"""
Claude User Input Logger Hook

Captures and logs all user inputs to Claude Code with timestamps and session tracking.
This hook extracts user messages from conversation transcripts and provides organized logging.

Author: Claude & Cristian Bucurenciu
Version: 1.0.0
License: MIT
"""
import json
import sys
from datetime import datetime
from pathlib import Path


# Configuration
CONFIG = {
    'max_transcript_lines': 20,     # Number of transcript lines to check for user messages
    'max_messages_per_capture': 3,  # Maximum messages to capture per hook trigger
    'min_message_length': 10,       # Minimum message length to capture
    'log_retention_days': 30,       # Days to retain log files (not implemented yet)
    'enable_daily_logs': True,      # Create separate daily log files
    'enable_statistics': True,      # Track usage statistics
}


def extract_user_messages_from_transcript(transcript_path, session_id):
    """
    Extract recent user messages from the conversation transcript file.
    
    Args:
        transcript_path (str): Path to the JSONL transcript file
        session_id (str): Current session ID for filtering
    
    Returns:
        list: List of recent user messages
    """
    user_messages = []
    
    try:
        if not Path(transcript_path).exists():
            return user_messages
            
        # Read the last few lines of the JSONL file to get recent messages
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Check recent lines for user messages
        for line in lines[-CONFIG['max_transcript_lines']:]:
            try:
                entry = json.loads(line.strip())
                
                # Look for user messages in Claude Code transcript format
                if entry.get('type') == 'user':
                    # Extract text from message.content (handle both string and array formats)
                    message_obj = entry.get('message', {})
                    content = message_obj.get('content', '')
                    
                    text_content = ''
                    
                    # Handle different content formats
                    if isinstance(content, str):
                        # Direct string format: "content": "message text"
                        text_content = content
                    elif isinstance(content, list) and len(content) > 0:
                        # Array format: "content": [{"type": "text", "text": "message text"}]
                        if isinstance(content[0], dict):
                            text_content = content[0].get('text', '')
                        else:
                            text_content = str(content[0])
                    
                    if text_content and isinstance(text_content, str):
                        # Clean up command messages and system messages
                        text = text_content.strip()
                        
                        # Skip command messages and system messages
                        if (not text.startswith('<command-') and 
                            not text.startswith('Stop hook feedback') and
                            not text.startswith('[Request interrupted') and
                            not text.startswith('Caveat:') and
                            len(text) >= CONFIG['min_message_length']):
                            user_messages.append(text)
                        
            except (json.JSONDecodeError, KeyError, AttributeError):
                continue
                
    except Exception:
        # Fail silently to avoid breaking Claude Code functionality
        pass
        
    return user_messages[-CONFIG['max_messages_per_capture']:] if user_messages else []


def extract_user_context(input_data):
    """
    Extract user input/context from the JSON data and transcript.
    
    Args:
        input_data (dict): Hook input data from Claude Code
    
    Returns:
        dict: Dictionary containing user context data
    """
    user_context = {}
    
    # Try to get user messages from transcript
    transcript_path = input_data.get('transcript_path')
    session_id = input_data.get('session_id', '')
    
    if transcript_path and session_id:
        recent_messages = extract_user_messages_from_transcript(transcript_path, session_id)
        if recent_messages:
            user_context['recent_user_messages'] = recent_messages
    
    # Check for any direct user fields in the JSON (fallback)
    potential_user_fields = [
        'user_message', 'message', 'prompt', 'input', 'context', 
        'user_input', 'query', 'request', 'content', 'text',
        'user_context', 'conversation_context'
    ]
    
    for field in potential_user_fields:
        if field in input_data:
            user_context[field] = input_data[field]
    
    return user_context


def create_log_entry(timestamp, session_id, tool_name, user_context):
    """
    Create a formatted log entry.
    
    Args:
        timestamp (str): Formatted timestamp
        session_id (str): Session identifier
        tool_name (str): Name of the tool that triggered the hook
        user_context (dict): User context data
    
    Returns:
        str: Formatted log entry
    """
    if user_context:
        context_str = " | ".join([
            f"{k}: {str(v)[:200]}..." if len(str(v)) > 200 else f"{k}: {v}" 
            for k, v in user_context.items()
        ])
        return f"[{timestamp}] [{session_id[:8]}] Tool: {tool_name} | User Context: {context_str}\n"
    else:
        return f"[{timestamp}] [{session_id[:8]}] Tool: {tool_name} | No user context detected\n"


def write_to_log_file(log_entry, log_file_path):
    """
    Write log entry to file with error handling.
    
    Args:
        log_entry (str): The log entry to write
        log_file_path (Path): Path to the log file
    """
    try:
        # Ensure directory exists
        log_file_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write to log file {log_file_path}: {e}", file=sys.stderr)


def update_statistics(tool_name, user_context):
    """
    Update usage statistics.
    
    Args:
        tool_name (str): Name of the tool that triggered the hook
        user_context (dict): User context data
    """
    if not CONFIG['enable_statistics']:
        return
    
    stats_file = Path.home() / '.claude' / 'hooks' / 'user-input-stats.json'
    
    try:
        stats = {}
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        
        # Track tool triggers and user context frequency
        stats['total_interactions'] = stats.get('total_interactions', 0) + 1
        stats['tools_triggered'] = stats.get('tools_triggered', {})
        stats['tools_triggered'][tool_name] = stats['tools_triggered'].get(tool_name, 0) + 1
        
        if user_context:
            stats['interactions_with_context'] = stats.get('interactions_with_context', 0) + 1
            stats['context_fields_found'] = stats.get('context_fields_found', {})
            for field in user_context.keys():
                stats['context_fields_found'][field] = stats['context_fields_found'].get(field, 0) + 1
        
        # Ensure directory exists
        stats_file.parent.mkdir(exist_ok=True, parents=True)
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
    
    except Exception:
        # Fail silently to avoid breaking Claude Code functionality
        pass


def main():
    """
    Main hook function called by Claude Code.
    """
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        
        # Extract basic info
        tool_name = input_data.get('tool_name', 'unknown')
        session_id = input_data.get('session_id', 'unknown')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Extract user context from transcript
        user_context = extract_user_context(input_data)
        
        # Only log if we have meaningful data
        if user_context or tool_name != 'unknown':
            # Create log entry
            log_entry = create_log_entry(timestamp, session_id, tool_name, user_context)
            
            # Write to main log file
            main_log_file = Path.home() / '.claude' / 'user-inputs-log.txt'
            write_to_log_file(log_entry, main_log_file)
            
            # Write to daily log if enabled
            if CONFIG['enable_daily_logs']:
                daily_log = Path.home() / '.claude' / 'hooks' / f"user-inputs-{datetime.now().strftime('%Y-%m-%d')}.log"
                write_to_log_file(log_entry, daily_log)
            
            # Update statistics
            update_statistics(tool_name, user_context)
        
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Don't fail the command due to logging errors
        print(f"Warning: User input logging error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()