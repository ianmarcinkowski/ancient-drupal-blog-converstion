import argparse
import mysql.connector
from ollama import Client
import time
from prettytable import PrettyTable
import pandas as pd

DRUPAL_COMMENTS_ONLY_QUERY = """
SELECT
  c.subject as comment_subject,
  c.name as comment_username,
  c.mail as comment_user_email,
  c.homepage as comment_user_homepage_url,
  cf.comment_body_value as comment_content
FROM node_revision r
LEFT JOIN comment c on c.nid = r.nid
LEFT JOIN field_data_comment_body cf on c.cid = cf.entity_id
WHERE
  cf.comment_body_value is not null
"""

DRUPAL_NODES_AND_COMMENTS_QUERY = """
SELECT
    r.title AS node_title,
    r.status AS node_status,
    n.created AS node_created,
    n.changed AS node_changed,
    r.title AS blog_title,
    fr.body_value AS blog_post_body,
    r.timestamp AS revision_timestamp,
FROM node_revision r
JOIN node n on r.nid = n.nid
JOIN field_revision_body fr on fr.revision_id = r.vid
LEFT JOIN comment c on c.nid = r.nid
LEFT JOIN field_data_comment_body cf on c.cid = cf.entity_id
ORDER BY r.nid, r.timestamp DESC
"""


def fetch_records(db_config, query, limit=None):
    # Connect to the database
    if limit:
        query += f"\nLIMIT {limit}"

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Query to select all records from the specified table
    cursor.execute(query)

    # Fetch all records
    records = cursor.fetchall()
    cursor.close()
    return records


EVALUATION_PROMPT = """
You are evaluating blog comments to detect spam. Analyze the following comment and determine if it's spam.

Comment details:
- Subject: {}
- Username: {}
- Email: {}
- Homepage URL: {}
- Content: {}

Look for these spam indicators:
1. Excessive or irrelevant links
2. Generic, unrelated content
3. Promotional language unrelated to the post
4. Suspicious URLs or email patterns
5. Mismatched username/email combinations
6. Nonsensical text or keyword stuffing

Respond with ONLY ONE of these two statements:
- "SPAM" if you determine this is likely spam
- "NOT_SPAM" if you believe this is a legitimate comment

Your analysis:
"""


def evaluate_comment(comment_record, ollama_client, model):
    (comment, username, user_email, homepage_url, content) = comment_record
    prompt = EVALUATION_PROMPT.format(
        comment, username, user_email, homepage_url, content
    )
    # Start with a carriage return to overwrite the previous line
    print(f"\rProcessing comment: '{comment[:30]}'", end="\r")
    response = ollama_client.generate(model=model, prompt=prompt)
    result = response["response"].strip()
    return result


def main(db_config, ollama_client, model):
    try:
        comments = fetch_records(db_config, DRUPAL_COMMENTS_ONLY_QUERY, limit=20)
    except mysql.connector.errors.Error as exc:
        print(f"Error fetching records: {exc}")
        exit(1)

    results_table = PrettyTable()
    results_table.field_names = ["Comment ID", "Length", "Execution Time (s)", "Result"]

    # Create a list of values and construct the Dataframe at the end
    performance_data = []
    for i, comment in enumerate(comments):
        content_length = len(comment[4]) if comment[4] else 0

        # Measure execution time
        start_time = time.time()
        result = evaluate_comment(comment, ollama_client, model=model)
        execution_time = time.time() - start_time

        # Add row to table
        results_table.add_row([i + 1, content_length, f"{execution_time:.3f}", result])
        performance_data.append([i + 1, content_length, execution_time, result])

        # # Add data to results_df
        # results_df = pd.concat([results_df, pd.DataFrame({
        #     "Comment ID": [i + 1],
        #     "Length": [content_length],
        #     "Execution Time (s)": [execution_time],
        #     "Result": [result]
        # })], ignore_index=True)

    # Create a pretty table for output
    # Initialize an empty DataFrame to store results
    results_df = pd.DataFrame(performance_data, columns=["Comment ID", "Length", "Execution Time (s)", "Result"])

    # Print performance summary
    print("\n=== Performance Summary ===")
    print(f"Model: {model}")
    # Get statistics from the DataFrame
    comment_count = len(results_df)
    total_time = results_df['Execution Time (s)'].sum()

    # Generate statistics from the DataFrame
    print("\n=== Performance Statistics ===")
    print(f"Total comments processed: {comment_count}")
    print(f"Total execution time: {total_time:.3f} seconds")
    print(f"Average time per comment: {(total_time/comment_count):.3f} seconds")
    print(f"Average content length: {results_df['Length'].mean():.2f} characters")
    print(f"Min execution time: {results_df['Execution Time (s)'].min():.3f} seconds")
    print(f"Max execution time: {results_df['Execution Time (s)'].max():.3f} seconds")

    # Count spam vs non-spam
    result_counts = results_df['Result'].value_counts()
    print("\n=== Classification Results ===")
    for result_type, count in result_counts.items():
        print(f"{result_type}: {count} ({count/comment_count*100:.1f}%)")

    # Show correlation between content length and execution time
    correlation = results_df['Length'].corr(results_df['Execution Time (s)'])
    print(f"\nCorrelation between content length and execution time: {correlation:.3f}")

    print("\n=== Detailed Results ===")
    print(results_table)
    print(results_df)


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
    parser.add_argument("--ollama-host", default="127.0.0.1", help="Ollama Host")
    parser.add_argument("--ollama-port", default="11434", help="Ollama Port")
    parser.add_argument(
        "--language-model", required=True, help="LLM model for filtering"
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

    ollama_uri = f"{args.ollama_host}:{args.ollama_port}"
    ollama_client = Client(host=ollama_uri)

    main(db_config, ollama_client, args.language_model)
