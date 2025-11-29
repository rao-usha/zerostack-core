# Multiple Databases Setup for Data Explorer

## How to Add Multiple Databases

The Data Explorer now supports multiple database connections! You can switch between them using a dropdown.

### Environment Variable Pattern

For each database you want to add, use this pattern:

**Database 1 (Default):**
```bash
EXPLORER_DB_HOST=host.docker.internal
EXPLORER_DB_PORT=5433
EXPLORER_DB_USER=nexdata
EXPLORER_DB_PASSWORD=nexdata_dev_password
EXPLORER_DB_NAME=nexdata
```

**Database 2:**
```bash
EXPLORER_DB_2_HOST=host.docker.internal
EXPLORER_DB_2_PORT=5434
EXPLORER_DB_2_USER=username2
EXPLORER_DB_2_PASSWORD=password2
EXPLORER_DB_2_NAME=database2name
```

**Database 3:**
```bash
EXPLORER_DB_3_HOST=host.docker.internal
EXPLORER_DB_3_PORT=5435
EXPLORER_DB_3_USER=username3
EXPLORER_DB_3_PASSWORD=password3
EXPLORER_DB_3_NAME=database3name
```

And so on up to EXPLORER_DB_5_*.

### Add to docker-compose.dev.yml

In your `docker-compose.dev.yml`, add all these environment variables to the backend service:

```yaml
  backend:
    environment:
      # ... existing vars ...
      
      # Database 1 (default) - nexdata on port 5433
      - EXPLORER_DB_HOST=host.docker.internal
      - EXPLORER_DB_PORT=5433
      - EXPLORER_DB_USER=nexdata
      - EXPLORER_DB_PASSWORD=nexdata_dev_password
      - EXPLORER_DB_NAME=nexdata
      
      # Database 2 - Add your second database here
      - EXPLORER_DB_2_HOST=host.docker.internal
      - EXPLORER_DB_2_PORT=5432  # or whatever port
      - EXPLORER_DB_2_USER=nex
      - EXPLORER_DB_2_PASSWORD=nex
      - EXPLORER_DB_2_NAME=nex
      
      # Database 3 - Add your third database
      - EXPLORER_DB_3_HOST=host.docker.internal
      - EXPLORER_DB_3_PORT=5434
      - EXPLORER_DB_3_USER=youruser
      - EXPLORER_DB_3_PASSWORD=yourpassword
      - EXPLORER_DB_3_NAME=yourdb
      
      # Add more as needed (up to DB_5)
```

### Example for Your .env Lines 4-13

If your .env has databases like:
```
Line 4: EXPLORER_DB_HOST=localhost
Line 5: EXPLORER_DB_PORT=5433
Line 6: EXPLORER_DB_USER=nexdata
Line 7: EXPLORER_DB_PASSWORD=nexdata_dev_password
Line 8: EXPLORER_DB_NAME=nexdata
Line 9: DB2_HOST=localhost
Line 10: DB2_PORT=5434
Line 11: DB2_USER=someuser
Line 12: DB2_PASSWORD=somepass
Line 13: DB2_NAME=somedb
```

You would add to docker-compose:
```yaml
      - EXPLORER_DB_HOST=host.docker.internal
      - EXPLORER_DB_PORT=5433
      - EXPLORER_DB_USER=nexdata
      - EXPLORER_DB_PASSWORD=nexdata_dev_password
      - EXPLORER_DB_NAME=nexdata
      
      - EXPLORER_DB_2_HOST=host.docker.internal
      - EXPLORER_DB_2_PORT=5434
      - EXPLORER_DB_2_USER=someuser
      - EXPLORER_DB_2_PASSWORD=somepass
      - EXPLORER_DB_2_NAME=somedb
```

## Quick Setup

1. Copy the database info from your .env file
2. Add environment variables to `docker-compose.dev.yml` backend service
3. Restart backend: `docker-compose -f docker-compose.dev.yml up -d backend`
4. Refresh the Data Explorer page
5. You'll see a database dropdown at the top!

## Need Help?

Share lines 4-13 from your .env file and I'll create the exact configuration for you!

