# Restoring 2010s Drupal 5 blog to modern tech stack

Overall Goal:

- Migrate my historic blog entries to a static site generator (probably Hugo)

Situation:

- Old Mysql 5.x backups containing a Drupal 5 blog (2010s era)
- Mysql 5.x backups do not cleanly restore in Mysql 8

Nice to haves:

- We want to convert to Sqlite3 to remove need for a DB server for future archive work

## Restoring MySQL 5.5 backups in 202X

```bash
docker compose up mysql5 -d
export MYSQL5_PORT=3307
# Create the DB
mysql -h 127.0.0.1 -u root -P $MYSQL5_PORT -p -e  "create database drupal_5_mysql5"
# Restore the backup
mysql -h 127.0.0.1 -u root -P $MYSQL5_PORT -p drupal_5_mysql5 < drupal_5_mysql5.mysql
```
