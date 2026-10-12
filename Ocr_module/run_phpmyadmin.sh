#!/bin/bash
# Start phpMyAdmin — the web interface for browsing the MariaDB database.
#
# macOS equivalent of clicking "Admin" next to MySQL in XAMPP's control
# panel. XAMPP's bundled Apache is Intel-only and cannot run on Apple
# Silicon, so PHP's own built-in web server is used instead. The page and
# the database behind it are identical to the Windows setup.
#
#   ./run_phpmyadmin.sh      then open http://127.0.0.1:8080
#
# Leave this window open while using it; press Ctrl+C to stop.

PMA_DIR="/opt/homebrew/share/phpmyadmin"
PORT=8080

if [ ! -f "$PMA_DIR/index.php" ]; then
  echo "phpMyAdmin not found at $PMA_DIR"
  echo "Install it with:  brew install php phpmyadmin"
  exit 1
fi

if ! /opt/homebrew/bin/mariadb -u root -h 127.0.0.1 -e "SELECT 1" >/dev/null 2>&1; then
  echo "Cannot reach MariaDB on 127.0.0.1:3306."
  echo "Start it with:  brew services start mariadb"
  exit 1
fi

echo
echo "  phpMyAdmin is starting."
echo "  Open:     http://127.0.0.1:$PORT"
echo "  Username: root"
echo "  Password: (leave blank)"
echo
echo "  Press Ctrl+C to stop."
echo

exec php -S "127.0.0.1:$PORT" -t "$PMA_DIR"
