"""Start the web API server."""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.session_manager import SessionManager
from web.api import run_api

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    # Initialize session manager
    db_path = Path("data/promirror.db")
    session_manager = SessionManager(db_path)
    
    # Run API server
    run_api(session_manager, host="127.0.0.1", port=5000, debug=True)


if __name__ == "__main__":
    main()

