This script monitors RSS feeds and can send new entries as Jabber messages or execute pre-defined command against links in new messages on the feed. It designed specifically with Youtube RSS in mind, but might also work with other feeds.

## Installation

It should work with Python version 3.6 and higher.

Clone or unzip this repo to appropriate folder.

Install dependencies from requirements file:

```bash
pip3 install --user -r requirements.txt
```

## Configuration

Settings are stored in `YAML` format in `config.yml`. As a starting poing, `config.yml.example` is provided. Rename it to `config.yml` and adapt for your needs.

### Common options:
- `loglevel`: how detailed script messages should be. Can be "DEBUG", "INFO" or "WARNING"
- `ua`: useragent to make requests with. If not specified default from urllib is used.
- `db_path`: to preserve state between runs, all messages from RSS feeds are stored in a file. Can be ommited.
- `update_interval`: how often RSS feeds should be updated in minutes.
- `send_interval`: how often pending Jabber notifications will be send in minutes.
- `xmpp_username` and `xmpp_pass`: Jabber credentials to send notifications from
- `download_command`: command that will be executed to download url from feed. Placeholder `{url}` will be replaced with url field from RSS feed message. Command will be executed as subprocess, so typical shell commands characters won't work.

### Feeds section:

```yaml
feeds:
  feed1: "url1"
  feed2: "url2"
```

Names such as `feed1` are arbitrary and used in `users` section.
Currently, url for RSS feed on Youtube channel is `https://www.youtube.com/feeds/videos.xml?channel_id=...`.

### Users section:

Common structure: 

```yaml
users:
  username1:
    ...
  username2:
    ...

  usernameN:
    ...
```

Possible options for specific user:

- `xmpp_username`: JID to send messages about feeds listed in actions for this user
- `timezone_offset`: used to recalculate timestamps to local time in Jabber messages. All timestamps are internally stored in UTC

```yaml
users:
  username1:
    xmpp_username: "username1@exmple.com"
    timezone_offset: -7
    feeds:
      - feed1:
        ...
      - feed2:
        ...
```

Options for `feeds` section of specific user:

- `save_path`: work directory for `download_command` subprocess when called for this specific feed and user
- `send_errors`: send Jabber message to user if `download_command` subprocess finished with non-zero exit code
- `actions`: how to handle new entries on RSS feed for specific user
- `filter`: only process entry if it has specified pattern in it, case-insensitive

```yaml
users:
  username1:
    xmpp_username: "username1@exmple.com"
    feeds:
      - feed1:
          actions:
            - send_any
            - download_any
          filter:
            - "archive"
            - "sing"
          save_path: "absolute/path/to/store/files/"
          send_errors: true
```

Possible `actions`:

- `send_any`: send user Jabber message about new entry in RSS feed
- `send_unarchived`: same as above, but only if title has `archive` in it
- `download_any`: start downlad subprocess for an url from new entry in RSS feed
- `download_unarchived`: same as above, but only if title has `archive` in it

Note, that it's possible to have multiple sets of feed options for a single link by specifying same feed twice:

```yaml
users:
  username1:
    xmpp_username: "username1@exmple.com"
    feeds:
      - feed1:
          actions:
            - send_any
      - feed1:
          filter:
            - "unarchived"
          actions:
            - download_any
          save_path: "absolute/path/to/store/files/"
```


## Running

Start `rss2jbr` module with your python interpreter.
```sh
python3 rss2jbr
```
