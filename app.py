import os
import sys
from app import create_app

try:
    app = create_app()
except Exception as e:
    print(f"❌ Error during app creation: {e}", file=sys.stderr)
    raise

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)