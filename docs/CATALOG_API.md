# PurpleCrayon Catalog API Documentation

## Overview

The Catalog API provides comprehensive asset management and organization capabilities. This feature allows you to create, update, search, and manage asset catalogs with detailed metadata, automatic organization, and powerful search capabilities across all your image assets.

## Core Concepts

### Asset Catalog System
1. **Metadata Storage**: Stores detailed information about each asset
2. **Automatic Organization**: Organizes assets by source and type
3. **Search Capabilities**: Powerful search across all metadata
4. **Statistics Tracking**: Comprehensive statistics and analytics
5. **Format Support**: Both YAML and JSON catalog formats
6. **Validation**: Ensures catalog integrity and consistency

### Asset Categories
- **AI Generated**: Images created using AI providers
- **Stock Photos**: Downloaded from stock photo providers
- **Downloaded**: Images scraped from websites
- **Cloned**: Royalty-free alternatives created from existing images
- **Proprietary**: User-provided or custom images

### Key Features
- **Multi-Format Support**: YAML and JSON catalog formats
- **Smart Organization**: Automatic categorization by source and content
- **Advanced Search**: Search by description, tags, dimensions, format
- **Statistics**: Comprehensive analytics and reporting
- **Validation**: Image validation and corruption detection
- **Cleanup**: Automatic cleanup of corrupted and junk files

## API Reference

### PurpleCrayon Class Methods

#### `sort_catalog()`
Sort and update the asset catalog with current files.

**Returns:**
- `Dict[str, Any]`: Dictionary containing success status and statistics

**Example:**
```python
from purplecrayon import PurpleCrayon

crayon = PurpleCrayon()

# Sort and update catalog
result = crayon.sort_catalog()

if result["success"]:
    print("Catalog updated successfully")
    print(f"Rename stats: {result['rename_stats']}")
    print(f"Catalog stats: {result['catalog_stats']}")
    print(f"Final stats: {result['final_stats']}")
else:
    print(f"Catalog update failed: {result['error']}")
```

#### `cleanup_assets(remove_junk=True, format="both")`
Clean up corrupted and junk images, then update catalog.

**Parameters:**
- `remove_junk` (bool, optional): Remove junk files (default: True)
- `format` (str, optional): Catalog format - "yaml", "json", "both" (default: "both")

**Returns:**
- `Dict[str, Any]`: Dictionary containing success status and cleanup statistics

**Example:**
```python
# Clean up assets and update catalog
result = crayon.cleanup_assets(remove_junk=True, format="both")

if result["success"]:
    print("Cleanup completed successfully")
    print(f"Cleanup stats: {result['cleanup_stats']}")
    print(f"Final stats: {result['final_stats']}")
```

### AssetCatalog Class

#### `__init__(catalog_path)`
Initialize catalog with specified path.

**Parameters:**
- `catalog_path` (Path): Path to catalog file (YAML or JSON)

**Example:**
```python
from purplecrayon import AssetCatalog
from pathlib import Path

catalog = AssetCatalog(Path("./assets/catalog.yaml"))
```

#### `update_catalog_from_assets(assets_dir)`
Update catalog by scanning assets directory.

**Parameters:**
- `assets_dir` (Path): Directory to scan for assets

**Returns:**
- `Dict[str, Any]`: Update statistics

#### `search_assets(query=None, source=None, format=None, **kwargs)`
Search assets in the catalog.

**Parameters:**
- `query` (str, optional): Search query for descriptions
- `source` (str, optional): Filter by source type
- `format` (str, optional): Filter by file format
- `**kwargs`: Additional filter parameters

**Returns:**
- `List[Dict]`: List of matching assets

**Example:**
```python
# Search for specific assets
results = catalog.search_assets(
    query="panda",
    source="ai",
    format="png"
)

for asset in results:
    print(f"Found: {asset['path']} - {asset['description']}")
```

#### `get_stats()`
Get comprehensive catalog statistics.

**Returns:**
- `Dict[str, Any]`: Statistics including counts by source, format, etc.

#### `export_catalog(format="both")`
Export catalog in specified format(s).

**Parameters:**
- `format` (str): Export format - "yaml", "json", "both"

**Returns:**
- `Dict[str, str]`: Paths to exported files

### Direct Tool Functions

#### `scan_and_rename_assets(assets_dir)`
Scan and rename assets based on content analysis.

**Parameters:**
- `assets_dir` (Path): Directory to scan

**Returns:**
- `Dict[str, Any]`: Renaming statistics

#### `cleanup_corrupted_images(assets_dir, remove_junk=True)`
Clean up corrupted and junk images.

**Parameters:**
- `assets_dir` (Path): Directory to clean
- `remove_junk` (bool): Remove junk files

**Returns:**
- `Dict[str, Any]`: Cleanup statistics

#### `validate_image_file(image_path)`
Validate a single image file.

**Parameters:**
- `image_path` (Path): Path to image file

**Returns:**
- `Dict[str, Any]`: Validation result

## CLI Usage

### Sort Catalog Command
```bash
uv run python -m main --sort-catalog
```

### Cleanup Assets Command
```bash
# Clean up corrupted and junk images
uv run python -m main --cleanup

# Keep junk files, only remove corrupted
uv run python -m main --cleanup --keep-junk

# Export in specific format
uv run python -m main --cleanup --catalog-format yaml
```

## Examples

### Example 1: Basic Catalog Management
```python
from purplecrayon import PurpleCrayon, AssetCatalog
from pathlib import Path

crayon = PurpleCrayon()

# Sort and update catalog
result = crayon.sort_catalog()

if result["success"]:
    print("✅ Catalog updated successfully")
    
    # Get catalog statistics
    stats = crayon.catalog.get_stats()
    print(f"Total assets: {stats['total_assets']}")
    print(f"By source: {stats['by_source']}")
    print(f"By format: {stats['by_format']}")
else:
    print(f"❌ Catalog update failed: {result['error']}")
```

### Example 2: Asset Search
```python
# Search for specific assets
results = crayon.catalog.search_assets(
    query="landscape",
    source="stock",
    format="jpg"
)

print(f"Found {len(results)} landscape stock photos:")
for asset in results:
    print(f"  - {asset['path']} ({asset['width']}x{asset['height']})")
```

### Example 3: Asset Cleanup
```python
# Clean up corrupted and junk images
result = crayon.cleanup_assets(remove_junk=True, format="both")

if result["success"]:
    cleanup_stats = result["cleanup_stats"]
    print(f"✅ Cleanup completed:")
    print(f"  - Corrupted removed: {cleanup_stats['corrupted_removed']}")
    print(f"  - Junk removed: {cleanup_stats['junk_removed']}")
    print(f"  - Files renamed: {cleanup_stats['files_renamed']}")
    print(f"  - Extensions corrected: {cleanup_stats['extensions_corrected']}")
```

### Example 4: Direct Catalog Usage
```python
from purplecrayon import AssetCatalog
from pathlib import Path

# Create catalog instance
catalog = AssetCatalog(Path("./assets/catalog.yaml"))

# Search with multiple filters
results = catalog.search_assets(
    query="business",
    source="stock",
    format="jpg",
    min_width=1920,
    min_height=1080
)

# Export catalog
export_paths = catalog.export_catalog(format="both")
print(f"Exported to: {export_paths}")
```

### Example 5: Asset Validation
```python
from purplecrayon.tools.image_validation_tools import validate_image_file
from pathlib import Path

# Validate individual images
image_path = Path("./assets/ai/generated_image.png")
result = validate_image_file(image_path)

if result["valid"]:
    print(f"✅ Image is valid: {result['format']} {result['dimensions']}")
else:
    print(f"❌ Image is invalid: {result['error']}")
```

## Output Organization

### File Structure
```
assets/
├── catalog.yaml              # YAML catalog file
├── catalog.json              # JSON catalog file
├── ai/                       # AI-generated images
├── stock/                    # Stock photos
├── downloaded/               # Scraped images
├── cloned/                   # Cloned images
├── proprietary/              # User-provided images
└── ...
```

### Catalog Format
```yaml
# YAML Format
assets:
  - path: "ai/gemini_123456.png"
    source: "ai"
    provider: "gemini"
    description: "artistic panda illustration"
    width: 1024
    height: 1024
    format: "png"
    tags: ["panda", "artistic", "watercolor"]
    created_at: "2024-01-01T00:00:00Z"
    file_size: 1024000
```

```json
// JSON Format
{
  "assets": [
    {
      "path": "ai/gemini_123456.png",
      "source": "ai",
      "provider": "gemini",
      "description": "artistic panda illustration",
      "width": 1024,
      "height": 1024,
      "format": "png",
      "tags": ["panda", "artistic", "watercolor"],
      "created_at": "2024-01-01T00:00:00Z",
      "file_size": 1024000
    }
  ]
}
```

## Search Capabilities

### Search Parameters
- **query** (str): Text search in descriptions and tags
- **source** (str): Filter by source type (ai, stock, downloaded, cloned, proprietary)
- **provider** (str): Filter by specific provider
- **format** (str): Filter by file format (jpg, png, webp, etc.)
- **min_width** (int): Minimum width filter
- **min_height** (int): Minimum height filter
- **max_width** (int): Maximum width filter
- **max_height** (int): Maximum height filter
- **tags** (List[str]): Filter by specific tags
- **created_after** (str): Filter by creation date
- **created_before** (str): Filter by creation date

### Search Examples
```python
# Search by description
results = catalog.search_assets(query="sunset landscape")

# Search by source and format
results = catalog.search_assets(source="ai", format="png")

# Search by dimensions
results = catalog.search_assets(min_width=1920, min_height=1080)

# Complex search
results = catalog.search_assets(
    query="business meeting",
    source="stock",
    format="jpg",
    min_width=1920,
    tags=["professional", "office"]
)
```

## Statistics and Analytics

### Available Statistics
- **total_assets**: Total number of assets
- **by_source**: Count by source type
- **by_format**: Count by file format
- **by_provider**: Count by provider
- **by_aspect_ratio**: Count by aspect ratio
- **total_size**: Total file size
- **average_size**: Average file size
- **recent_assets**: Recently added assets

### Statistics Example
```python
stats = catalog.get_stats()

print(f"Total Assets: {stats['total_assets']}")
print(f"By Source: {stats['by_source']}")
print(f"By Format: {stats['by_format']}")
print(f"Total Size: {stats['total_size']} bytes")
print(f"Average Size: {stats['average_size']} bytes")
```

## Validation and Cleanup

### Image Validation
- **Format Validation**: Ensures files are valid images
- **Corruption Detection**: Identifies corrupted image files
- **Extension Correction**: Fixes incorrect file extensions
- **Metadata Extraction**: Extracts image metadata

### Junk Detection
- **Tracking Pixels**: Identifies 1x1 tracking pixels
- **Tiny Images**: Detects very small images
- **Common Patterns**: Recognizes common junk file patterns
- **Size Thresholds**: Filters by file size

### Cleanup Process
1. **Scan Assets**: Scans all assets in directory
2. **Validate Images**: Checks each image for validity
3. **Detect Junk**: Identifies junk and corrupted files
4. **Remove Files**: Removes identified junk files
5. **Rename Assets**: Renames files based on content
6. **Update Catalog**: Updates catalog with changes

## Error Handling

### Common Errors
- **File Not Found**: Asset files missing from filesystem
- **Invalid Format**: Unsupported file formats
- **Corrupted Files**: Damaged image files
- **Permission Denied**: File system access issues
- **Catalog Corruption**: Invalid catalog file format

### Error Recovery
- **Automatic Repair**: Attempts to repair corrupted catalogs
- **Graceful Degradation**: Continues with available assets
- **Detailed Logging**: Comprehensive error reporting
- **Backup Creation**: Creates backup before major operations

## Performance Considerations

### Optimization Tips
- Use appropriate search filters to reduce results
- Export catalogs in preferred format only
- Regular cleanup to maintain performance
- Monitor catalog size and complexity

### Resource Usage
- **Memory**: Efficient catalog loading and searching
- **Storage**: Minimal catalog file size
- **CPU**: Optimized search algorithms
- **I/O**: Efficient file system operations

## Configuration

### Environment Variables
```bash
# Optional for enhanced functionality
LANGCHAIN_API_KEY=your_langchain_key  # For AI-powered analysis
```

### Catalog Configuration
```python
# Customize catalog behavior
catalog = AssetCatalog(
    catalog_path=Path("./custom_catalog.yaml"),
    auto_save=True,  # Auto-save changes
    backup_enabled=True  # Enable backups
)
```

## Troubleshooting

### Common Issues
1. **Catalog Not Found**: Ensure catalog file exists or create new one
2. **Search No Results**: Check search parameters and catalog content
3. **Validation Failures**: Check image file integrity
4. **Performance Issues**: Consider catalog cleanup and optimization

### Debug Mode
Enable verbose output:
```python
crayon = PurpleCrayon(verbose=True)
```

This will show detailed information about catalog operations.

## Best Practices

### Catalog Management
- Regular cleanup and maintenance
- Use appropriate search filters
- Monitor catalog size and performance
- Backup catalogs before major operations

### Asset Organization
- Use descriptive filenames
- Add relevant tags and metadata
- Regular validation and cleanup
- Maintain consistent directory structure

### Performance
- Use specific search filters
- Regular catalog optimization
- Monitor file system usage
- Consider catalog format preferences
