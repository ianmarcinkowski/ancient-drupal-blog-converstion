import mysql.connector
from datetime import datetime
import os
import argparse


DRUPAL_NODES_QUERY = """
SELECT
    n.nid AS node_id,
    r.title AS node_title,
    r.status AS node_status,
    n.created AS node_created,
    n.changed AS node_changed,
    r.title AS title,
    frb.body_value AS body,
    r.timestamp AS revision_timestamp
FROM node_revision r
JOIN node n on r.nid = n.nid
JOIN field_revision_body frb on frb.revision_id = r.vid
ORDER BY r.nid, r.timestamp DESC
"""


def save_markdown(filename, record):
    with open(filename, "w", encoding="utf-8") as mdfile:
        mdfile.write(record)


def create_safe_filename(title):
    """Convert title to a safe filename by replacing special characters."""
    safe_title = "".join(
        c if c.isalnum() or c in [" ", "-", "_"] else "_" for c in title
    )
    safe_title = safe_title.replace(" ", "-").lower().strip("-_")
    return safe_title


def fetch_comments(node_id):
    pass


def generate_markdown(record):
    (
        node_id,
        node_title,
        node_status,
        node_created,
        node_changed,
        title,
        body,
        revision_timestamp,
    ) = record
    postdate = datetime.fromtimestamp(revision_timestamp)
    date_string = postdate.strftime("%Y-%m-%dT%H:%M:%SZ")

    md_content = f"""
+++
title = "{title}"
date = "{date_string}"
#dateFormat = "2006-01-02" # This value can be configured for per-post date formatting
author = "Ian Marcinkowski"
cover = ""
showFullContent = false
readingTime = false
hideComments = false
+++

{body}
  """
    return md_content



# --user root --port 3307 --password rootpassword --database blog_2020 --output output/markdown
def extract_and_write_markdown(records, output_directory):
    posts = dict()
    for record in records:
        (
            node_id,
            node_title,
            node_status,
            node_created,
            node_changed,
            title,
            body,
            revision_timestamp,
        ) = record
        md_record = generate_markdown(record)
        # Store a dictionary of the posts
        if node_id not in posts:
            # We receive one row for each comment
            postdate = datetime.fromtimestamp(revision_timestamp)
            year = str(postdate.year)
            month = str(postdate.month)
            day = str(postdate.day)

            # Convert title to a safe filename
            safe_title = create_safe_filename(node_title)
            safe_markdown_filename = f"{safe_title}.md"
            directory_path = os.path.join(*[output_directory, year, month, day])
            os.makedirs(directory_path, exist_ok=True)
            file_path = os.path.join(*[directory_path, safe_markdown_filename])
            save_markdown(file_path, md_record)


if __name__ == "__main__":
    # Database connection parameters
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Extract Drupal blog posts as markdown files"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Database host")
    parser.add_argument("--port", required=True, help="Database port")
    parser.add_argument("--user", required=True, help="Database username")
    parser.add_argument("--password", required=True, help="Database password")
    parser.add_argument("--database", required=True, help="Database name")
    parser.add_argument(
        "--output",
        default="output/markdown",
        help="Output directory for markdown files",
    )

    args = parser.parse_args()

    # Database connection parameters from command line args
    db_config = {
        "host": args.host,
        "port": args.port,
        "user": args.user,
        "password": args.password,
        "database": args.database,
    }

    # Update target directory from args
    target_directory = args.output
    try:
        records = fetch_records(db_config)
    except mysql.connector.errors.Error as exc:
        print(f"Error fetching records: {exc}")
        exit(1)

    output_directory = args.output
    extract_and_write_markdown(records, output_directory)
