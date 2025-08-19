# Claude User Input Logger 📋

A powerful and lightweight hook for [Claude Code](https://claude.ai/code) that captures and logs all your user inputs with timestamps, session tracking, and organized storage. Perfect for tracking your conversations, analyzing usage patterns, and maintaining a searchable history of your interactions with Claude.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Bucurenciu-Cristian/claude-user-input-logger)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://python.org)
[![Claude](https://img.shields.io/badge/Claude-Compatible-purple.svg)](https://claude.ai/code)

## ✨ Features

- **🎯 Smart Message Extraction**: Captures your actual messages from Claude Code conversation transcripts
- **⏰ Timestamp Tracking**: Every message logged with precise timestamps
- **🔄 Session Management**: Tracks different Claude Code sessions across restarts
- **📊 Usage Statistics**: Detailed analytics about your interactions and tool usage
- **📅 Daily Logs**: Separate daily log files for easy organization
- **🔧 Configurable**: Easy to customize logging behavior and retention policies
- **⚡ Lightweight**: Minimal performance impact on Claude Code
- **🛡️ Safe**: Fails gracefully without breaking Claude Code functionality

## 🚀 Quick Start

### Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/Bucurenciu-Cristian/claude-user-input-logger.git
   cd claude-user-input-logger
   ```

2. **Run the installation script:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Restart Claude Code** to activate the hook.

### Manual Installation

1. **Copy the hook file:**
   ```bash
   cp log-user-inputs.py ~/.claude/hooks/
   chmod +x ~/.claude/hooks/log-user-inputs.py
   ```

2. **Update your Claude settings:**
   Add this configuration to `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "hooks": [
             {
               "command": "~/.claude/hooks/log-user-inputs.py",
               "type": "command"
             }
           ],
           "matcher": ".*"
         }
       ]
     }
   }
   ```

3. **Restart Claude Code** to activate the hook.

## 📁 Log Files

After installation, your user inputs will be logged to:

### Main Log File
```
~/.claude/user-inputs-log.txt
```
Contains all your user inputs across all sessions.

### Daily Logs
```
~/.claude/hooks/user-inputs-YYYY-MM-DD.log
```
Separate log files for each day (e.g., `user-inputs-2025-08-19.log`).

### Statistics
```
~/.claude/hooks/user-input-stats.json
```
JSON file with usage statistics and analytics.

## 📋 Log Format

Each log entry follows this format:
```
[TIMESTAMP] [SESSION_ID] Tool: TOOL_NAME | User Context: YOUR_MESSAGE
```

**Example:**
```
[2025-08-19 14:45:03] [2356a836] Tool: TodoWrite | User Context: recent_user_messages: ["How do I view my Claude Code logs?"]
```

## 🔍 Viewing Your Logs

### Quick Commands

**See your recent messages:**
```bash
grep "User Context:" ~/.claude/user-inputs-log.txt | tail -10
```

**View today's logs:**
```bash
cat ~/.claude/hooks/user-inputs-$(date +%Y-%m-%d).log
```

**Check statistics:**
```bash
cat ~/.claude/hooks/user-input-stats.json | jq .
```

**Search for specific messages:**
```bash
grep -i "your search term" ~/.claude/user-inputs-log.txt
```

## ⚙️ Configuration

The hook includes built-in configuration options that can be modified in the script:

```python
CONFIG = {
    'max_transcript_lines': 20,     # Number of transcript lines to check
    'max_messages_per_capture': 3,  # Max messages to capture per trigger
    'min_message_length': 10,       # Minimum message length to log
    'log_retention_days': 30,       # Log retention period (future feature)
    'enable_daily_logs': True,      # Create daily log files
    'enable_statistics': True,      # Track usage statistics
}
```

## 📊 Statistics Dashboard

The hook automatically tracks:
- **Total interactions** with Claude Code
- **Tool usage frequency** (which tools you use most)
- **Message capture success rate**
- **Context field types** found in your messages

Example statistics output:
```json
{
  "total_interactions": 125,
  "tools_triggered": {
    "Read": 45,
    "Write": 30,
    "Bash": 25,
    "Edit": 20,
    "TodoWrite": 5
  },
  "interactions_with_context": 89,
  "context_fields_found": {
    "recent_user_messages": 89
  }
}
```

## 🛠️ How It Works

1. **Hook Trigger**: Activates on every tool use in Claude Code (Read, Write, Bash, etc.)
2. **Transcript Analysis**: Reads the conversation transcript file to find user messages
3. **Smart Filtering**: Filters out system messages and command outputs
4. **Message Extraction**: Extracts your actual user inputs
5. **Organized Logging**: Saves to multiple log files with timestamps
6. **Statistics Update**: Updates usage analytics in real-time

## 🔧 Troubleshooting

### Hook Not Working?

1. **Check if hook is installed:**
   ```bash
   ls -la ~/.claude/hooks/log-user-inputs.py
   ```

2. **Verify settings configuration:**
   ```bash
   grep -A 10 "log-user-inputs" ~/.claude/settings.json
   ```

3. **Check for errors:**
   ```bash
   tail ~/.claude/user-inputs-log.txt
   ```

4. **Restart Claude Code** after any changes.

### No Messages Being Captured?

- The hook only captures messages when tools are used
- Very short messages (< 10 characters) are filtered out
- System messages and commands are automatically excluded
- Check if log files are being created but without user context

### Permission Issues?

```bash
chmod +x ~/.claude/hooks/log-user-inputs.py
chmod 755 ~/.claude/hooks/
```

## 📈 Advanced Usage

### Custom Log Analysis

**Most active days:**
```bash
ls ~/.claude/hooks/user-inputs-*.log | xargs wc -l | sort -n
```

**Message frequency by hour:**
```bash
grep -o '\[2025-[0-9-]* [0-9]*:' ~/.claude/user-inputs-log.txt | cut -d' ' -f2 | cut -d':' -f1 | sort | uniq -c
```

**Your most used tools:**
```bash
jq -r '.tools_triggered | to_entries[] | "\(.value) \(.key)"' ~/.claude/hooks/user-input-stats.json | sort -nr
```

### Integration with Other Tools

**Export to CSV:**
```python
import json, csv
with open('user-input-stats.json') as f:
    data = json.load(f)
# Process and export as needed
```

**Database Integration:**
The log files can be easily imported into databases for advanced analysis.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test with Claude Code
5. Commit your changes: `git commit -m 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the [Claude Code](https://claude.ai/code) community
- Inspired by the need to track and analyze Claude interactions
- Thanks to all contributors and users

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Bucurenciu-Cristian/claude-user-input-logger/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Bucurenciu-Cristian/claude-user-input-logger/discussions)
- **Documentation**: This README and inline code comments

---

<div align="center">

**Made with ❤️ for the Claude Code community**

[⭐ Star this repo](https://github.com/Bucurenciu-Cristian/claude-user-input-logger) | [🐛 Report Bug](https://github.com/Bucurenciu-Cristian/claude-user-input-logger/issues) | [✨ Request Feature](https://github.com/Bucurenciu-Cristian/claude-user-input-logger/issues)

</div>