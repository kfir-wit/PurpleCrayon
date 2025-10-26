# Utility Scripts

This directory contains standalone utility scripts for the PurpleCrayon project.

## Available Scripts

### 1. Image Cleanup Script
**File**: `cleanup_corrupted_images.py`
**Purpose**: Clean up corrupted or invalid image files in a directory

**Usage**:
```bash
# Clean up corrupted images in downloads/downloaded/
uv run python -m src.utils.cleanup_corrupted_images downloads/downloaded/

# Clean up corrupted images in assets/ai/
uv run python -m src.utils.cleanup_corrupted_images assets/ai/
```

**Features**:
- Validates image file integrity
- Removes files that are too small (< 10x10 pixels)
- Removes corrupted image files
- Provides detailed cleanup statistics

### 2. Catalog Update Script
**File**: `update_catalog.py`
**Purpose**: Manually update the asset catalog without running the full agent

**Usage**:
```bash
# Update the asset catalog
uv run python -m src.utils.update_catalog
```

**Features**:
- Rescans the assets directory
- Updates catalog with new files
- Removes orphaned entries
- Shows current catalog statistics

## Integration with Main Project

These scripts are designed to work alongside the main agent workflow:

- **After scraping**: Use cleanup script to remove corrupted images
- **After manual file additions**: Use catalog update script to index new files
- **Maintenance**: Use both scripts for regular asset management

## Error Handling

Both scripts include comprehensive error handling:
- Validates input paths and directories
- Provides clear error messages
- Shows detailed statistics and results
- Graceful handling of file system errors
