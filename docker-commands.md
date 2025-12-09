# Docker Commands for Wallet Passes Database

## Starting the Services

Start MariaDB and phpMyAdmin:
```bash
docker-compose up -d
```

## Accessing the Services

- **phpMyAdmin**: http://localhost:8080
  - Username: `root`
  - Password: `123456789`
  - Database: `wallet_passes`

- **MariaDB**: 
  - Host: `127.0.0.1`
  - Port: `3306`
  - Database: `wallet_passes`
  - Username: `root`
  - Password: `123456789`

## Useful Commands

### View running containers
```bash
docker-compose ps
```

### View logs
```bash
# All services
docker-compose logs -f

# MariaDB only
docker-compose logs -f mariadb

# phpMyAdmin only
docker-compose logs -f phpmyadmin
```

### Stop services
```bash
docker-compose down
```

### Stop and remove volumes (WARNING: deletes all data)
```bash
docker-compose down -v
```

### Restart services
```bash
docker-compose restart
```

### Execute SQL commands directly
```bash
docker-compose exec mariadb mysql -uroot -p123456789 wallet_passes
```

### Import SQL file
```bash
docker-compose exec -T mariadb mysql -uroot -p123456789 wallet_passes < your_file.sql
```

### Backup database
```bash
docker-compose exec mariadb mysqldump -uroot -p123456789 wallet_passes > backup.sql
```

## Initialization

The database schema from `database/schema.sql` will be automatically executed when the MariaDB container starts for the first time.

## Troubleshooting

### Port already in use
If port 3306 or 8080 is already in use, you can change the ports in `docker-compose.yml`:
```yaml
ports:
  - "3307:3306"  # Change host port to 3307
```

### Reset database
```bash
docker-compose down -v
docker-compose up -d
```

### Check MariaDB health
```bash
docker-compose exec mariadb healthcheck.sh --connect
```
