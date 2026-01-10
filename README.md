# Fireflies.ai Transcript Downloader

Download transcripts from Fireflies.ai using their GraphQL API.

## What Works with Free Account

✅ **Available:**
- Full transcript text with timestamps
- Speaker names and identification
- AI-generated summaries
- Keywords extraction
- Action items
- All transcript metadata

❌ **Requires Paid Plan:**
- Audio file downloads (Pro+ plan)
- Video file downloads (Business+ plan)

## Quick Start

First, get your Fireflies.ai API key:
1. Log in to [Fireflies.ai](https://fireflies.ai/)
2. Go to Settings → Integrations → API
3. Copy your API key

**Option 1: Use .env file (recommended)**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
nano .env

# Now you can use the script without --api-key flag
./fireflies.py --list

# Download a specific transcript by URL
./fireflies.py --url "https://app.fireflies.ai/view/Meeting-Title::TRANSCRIPT_ID_HERE"

# Download all transcripts
./fireflies.py --all
```

**Option 2: Use environment variable**
```bash
export FIREFLIES_API_KEY="your-api-key-here"
./fireflies.py --list
```

**Option 3: Pass API key directly**
```bash
./fireflies.py --api-key "your-api-key-here" --list
```

## Installation

```bash
# Install Python requests library (if not already installed)
pip install requests

# Or on Ubuntu/Debian
sudo apt-get install python3-requests

# Make script executable
chmod +x fireflies.py
```

## Usage

### List All Transcripts

```bash
./fireflies.py --list
```

Shows all your transcripts with:
- Transcript ID
- Title
- Date and time
- Duration
- Direct URL

### Download by URL

```bash
./fireflies.py --url "https://app.fireflies.ai/view/Meeting-Title::TRANSCRIPT_ID_HERE"
```

Copy the URL from your browser and paste it directly.

### Download by ID

```bash
./fireflies.py --id TRANSCRIPT_ID_HERE
```

Use the transcript ID from the URL or from `--list` output.

### Download All Transcripts

```bash
./fireflies.py --all
```

Downloads all your transcripts in all formats (txt, json, srt).

### Format Options

```bash
# Download only text format
./fireflies.py --all --format txt

# Download text and JSON
./fireflies.py --all --format txt json

# Download all formats (default)
./fireflies.py --all --format txt json srt
```

Available formats:
- **txt** - Human-readable with summary and transcript
- **json** - Complete structured data
- **srt** - Subtitle format for video editing

### Custom Output Directory

```bash
./fireflies.py --all --output my_transcripts/
```

## Output Format Examples

### TXT Format
```
Title: Meeting Title
Date: 2024-01-15 14:30:00
Duration: 3600.00 seconds
URL: https://app.fireflies.ai/view/TRANSCRIPT_ID_HERE

================================================================================

SUMMARY:
- Key point 1
- Key point 2

KEYWORDS:
keyword1, keyword2, keyword3

ACTION ITEMS:
- Action 1
- Action 2

================================================================================

TRANSCRIPT:

[226.80s] Speaker1: Text here
[232.01s] Speaker2: Response here
```

### SRT Format (Subtitles)
```
1
00:03:46,800 --> 00:03:48,400
Speaker1: Text here

2
00:03:52,010 --> 00:03:53,570
Speaker2: Response here
```

### JSON Format
Complete structured data including all metadata, speakers, sentences, and summary.

## API Key Configuration

You have three options to provide your API key:

**1. .env file (Recommended)**
```bash
cp .env.example .env
# Edit .env and add your API key
```

**2. Environment variable**
```bash
export FIREFLIES_API_KEY="your-api-key-here"
```

**3. Command line**
```bash
./fireflies.py --api-key "your-api-key-here" --list
```

### Getting Your API Key

1. Log in to [Fireflies.ai](https://fireflies.ai/)
2. Navigate to Settings → Integrations → API
3. Copy your API key

## Examples

```bash
# Assuming you've set up .env file with your API key

# List all meetings
./fireflies.py --list

# Download specific meeting by ID
./fireflies.py --id TRANSCRIPT_ID_HERE

# Download from URL (copied from browser)
./fireflies.py --url "https://app.fireflies.ai/view/Meeting-Title::TRANSCRIPT_ID_HERE"

# Download all meetings as text files only
./fireflies.py --all --format txt

# Download all meetings to a specific folder
./fireflies.py --all --output ~/Documents/meetings/

# Download specific meeting in JSON format
./fireflies.py --id TRANSCRIPT_ID_HERE --format json
```

## File Naming

Downloaded files are automatically named:
```
YYYY-MM-DD_Meeting_Title_TRANSCRIPT_ID.ext
```

For example:
```
2024-01-15_Product_Strategy_Meeting_01KEXAMPLEID123456789.txt
2024-01-15_Product_Strategy_Meeting_01KEXAMPLEID123456789.json
2024-01-15_Product_Strategy_Meeting_01KEXAMPLEID123456789.srt
```

## Help

```bash
./fireflies.py --help
```

## API Documentation

- Official Fireflies.ai API: https://docs.fireflies.ai/
- GraphQL endpoint: https://api.fireflies.ai/graphql
- Transcript query docs: https://docs.fireflies.ai/graphql-api/query/transcript

## Notes

- Free account has full access to transcript text and AI summaries
- Audio/video downloads require paid plans
- The script handles both URL formats:
  - `https://app.fireflies.ai/view/Title::ID`
  - `https://app.fireflies.ai/view/ID`
- Rate limits may apply (not documented for free tier)
- All timestamps are in your local timezone
