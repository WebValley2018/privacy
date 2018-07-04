# SQL queries run on the DB starting from a fresh installation

Below are all the queries ran on the database in order to set it up

```sql
CREATE USER Tovel IDENTIFIED BY 'tovelwaterdoggo';
GRANT ALL PRIVILEGES ON *.* TO 'Tovel';
CREATE DATABASE Tovel CHARACTER SET utf8 COLLATE utf8_bin;
CREATE TABLE `Token` (
  `TokenValue` text COLLATE utf8_bin NOT NULL,
  `TTL` int(11) NOT NULL,
  `CreationDate` bigint(20) NOT NULL,
  `User` text COLLATE utf8_bin NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
CREATE TABLE `Users` (
  `Name` text COLLATE utf8_bin NOT NULL,
  `Surname` text COLLATE utf8_bin NOT NULL,
  `Mail` text COLLATE utf8_bin NOT NULL,
  `ID` text COLLATE utf8_bin NOT NULL,
  `Salt` text COLLATE utf8_bin NOT NULL,
  `Organization` text COLLATE utf8_bin NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
create table Sessions(ID text not null, UserID text not null, CreationDate Integer not null, ExpirationDate Integer not null);
```