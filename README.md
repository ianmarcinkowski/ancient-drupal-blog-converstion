# Restoring 2010s Drupal 5 blog to modern tech stack

Overall Goal:

- Migrate my historic blog entries to Hugo static site generator

Situation:

- Old Mysql 5.x backups containing a Drupal 5 blog (2010s era)
- Mysql 5.x backups do not cleanly restore in Mysql 8
- I have a few comments worth preserving from my old threads in Drupal
- I have ~19,000 spam commnets to sift through

Nice to haves/Stretch goals:

- We want to convert to Sqlite3 to remove need for a DB server for future archive work
- Filtering comments using a local LLM like Llama 3.2, Gemma3 or Deepseek

## Restoring MySQL 5.5 backups in 202X

```bash
docker compose up mysql5 -d
export MYSQL5_PORT=3307
# Create the DB
mysql -h 127.0.0.1 -u root -P $MYSQL5_PORT -p -e  "create database drupal_5_mysql5"
# Restore the backup
mysql -h 127.0.0.1 -u root -P $MYSQL5_PORT -p drupal_5_mysql5 < drupal_5_mysql5.mysql
```

## Filtering comments

The Drupal `comment` and `field_data_comment_body` tables combine to provide a full
view of a comment.  Comment metadata comes from `comment` and the content comes
from the field data table.

Page/node entity metadata and content can be found in the `node` table and joined
appropriately as well.  For spam filtering, it could be reasonable to include the
page/blog post comment in the LLM prompt to check for relevancy of the comments.

```
±:% python filter_comments.py --user root --port 3307 --password yourrootpassword --database drupal5 --language-model gemma3 --num-records 222
Processing comment: 'Make sure overflow openings'█████████████████████            | 167/222 [00:54<00:13,  4.01it/s]

=== Performance Summary ===
Model: gemma3

=== Performance Statistics ===
Total comments processed: 222
Total execution time: 68.578 seconds
Average time per comment: 0.309 seconds
Average content length: 2065.57 characters
Min execution time: 0.129 seconds
Max execution time: 5.156 seconds

Correlation between content length and execution time: 0.284

=== Classification Results ===
SPAM: 221 (99.5%)
NOT_SPAM: 1 (0.5%)

=== Detailed Results ===
     Comment ID  Length  Execution Time (s) Result
0             1    2292            5.156385   SPAM
1             2     201            0.150618   SPAM
2             3    1866            0.330929   SPAM
3             4     552            0.235011   SPAM
4             5    1450            0.244858   SPAM
..          ...     ...                 ...    ...
217         218    3206            0.345273   SPAM
218         219     498            0.160085   SPAM
219         220     293            0.146631   SPAM
220         221     477            0.147226   SPAM
221         222     126            0.140946   SPAM
```