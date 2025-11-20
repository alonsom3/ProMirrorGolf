# Scripts Directory

Utility scripts for development, testing, and maintenance.

## Maintenance Scripts

### `find_missing_current_colors.py`

Finds methods that use `current_colors` but don't initialize it with `get_current_colors()`.

**Usage:**
```bash
python scripts/find_missing_current_colors.py
```

**Output:**
- Lists files and methods with missing `current_colors` initialization
- Helps ensure all code follows the theme system pattern

## Testing Scripts

### `test_all_features.py`

Comprehensive feature test suite that verifies:
- Data validation
- Cache management
- Duplicate detection
- Pagination
- Multi-monitor support
- Import functionality
- Enhanced table widgets

**Usage:**
```bash
python scripts/test_all_features.py
```

### `quick_test.py`

Quick verification script for basic functionality.

**Usage:**
```bash
python scripts/quick_test.py
```

### `test_migration.py`

Tests design system migration and theme functionality.

**Usage:**
```bash
python scripts/test_migration.py
```

## Performance Scripts

### `profile_performance.py`

Performance profiling script for identifying bottlenecks.

**Usage:**
```bash
python scripts/profile_performance.py
```

## Legacy Scripts

### `replace_colors.py`

⚠️ **Legacy Script** - No longer needed after theme migration completion.

This script was used during the migration from hardcoded colors to the design constants system. All migrations are now complete, but the script is kept for reference.

**Note:** All color replacements should now be done manually using `get_current_colors()` pattern.

