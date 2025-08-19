#!/usr/bin/env python3
"""
Optimized User Input Logger for Claude Code.
Captures user messages with duplicate detection and clean formatting.
Only logs actual user input, no noise.
"""
import json
import sys
from datetime import datetime
from pathlib import Path


def extract_user_messages_from_transcript(transcript_path, session_id):
    """
    Extract recent user messages from the conversation transcript file.
    """
    user_messages = []
    
    try:
        if not Path(transcript_path).exists():
            return user_messages
            
        # Read the last few lines of the JSONL file to get recent messages
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
            
        # Check last 20 lines for user messages
        for line in lines[-20:]:
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
                            len(text) > 10):  # Skip very short messages
                            user_messages.append(text)
                        
            except (json.JSONDecodeError, KeyError, AttributeError):
                continue
                
    except Exception:
        pass
        
    return user_messages[-3:] if user_messages else []  # Return last 3 messages


def extract_user_context(input_data):
    """
    Extract potential user input/context from the JSON data and transcript.
    """
    user_context = {}
    
    # Try to get user messages from transcript
    transcript_path = input_data.get('transcript_path')
    session_id = input_data.get('session_id', '')
    
    if transcript_path and session_id:
        recent_messages = extract_user_messages_from_transcript(transcript_path, session_id)
        if recent_messages:
            user_context['recent_user_messages'] = recent_messages
    
    # Still check for any direct user fields in the JSON
    potential_user_fields = [
        'user_message', 'message', 'prompt', 'input', 'context', 
        'user_input', 'query', 'request', 'content', 'text',
        'user_context', 'conversation_context'
    ]
    
    for field in potential_user_fields:
        if field in input_data:
            user_context[field] = input_data[field]
    
    return user_context


def load_recent_messages():
    """Load recent messages to prevent duplicates."""
    recent_file = Path.home() / '.claude' / 'hooks' / 'recent-messages.json'
    try:
        if recent_file.exists():
            with open(recent_file, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_recent_messages(messages):
    """Save recent messages for duplicate detection."""
    recent_file = Path.home() / '.claude' / 'hooks' / 'recent-messages.json'
    try:
        # Keep only last 20 messages
        messages = messages[-20:] if len(messages) > 20 else messages
        with open(recent_file, 'w') as f:
            json.dump(messages, f)
    except Exception:
        pass


def main():
    try:
        # Read input
        input_data = json.load(sys.stdin)
        
        # Extract basic info
        tool_name = input_data.get('tool_name', 'unknown')
        session_id = input_data.get('session_id', 'unknown')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Extract potential user context
        user_context = extract_user_context(input_data)
        
        # Only proceed if we have actual user messages
        if user_context and 'recent_user_messages' in user_context:
            user_messages = user_context['recent_user_messages']
            
            # Load recent messages for duplicate detection
            recent_messages = load_recent_messages()
            
            # Filter out duplicates and process each message
            new_messages = []
            for message in user_messages:
                if message not in recent_messages:
                    new_messages.append(message)
                    recent_messages.append(message)
                    
                    # Clean log format - just show the actual message
                    log_entry = f"[{timestamp}] [{session_id[:8]}] {message}\n"
                    
                    # Main user inputs log
                    log_file = Path.home() / '.claude' / 'user-inputs-log.txt'
                    try:
                        with open(log_file, 'a') as f:
                            f.write(log_entry)
                    except Exception as e:
                        print(f"Warning: Could not write to user inputs log: {e}", file=sys.stderr)
                    
                    # Daily log
                    daily_log = Path.home() / '.claude' / 'hooks' / f"user-inputs-{datetime.now().strftime('%Y-%m-%d')}.log"
                    try:
                        daily_log.parent.mkdir(exist_ok=True)
                        with open(daily_log, 'a') as f:
                            f.write(log_entry)
                    except Exception:
                        pass
            
            # Save updated recent messages if we had new ones
            if new_messages:
                save_recent_messages(recent_messages)
                
                # Track statistics only for new user messages
                stats_file = Path.home() / '.claude' / 'hooks' / 'user-input-stats.json'
                try:
                    stats = {}
                    if stats_file.exists():
                        with open(stats_file, 'r') as f:
                            stats = json.load(f)
                    
                    # Track only meaningful interactions with user input
                    stats['total_interactions'] = stats.get('total_interactions', 0) + 1
                    stats['tools_triggered'] = stats.get('tools_triggered', {})
                    stats['tools_triggered'][tool_name] = stats['tools_triggered'].get(tool_name, 0) + 1
                    stats['user_messages_logged'] = stats.get('user_messages_logged', 0) + len(new_messages)
                    
                    with open(stats_file, 'w') as f:
                        json.dump(stats, f, indent=2)
                except Exception:
                    pass
        
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Don't fail the command due to logging errors
        print(f"Warning: User input logging error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()