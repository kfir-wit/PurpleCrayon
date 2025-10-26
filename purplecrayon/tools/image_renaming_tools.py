from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image
from .asset_management_tools import AssetCatalog


def get_image_dimensions(file_path: Path) -> Optional[Tuple[int, int]]:
    """Get image dimensions using PIL"""
    try:
        with Image.open(file_path) as img:
            return img.size  # Returns (width, height)
    except Exception as e:
        print(f"Could not get dimensions for {file_path}: {e}")
        return None


def has_actual_alpha_channel(file_path: Path) -> bool:
    """Check if PNG file actually has transparent pixels"""
    try:
        with Image.open(file_path) as img:
            # First check if it has an alpha channel
            if img.mode not in ('RGBA', 'LA'):
                return False
            
            # Convert to RGBA to check alpha values
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Get alpha channel
            alpha = img.split()[-1]
            
            # Check if any pixels are actually transparent (alpha < 255)
            alpha_values = list(alpha.getdata())
            transparent_pixels = [a for a in alpha_values if a < 255]
            
            return len(transparent_pixels) > 0
            
    except Exception as e:
        print(f"Error checking alpha for {file_path}: {e}")
        return False


def analyze_image_with_llm(file_path: Path) -> str:
    """
    Use LLM to analyze image content and generate a descriptive name prefix.
    Only called for files that aren't properly structured.
    """
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        import base64
        import io
        
        # Load and encode image
        with open(file_path, "rb") as f:
            image_bytes = f.read()
        
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        prompt = """
        Analyze this image and provide a concise, descriptive name prefix for it.
        The name should be 2-4 words that describe the main subject or content.
        Use underscores to separate words and make it suitable for a filename.
        
        Examples of good prefixes:
        - panda_with_bamboo
        - business_meeting_handshake
        - mountain_landscape
        - abstract_geometric_pattern
        - woman_presenting_charts
        
        Return ONLY the name prefix, nothing else.
        """
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ]
        )
        
        response = llm.invoke([message])
        content = response.content.strip()
        
        # Clean up the response
        content = re.sub(r'[^a-zA-Z_]', '', content)  # Remove non-alphanumeric except underscores
        content = content.lower()
        
        # Ensure it's not empty and has reasonable length
        if not content or len(content) < 3:
            return "image_content"
        
        return content
        
    except Exception as e:
        print(f"  ⚠️ LLM analysis failed for {file_path.name}: {e}")
        return "image_content"


def create_description_from_filename(filename: str, file_path: Path = None) -> str:
    """Create a description based on the filename, with LLM fallback for unstructured names"""
    # Remove extension
    name = Path(filename).stem
    
    # Handle different naming patterns
    descriptions = {
        # Clear descriptive names
        'sky-blue-clouds-wallpaper-preview': 'clear_blue_sky',
        'information-overload-1024x768': 'information_overload_diagram',
        'privacy': 'privacy_protection_concept',
        'logo': 'company_logo_round',
        'shutterstock_488322949': 'business_meeting_handshake',
        'marketing-big-data-examples-applications': 'big_data_marketing_analytics',
        'successful-businessman-showing-growth-chart-digital-tablet-generated-by-ai': 'businessman_growth_chart_tablet',
        'ColorMag-Featured-Image-18': 'colorful_magazine_feature',
        'businesspeople-working-finance-accounting-analyze-financial-graph-budget-planning-future-office-room': 'finance_team_analysis_office',
        'revenue-operations-collage': 'revenue_operations_collage',
        'abstract-office-desktop_': 'abstract_office_desktop',
        'chess': 'chess_strategy_board',
        'oup_22335': 'scientific_research_paper',
        '86361': 'modern_office_workspace',
        '39034': 'business_team_collaboration',
        'person-using-ai-tool-job': 'person_using_ai_tool',
        'modern-architecture-4749683': 'modern_architecture_building',
        'leo-sokolovsky-YhMS8WKquds-unsplash': 'mountain_landscape_nature',
        'ryunosuke-kikuno-lfAys7KTGCs-unsplash': 'urban_city_skyline',
        'smiling-caucasian-woman-startup-office-doing-business-presentation-big-tv-screen-with-charts-front-team-confident-employee-presenting-growing-sales-statistics-late-night-meeting': 'woman_business_presentation_team',
        'mid-adult-manager-holding-business-presentation-looking-camera-while-standing-front-whiteboard': 'manager_whiteboard_presentation',
        'business-people-meeting': 'business_people_meeting',
        'workplace-with-smartphone-laptop-black-table-top-view-copyspace-background': 'workplace_technology_setup',
        'hero-background': 'hero_section_background',
    }
    
    # Check for exact matches first
    if name in descriptions:
        return descriptions[name]
    
    # Handle kfiri_51441 files (AI generated images)
    if name.startswith('kfiri_51441_'):
        # Extract the descriptive part after the ID
        descriptive_part = name.replace('kfiri_51441_', '')
        
        # Map specific kfiri files
        kfiri_descriptions = {
            'a_digital_twin_that_knows_the_responsibilities_and__a0fe1e49-f093-4546-86c7-0a9b1b52fb21-removebg-preview': 'digital_twin_concept_alpha',
            'a_digital_twin_that_knows_the_responsibilities_and__a0fe1e49-f093-4546-86c7-0a9b1b52fb21': 'digital_twin_concept',
            'a_great_background_image_for_a_landing_page._someth_0fadfb0c-0350-43f9-a570-8a7b428dbed8': 'landing_page_background',
            'a_multi_modal_intelligence_system_based_on_digital__6a08b9d2-d1cb-4136-9373-7bd45674ef73': 'multi_modal_intelligence_system',
            'a_multi_modal_intelligence_system_based_on_digital__a2662664-7170-4519-b2cd-cfd132e337ea': 'multi_modal_intelligence_diagram',
            'a_multi_modal_intelligence_system_based_on_digital__faf14000-85ac-4c43-a950-09ac68e06c9c': 'multi_modal_intelligence_network',
            'a_visualisation_of_a_BI_system_running_on_a_macbook_57ecbd99-2ab8-48d6-891f-68268918b935': 'bi_system_macbook_dashboard',
            'an_executive_seeing_only_what_is_in_front_of_her_ig_ed4ec01a-fc82-4f16-b105-3e214f60bc55': 'executive_forward_focus',
            'an_iceberg_where_one_third_is_above_water_and_two_t_5bfc4600-2888-48ed-a82a-1325ccc561a0': 'iceberg_metaphor_visible_hidden',
            'a_business_man_in_a_suit_relaxing_at_the_beach._sho_e33ea727-b650-4c6d-9ad3-3682bd370d79': 'businessman_beach_relaxing',
            'companies_achieving_business_success_as_a_result_of_dadfd08c-eb33-473f-b408-89e8bb904583': 'companies_business_success',
            'the_brain_of_an_AI_system_gathering__analyzing_and__673a687c-d07f-435c-8217-680262fb86eb': 'ai_brain_analysis_system',
            'the_brain_of_an_AI_system_gathering__analyzing_and__c7a1aa6c-40c0-4c25-aa8a-0819a3b99d2d': 'ai_brain_processing_network',
        }
        
        if name in kfiri_descriptions:
            return kfiri_descriptions[name]
        
        # Generic kfiri description
        return 'ai_generated_concept'
    
    # Try to extract meaningful words from the filename
    words = re.findall(r'[a-zA-Z]+', name)
    if len(words) >= 3:
        return '_'.join(words[:3])
    elif len(words) >= 2:
        return '_'.join(words[:2])
    else:
        # If filename is not descriptive and we have file_path, use LLM analysis
        if file_path and file_path.exists():
            print(f"  🤖 Using LLM to analyze image content for: {filename}")
            return analyze_image_with_llm(file_path)
        else:
            return 'image_asset'


def normalize_image_extension(filename: str) -> str:
    """Normalize image filename to use .jpg for JPEG files."""
    if filename.lower().endswith('.jpeg'):
        return filename[:-5] + '.jpg'
    return filename


def generate_alternative_description(original_description: str, attempt: int) -> str:
    """Generate alternative descriptions to resolve filename conflicts."""
    alternatives = {
        # Common word variations
        'bamboo': ['bamboo_twigs', 'bamboo_shoots', 'bamboo_leaves', 'bamboo_forest', 'bamboo_grove'],
        'panda': ['panda_bear', 'giant_panda', 'panda_cub', 'panda_mother', 'panda_family'],
        'eating': ['munching', 'chewing', 'feeding', 'dining', 'consuming'],
        'forest': ['woodland', 'jungle', 'woods', 'grove', 'thicket'],
        'mountain': ['peak', 'summit', 'ridge', 'hill', 'cliff'],
        'water': ['ocean', 'sea', 'lake', 'river', 'stream'],
        'sky': ['heavens', 'clouds', 'atmosphere', 'firmament', 'blue_sky'],
        'sun': ['sunshine', 'sunlight', 'solar', 'bright', 'radiant'],
        'moon': ['lunar', 'crescent', 'full_moon', 'night_sky', 'celestial'],
        'flower': ['bloom', 'blossom', 'petal', 'floral', 'botanical'],
        'tree': ['oak', 'pine', 'maple', 'birch', 'cedar'],
        'bird': ['eagle', 'hawk', 'sparrow', 'robin', 'cardinal'],
        'cat': ['feline', 'kitten', 'tabby', 'persian', 'siamese'],
        'dog': ['canine', 'puppy', 'hound', 'retriever', 'shepherd'],
        'car': ['vehicle', 'automobile', 'sedan', 'suv', 'truck'],
        'house': ['home', 'dwelling', 'residence', 'cottage', 'mansion'],
        'city': ['urban', 'metropolitan', 'downtown', 'skyline', 'streetscape'],
        'business': ['corporate', 'professional', 'office', 'commercial', 'enterprise'],
        'meeting': ['conference', 'gathering', 'assembly', 'discussion', 'collaboration'],
        'team': ['group', 'crew', 'staff', 'workforce', 'personnel'],
        'chart': ['graph', 'diagram', 'visualization', 'analytics', 'data'],
        'technology': ['tech', 'digital', 'electronic', 'computer', 'software'],
        'abstract': ['geometric', 'pattern', 'design', 'artistic', 'creative'],
        'flag': ['banner', 'emblem', 'symbol', 'standard', 'pennant'],
    }
    
    # Try to find variations for each word in the description
    words = original_description.split('_')
    new_words = []
    
    for word in words:
        if word in alternatives and attempt < len(alternatives[word]):
            new_words.append(alternatives[word][attempt])
        else:
            new_words.append(word)
    
    # If we've exhausted alternatives, add a numeric suffix
    if attempt >= 5:
        return f"{original_description}_{attempt + 1}"
    
    return '_'.join(new_words)


def find_unique_filename(base_path: Path, description: str, size_str: str, alpha_suffix: str, extension: str) -> Path:
    """Find a unique filename by trying alternatives if conflicts exist."""
    base_name = f"{description}_{size_str}{alpha_suffix}{extension}"
    target_path = base_path.parent / base_name
    
    if not target_path.exists():
        return target_path
    
    # Try alternative descriptions
    for attempt in range(10):  # Try up to 10 alternatives
        alt_description = generate_alternative_description(description, attempt)
        alt_name = f"{alt_description}_{size_str}{alpha_suffix}{extension}"
        alt_path = base_path.parent / alt_name
        
        if not alt_path.exists():
            print(f"  🔄 Resolved conflict: {base_name} -> {alt_name}")
            return alt_path
    
    # If all alternatives fail, add a numeric suffix
    counter = 1
    while True:
        fallback_name = f"{description}_{size_str}{alpha_suffix}_{counter}{extension}"
        fallback_path = base_path.parent / fallback_name
        
        if not fallback_path.exists():
            print(f"  🔄 Fallback naming: {base_name} -> {fallback_name}")
            return fallback_path
        
        counter += 1
        if counter > 999:  # Safety limit
            raise ValueError(f"Could not find unique filename for {base_name}")


def is_already_properly_named(filename: str) -> bool:
    """Check if file already follows the proper naming convention"""
    # Pattern: description_dimensions[_alpha].extension
    # Examples: clear_blue_sky_728x485.jpg, company_logo_round_970x257_alpha.png
    
    # Remove extension to get the base name
    name_without_ext = Path(filename).stem
    extension = Path(filename).suffix.lower()
    
    # Check if it matches the pattern: word_word_word_dimensions[_alpha]
    # Pattern breakdown:
    # - One or more word groups separated by underscores
    # - Followed by dimensions (numbers x numbers)
    # - Optionally followed by _alpha
    pattern = r'^[a-zA-Z_]+_\d+x\d+(_alpha)?$'
    
    return bool(re.match(pattern, name_without_ext))


def rename_image_file(file_path: Path) -> Optional[Path]:
    """Rename a single image file with proper naming convention"""
    if not file_path.exists():
        return None
    
    # Check if already properly named
    if is_already_properly_named(file_path.name):
        return file_path
    
    # Get image dimensions
    dimensions = get_image_dimensions(file_path)
    if not dimensions:
        return None
    
    width, height = dimensions
    size_str = f"{width}x{height}"
    
    # Create description
    description = create_description_from_filename(file_path.name)
    
    # Determine suffix/extension details (PNG needs alpha flag)
    has_alpha = False
    alpha_suffix = ""
    normalized_extension = normalize_image_extension(file_path.suffix)

    if file_path.suffix.lower() == '.png':
        has_alpha = has_actual_alpha_channel(file_path)
        alpha_suffix = "_alpha" if has_alpha else ""

    # Find unique filename to avoid conflicts
    new_path = find_unique_filename(file_path, description, size_str, alpha_suffix, normalized_extension)

    # Rename the file
    try:
        file_path.rename(new_path)
        return new_path
    except Exception as e:
        print(f"Error renaming {file_path.name}: {e}")
        return file_path


def rename_images_in_directory(directory: Path) -> Dict[str, int]:
    """Rename all images in a directory with proper naming convention"""
    if not directory.exists():
        return {"renamed": 0, "skipped": 0, "errors": 0}
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico'}
    
    renamed_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            print(f"Processing: {file_path.name}")
            
            # Check if file is already properly named
            if is_already_properly_named(file_path.name):
                print(f"  ✅ Already properly named - skipping")
                skipped_count += 1
                continue
            
            # Get image dimensions
            dimensions = get_image_dimensions(file_path)
            if not dimensions:
                print(f"  ❌ Could not get dimensions")
                error_count += 1
                continue
            
            width, height = dimensions
            size_str = f"{width}x{height}"
            
            # Create description (with LLM analysis if needed)
            description = create_description_from_filename(file_path.name, file_path)
            
            # Determine suffix/extension details (PNG needs alpha flag)
            has_alpha = False
            alpha_suffix = ""
            normalized_extension = normalize_image_extension(file_path.suffix)

            if file_path.suffix.lower() == '.png':
                has_alpha = has_actual_alpha_channel(file_path)
                print(f"  Alpha detection: {has_alpha}")
                alpha_suffix = "_alpha" if has_alpha else ""

            # Find unique filename to avoid conflicts
            new_path = find_unique_filename(file_path, description, size_str, alpha_suffix, normalized_extension)

            # Rename the file
            try:
                file_path.rename(new_path)
                print(f"  ✅ Renamed: {file_path.name} -> {new_path.name}")
                renamed_count += 1
            except Exception as e:
                print(f"  ❌ Error renaming {file_path.name}: {e}")
                error_count += 1
    
    return {
        "renamed": renamed_count,
        "skipped": skipped_count, 
        "errors": error_count
    }


def scan_and_rename_assets(assets_dir: Path = None) -> Dict[str, int]:
    """Scan the assets directory, rename files, and update catalog."""
    if assets_dir is None:
        assets_dir = Path("assets")
    
    if not assets_dir.exists():
        return {"renamed": 0, "skipped": 0, "errors": 0, "catalog_updated": 0}
    
    # Initialize catalog
    catalog_path = assets_dir / "catalog.yaml"
    catalog = AssetCatalog(catalog_path)
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico'}
    
    renamed_count = 0
    skipped_count = 0
    error_count = 0
    catalog_updated = 0
    
    # Process each subdirectory
    for subdir in [assets_dir / "ai", assets_dir / "stock", assets_dir / "proprietary", assets_dir / "downloaded"]:
        if not subdir.exists():
            continue
            
        print(f"\n📁 Processing {subdir.name}/ directory...")
        
        for file_path in subdir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                print(f"Processing: {file_path.name}")
                
                # Check if file is already properly named
                if is_already_properly_named(file_path.name):
                    print(f"  ✅ Already properly named - skipping")
                    skipped_count += 1
                    continue
                
                # Get image dimensions
                dimensions = get_image_dimensions(file_path)
                if not dimensions:
                    print(f"  ❌ Could not get dimensions")
                    error_count += 1
                    continue
                
                width, height = dimensions
                size_str = f"{width}x{height}"
                
                # Create description (with LLM analysis if needed)
                description = create_description_from_filename(file_path.name, file_path)
                
                # Determine suffix/extension details (PNG needs alpha flag)
                has_alpha = False
                alpha_suffix = ""
                normalized_extension = normalize_image_extension(file_path.suffix)

                if file_path.suffix.lower() == '.png':
                    has_alpha = has_actual_alpha_channel(file_path)
                    print(f"  Alpha detection: {has_alpha}")
                    alpha_suffix = "_alpha" if has_alpha else ""

                # Find unique filename to avoid conflicts
                new_path = find_unique_filename(file_path, description, size_str, alpha_suffix, normalized_extension)

                # Rename the file
                try:
                    file_path.rename(new_path)
                    print(f"  ✅ Renamed: {file_path.name} -> {new_path.name}")
                    renamed_count += 1
                    
                    # Add to catalog
                    try:
                        catalog.add_asset(new_path)
                        catalog_updated += 1
                        print(f"  📝 Added to catalog")
                    except Exception as e:
                        print(f"  ⚠️ Could not add to catalog: {e}")
                        
                except Exception as e:
                    print(f"  ❌ Error renaming {file_path.name}: {e}")
                    error_count += 1
    
    # Update catalog with any remaining files
    try:
        scan_results = catalog.scan_and_update_assets(assets_dir)
        catalog_updated += scan_results.get("added", 0)
        print(f"\n📊 Catalog scan: {scan_results}")
    except Exception as e:
        print(f"⚠️ Catalog scan error: {e}")
    
    return {
        "renamed": renamed_count,
        "skipped": skipped_count,
        "errors": error_count,
        "catalog_updated": catalog_updated
    }
