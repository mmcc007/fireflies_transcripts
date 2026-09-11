#!/usr/bin/env python3
"""
Fireflies.ai Transcript Downloader
Download transcripts from Fireflies.ai using their GraphQL API
"""

import requests
import json
import argparse
import os
import re
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class FirefliesClient:
    """Client for interacting with Fireflies.ai GraphQL API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://api.fireflies.ai/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.endpoint,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def list_transcripts(self) -> List[Dict]:
        """List all available transcripts"""
        query = """
        query {
            transcripts {
                id
                title
                date
                duration
            }
        }
        """
        result = self._execute_query(query)
        return result.get("data", {}).get("transcripts", [])

    def get_transcript(self, transcript_id: str, include_summary: bool = True) -> Dict:
        """
        Get full transcript details including sentences and summary

        Args:
            transcript_id: The transcript ID
            include_summary: Whether to include AI-generated summary
        """
        summary_fields = """
            summary {
                keywords
                action_items
                overview
            }
        """ if include_summary else ""

        query = f"""
        query {{
            transcript(id: "{transcript_id}") {{
                id
                title
                date
                transcript_url
                duration
                sentences {{
                    text
                    speaker_name
                    start_time
                    end_time
                }}
                speakers {{
                    id
                    name
                }}
                {summary_fields}
            }}
        }}
        """
        result = self._execute_query(query)
        return result.get("data", {}).get("transcript", {})

    def save_transcript_to_file(self, transcript_id: str, output_file: str, format: str = "txt"):
        """
        Save transcript to a file

        Args:
            transcript_id: The transcript ID
            output_file: Path to output file
            format: Output format ('txt', 'json', or 'srt')
        """
        transcript = self.get_transcript(transcript_id)

        if not transcript:
            print(f"Error: Transcript {transcript_id} not found")
            return False

        if format == "json":
            with open(output_file, 'w') as f:
                json.dump(transcript, f, indent=2)

        elif format == "txt":
            with open(output_file, 'w') as f:
                # Write header
                f.write(f"Title: {transcript['title']}\n")
                f.write(f"Date: {datetime.fromtimestamp(transcript['date']/1000).strftime('%Y-%m-%d %H:%M:%S')}\n")
                # Fireflies reports `duration` in MINUTES (measured 2026-09-11: a
                # 47-minute call carries 48.42; a 62-minute one carries 63.41).
                f.write(f"Duration: {transcript['duration']:.2f} minutes\n")
                f.write(f"URL: {transcript['transcript_url']}\n")
                f.write("\n" + "="*80 + "\n\n")

                # Write summary if available
                if transcript.get('summary'):
                    summary = transcript['summary']
                    if summary.get('overview'):
                        f.write("SUMMARY:\n")
                        f.write(summary['overview'] + "\n\n")

                    if summary.get('keywords'):
                        f.write("KEYWORDS:\n")
                        f.write(", ".join(summary['keywords']) + "\n\n")

                    if summary.get('action_items'):
                        f.write("ACTION ITEMS:\n")
                        f.write(summary['action_items'] + "\n\n")

                    f.write("="*80 + "\n\n")

                # Write transcript
                f.write("TRANSCRIPT:\n\n")
                for sentence in transcript['sentences']:
                    timestamp = f"[{sentence['start_time']:.2f}s]"
                    f.write(f"{timestamp} {sentence['speaker_name']}: {sentence['text']}\n")

        elif format == "srt":
            # SRT subtitle format
            with open(output_file, 'w') as f:
                for i, sentence in enumerate(transcript['sentences'], 1):
                    start_time = self._format_srt_time(sentence['start_time'])
                    end_time = self._format_srt_time(sentence['end_time'])

                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{sentence['speaker_name']}: {sentence['text']}\n\n")

        return True

    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds as SRT timestamp (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def extract_transcript_id(url_or_id: str) -> str:
    """
    Extract transcript ID from URL or return ID if already in correct format

    Examples:
        https://app.fireflies.ai/view/Meeting-Title::TRANSCRIPT_ID_HERE
        https://app.fireflies.ai/view/TRANSCRIPT_ID_HERE
        TRANSCRIPT_ID_HERE
    """
    # If it's a URL, extract the ID
    if url_or_id.startswith('http'):
        # Match pattern like: /view/anything::ID or /view/ID
        match = re.search(r'/view/(?:.*::)?([A-Z0-9]+)$', url_or_id)
        if match:
            return match.group(1)
        # Try to get the last part after /view/
        parts = url_or_id.rstrip('/').split('/')
        if len(parts) >= 2:
            last_part = parts[-1]
            # If it contains ::, get the part after it
            if '::' in last_part:
                return last_part.split('::')[-1]
            return last_part

    # Otherwise assume it's already an ID
    return url_or_id


def download_transcript(client: FirefliesClient, url_or_id: str, output_dir: str, formats: List[str]):
    """Download a single transcript"""
    transcript_id = extract_transcript_id(url_or_id)

    print(f"Downloading transcript: {transcript_id}")

    # Get transcript info first
    try:
        transcript = client.get_transcript(transcript_id)
        if not transcript:
            print(f"Error: Transcript not found")
            return False

        title = transcript['title']
        date_str = datetime.fromtimestamp(transcript['date']/1000).strftime('%Y-%m-%d')

        # Create safe filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]
        filename_base = f"{date_str}_{safe_title}_{transcript_id}"

        print(f"Title: {title}")
        print(f"Date: {date_str}")
        print(f"Saving to: {output_dir}/")

        # Download in requested formats
        for fmt in formats:
            output_file = os.path.join(output_dir, f"{filename_base}.{fmt}")
            client.save_transcript_to_file(transcript_id, output_file, format=fmt)
            print(f"  ✓ {filename_base}.{fmt}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def download_all_transcripts(client: FirefliesClient, output_dir: str, formats: List[str]):
    """Download all transcripts"""
    print("Fetching transcript list...")
    transcripts = client.list_transcripts()
    print(f"Found {len(transcripts)} transcripts\n")

    success_count = 0
    for i, t in enumerate(transcripts, 1):
        transcript_id = t['id']
        title = t['title']
        date_str = datetime.fromtimestamp(t['date']/1000).strftime('%Y-%m-%d')

        # Create safe filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]
        filename_base = f"{date_str}_{safe_title}_{transcript_id}"

        print(f"[{i}/{len(transcripts)}] {title} ({date_str})")

        try:
            # Save in requested formats
            for fmt in formats:
                output_file = os.path.join(output_dir, f"{filename_base}.{fmt}")
                client.save_transcript_to_file(transcript_id, output_file, format=fmt)
                print(f"  ✓ {filename_base}.{fmt}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            continue

    print(f"\nDone! Downloaded {success_count}/{len(transcripts)} transcripts to: {output_dir}/")


def list_transcripts(client: FirefliesClient):
    """List all available transcripts"""
    transcripts = client.list_transcripts()
    print(f"Found {len(transcripts)} transcripts:\n")

    for t in transcripts:
        date_str = datetime.fromtimestamp(t['date']/1000).strftime('%Y-%m-%d %H:%M')
        duration_min = t['duration'] or 0   # already minutes — dividing by 60 printed a 47-min call as 0.8
        print(f"  {t['id']}")
        print(f"    Title: {t['title']}")
        print(f"    Date: {date_str}")
        print(f"    Duration: {duration_min:.1f} min")
        print(f"    URL: https://app.fireflies.ai/view/{t['id']}")
        print()


def load_env_file():
    """Load .env file if it exists"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value


def main():
    # Load .env file if present
    load_env_file()

    parser = argparse.ArgumentParser(
        description='Download transcripts from Fireflies.ai',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all transcripts
  %(prog)s --list

  # Download specific transcript by ID
  %(prog)s --id TRANSCRIPT_ID_HERE

  # Download specific transcript by URL
  %(prog)s --url "https://app.fireflies.ai/view/Meeting-Title::TRANSCRIPT_ID_HERE"

  # Download all transcripts
  %(prog)s --all

  # Download in specific formats
  %(prog)s --all --format txt json

  # Download to specific directory
  %(prog)s --all --output my_transcripts/

  # Use custom API key
  %(prog)s --all --api-key YOUR_API_KEY
        """
    )

    parser.add_argument('--api-key',
                        default=os.environ.get('FIREFLIES_API_KEY'),
                        help='Fireflies.ai API key (or set FIREFLIES_API_KEY env var)')

    parser.add_argument('--output', '-o',
                        default='transcripts',
                        help='Output directory (default: transcripts/)')

    parser.add_argument('--format', '-f',
                        nargs='+',
                        choices=['txt', 'json', 'srt'],
                        default=['txt', 'json', 'srt'],
                        help='Output formats (default: txt json srt)')

    # Action group - only one can be specified
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--list', '-l',
                             action='store_true',
                             help='List all available transcripts')

    action_group.add_argument('--all', '-a',
                             action='store_true',
                             help='Download all transcripts')

    action_group.add_argument('--id',
                             help='Download transcript by ID')

    action_group.add_argument('--url',
                             help='Download transcript by URL')

    args = parser.parse_args()

    # Check if API key is provided
    if not args.api_key:
        parser.error("API key required. Set FIREFLIES_API_KEY environment variable or use --api-key")

    # Initialize client
    client = FirefliesClient(args.api_key)

    # Create output directory if needed
    if not args.list:
        os.makedirs(args.output, exist_ok=True)

    # Execute requested action
    if args.list:
        list_transcripts(client)
    elif args.all:
        download_all_transcripts(client, args.output, args.format)
    elif args.id:
        download_transcript(client, args.id, args.output, args.format)
    elif args.url:
        download_transcript(client, args.url, args.output, args.format)


if __name__ == "__main__":
    main()
