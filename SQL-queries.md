# SQL queries run on the DB starting from a fresh installation

Below are all the queries ran on the database in order to set it up

```sql
CREATE USER Tovel IDENTIFIED BY 'tovelwaterdoggo';
GRANT ALL PRIVILEGES ON *.* TO 'Tovel';
CREATE DATABASE Tovel CHARACTER SET utf8 COLLATE utf8_bin;
```