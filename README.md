# OpenMemory MCP Server

MCP (Model Context Protocol) server that provides Claude Desktop with access to your OpenMemory API running on Ubuntu server `richard-XPS-15-9560.local:8892`.

## Architecture

```
Claude Desktop (Windows)
    ↓ stdio
MCP Server (Python - this package)
    ↓ HTTP REST
OpenMemory API (richard-XPS-15-9560.local:8892)
    ↓
Neo4j + Vector DB (Ubuntu Docker)
```

## Features

The MCP server provides Claude Desktop with the following tools:

- **search_memories** - Semantic search across OpenMemory graph
- **add_memory** - Store new memories with sector classification
- **list_memories** - Browse recent memories with pagination
- **get_memory** - Retrieve specific memory by ID
- **reinforce_memory** - Boost importance of a memory
- **delete_memory** - Remove a memory
- **health_check** - Verify OpenMemory API connectivity

## Windows Installation

### Prerequisites

1. **Python 3.10 or higher** installed on Windows
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Claude Desktop** installed on Windows
   - Download from: https://claude.ai/download

3. **Network access** to `richard-XPS-15-9560.local:8892` from your Windows PC
   - Test with: `curl http://richard-XPS-15-9560.local:8892/health` in PowerShell
   - Or open `http://richard-XPS-15-9560.local:8892/health` in browser

### Step 1: Copy Files to Windows

Transfer the entire `openmemory-mcp` folder to your Windows PC. You can use:
- Network share
- USB drive
- Git clone (if you push this to a repo)
- Any file transfer method

Suggested location: `C:\Users\YourUsername\openmemory-mcp`

### Step 2: Install Python Dependencies

Open **PowerShell** or **Command Prompt** and navigate to the folder:

```powershell
cd C:\Users\YourUsername\openmemory-mcp
```

Install the package and dependencies:

```powershell
pip install -e .
```

This will install:
- `mcp` - Model Context Protocol SDK
- `httpx` - HTTP client for API calls
- `python-dotenv` - Environment variable management

### Step 3: Configure Claude Desktop

1. Locate your Claude Desktop configuration file:
   - Path: `%APPDATA%\Claude\claude_desktop_config.json`
   - Full path example: `C:\Users\YourUsername\AppData\Roaming\Claude\claude_desktop_config.json`

2. Open the file in a text editor (create it if it doesn't exist)

3. Add the OpenMemory MCP server configuration:

```json
{
  "mcpServers": {
    "openmemory": {
      "command": "python",
      "args": ["-m", "openmemory_mcp"],
      "env": {
        "OPENMEMORY_URL": "http://richard-XPS-15-9560.local:8892"
      }
    }
  }
}
```

**If you already have other MCP servers configured**, add the `openmemory` entry to the existing `mcpServers` object:

```json
{
  "mcpServers": {
    "existing-server": {
      "command": "...",
      "args": ["..."]
    },
    "openmemory": {
      "command": "python",
      "args": ["-m", "openmemory_mcp"],
      "env": {
        "OPENMEMORY_URL": "http://richard-XPS-15-9560.local:8892"
      }
    }
  }
}
```

4. Save the file

### Step 4: Restart Claude Desktop

1. Completely quit Claude Desktop (check system tray)
2. Restart Claude Desktop
3. The MCP server should now be available

## Testing

### Test 1: Network Connectivity

From Windows PowerShell, verify you can reach the OpenMemory API:

```powershell
curl http://richard-XPS-15-9560.local:8892/health
```

Expected response:
```json
{"status": "ok", "timestamp": "..."}
```

### Test 2: MCP Server in Claude Desktop

In Claude Desktop, try asking:

> "Can you check if OpenMemory is healthy?"

Claude should use the `health_check` tool and report success.

### Test 3: Search Memories

> "Search my memories for 'dashboard'"

### Test 4: Add Memory

> "Add a memory: 'Configured OpenMemory MCP server on Windows' to the semantic sector"

## Troubleshooting

### "Cannot connect to OpenMemory API"

1. Check network connectivity from Windows:
   ```powershell
   ping richard-XPS-15-9560.local
   curl http://richard-XPS-15-9560.local:8892/health
   ```

2. Verify OpenMemory container is running on Ubuntu:
   ```bash
   docker ps | grep openmemory
   docker logs openmemory
   ```

3. Check firewall settings on both Windows and Ubuntu

### "Python not found" or "Module not found"

1. Verify Python is installed:
   ```powershell
   python --version
   ```

2. Reinstall dependencies:
   ```powershell
   cd C:\Users\YourUsername\openmemory-mcp
   pip install -e . --force-reinstall
   ```

### MCP Server Not Showing in Claude Desktop

1. Check the config file path is correct:
   - `%APPDATA%\Claude\claude_desktop_config.json`

2. Verify JSON syntax is valid (no trailing commas, proper quotes)

3. Check Claude Desktop logs (if available)

4. Completely quit and restart Claude Desktop

### Memory Sectors

OpenMemory uses hierarchical memory sectors:

- **episodic** - Event-based memories (what happened)
- **semantic** - Conceptual knowledge (facts, concepts)
- **procedural** - How-to information (processes, workflows)
- **emotional** - User preferences, sentiment
- **reflective** - Meta-learnings, insights

When adding memories, choose the most appropriate sector.

## Development

### Running Server Manually (for testing)

```powershell
cd C:\Users\YourUsername\openmemory-mcp
python -m openmemory_mcp
```

The server will run in stdio mode and wait for MCP protocol messages.

### Project Structure

```
openmemory-mcp/
├── pyproject.toml              # Package configuration
├── README.md                   # This file
├── .env.example                # Environment template
└── src/
    └── openmemory_mcp/
        ├── __init__.py         # Package entry point
        ├── __main__.py         # CLI entry point
        ├── client.py           # OpenMemory API client
        └── server.py           # MCP server implementation
```

## Advanced Configuration

### Using API Key Authentication

If your OpenMemory API requires authentication:

1. Set the API key in Claude Desktop config:

```json
{
  "mcpServers": {
    "openmemory": {
      "command": "python",
      "args": ["-m", "openmemory_mcp"],
      "env": {
        "OPENMEMORY_URL": "http://richard-XPS-15-9560.local:8892",
        "OPENMEMORY_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Using Custom OpenMemory URL

If your OpenMemory runs on a different host/port, update the URL:

```json
"env": {
  "OPENMEMORY_URL": "http://different-host:8892"
}
```

## Support

For issues:
1. Check the troubleshooting section above
2. Verify OpenMemory API is working directly (curl/browser)
3. Check Claude Desktop and MCP server logs
4. Ensure Python dependencies are correctly installed

## License

MIT
