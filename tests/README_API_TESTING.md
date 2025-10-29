# API Testing Strategy

This document outlines the testing strategy for 3rd party API integrations in PurpleCrayon, designed to provide comprehensive coverage while minimizing API costs and usage.

## Core Principle: One API Call Per Option

Each test makes exactly **one API call per available option** (model, style, size, website, etc.) to ensure comprehensive coverage while keeping costs minimal.

## Test Categories

### 1. AI Generation Tests (`test_ai_generation_api.py`)

#### Gemini Tests
- **Aspect Ratios**: Tests all supported ratios (1:1, 16:9, 3:2, 4:3) with one call each
- **Styles**: Tests all supported styles (photorealistic, artistic, cartoon, abstract) with one call each
- **Basic Generation**: Single call with minimal parameters

#### Replicate Tests
- **Models**: Tests each available model (flux-1.1-pro, stable-diffusion) with one call each
- **Sizes**: Tests different image sizes (256x256, 512x512, 1024x768) with one call each
- **Basic Generation**: Single call with minimal parameters

### 2. Clone Tests (`test_clone_api.py`)

#### Style Testing
- Tests all supported styles (photorealistic, artistic, cartoon, abstract) with one call each
- Each call uses minimal parameters (128x128, short prompts)

#### Size Testing
- Tests different output sizes (128x128, 256x256, 512x512) with one call each
- Each call uses consistent style to isolate size effects

### 3. Augmentation Tests (`test_augmentation_api.py`)

#### Style Testing
- Tests all supported styles (photorealistic, artistic, cartoon, abstract) with one call each
- Each call uses minimal parameters (128x128, short prompts)

#### Prompt Testing
- Tests different prompt types with one call each
- Uses minimal parameters to focus on prompt effectiveness

### 4. Stock Photo Tests (`test_stock_photos_api.py`)

#### Website Testing
- Tests each available stock photo website (Unsplash, Pexels, Pixabay) with one call each
- Each call requests only 1 image to minimize API usage
- Comprehensive coverage across all available APIs

### 5. Integration Tests (`test_integration_api.py`)

#### PurpleCrayon Class Tests
- **Multiple Images**: Tests different count values (1, 2, 3) with one API call each
- **Single Operations**: Each operation (generate, clone, augment) gets one API call
- **Directory Operations**: Limited to single file processing to minimize API usage

## Cost Optimization Strategies

### 1. Minimal Parameters
- **Short Prompts**: Use 1-2 word prompts instead of full sentences
- **Small Images**: Use 128x128 or 256x256 instead of larger sizes
- **Single Images**: Request 1 image per call instead of batches

### 2. Focused Testing
- **One Variable**: Each test focuses on one parameter (style, size, model)
- **Clear Assertions**: Basic pass/fail validation without detailed content analysis
- **Skip Invalid**: Skip tests when API keys are not available

### 3. Comprehensive Coverage
- **All Options**: Test every available option (model, style, website)
- **All APIs**: Test every available API provider
- **All Functions**: Test every public function with API dependencies

## Test Execution

### Running All API Tests
```bash
# Run all API-dependent tests
pytest -m "api_gemini or api_replicate or api_unsplash or api_pexels or api_pixabay" -v

# Run specific API tests
pytest -m api_gemini -v
pytest -m api_replicate -v
```

### Running Without API Keys
```bash
# Skip API-dependent tests
pytest -m "not (api_gemini or api_replicate or api_unsplash or api_pexels or api_pixabay)" -v
```

## Expected API Usage

### Per Test Run (with all API keys available)
- **Gemini**: ~8 calls (4 aspect ratios + 4 styles)
- **Replicate**: ~5 calls (2 models + 3 sizes)
- **Clone**: ~7 calls (4 styles + 3 sizes)
- **Augmentation**: ~4 calls (4 styles)
- **Stock Photos**: ~3 calls (3 websites)
- **Integration**: ~6 calls (3 counts + 3 operations)

**Total**: ~33 API calls per full test run

### Cost Estimation
- **Gemini**: ~$0.01-0.05 (depending on image sizes)
- **Replicate**: ~$0.10-0.50 (depending on models and sizes)
- **Stock Photos**: ~$0.00-0.01 (free tiers)
- **Total**: ~$0.11-0.56 per full test run

## Maintenance

### Adding New APIs
1. Add new API marker in `conftest.py`
2. Create test with "ONE API CALL PER [OPTION]" pattern
3. Test all available options for the new API
4. Update this documentation

### Adding New Options
1. Add new option to existing test loops
2. Ensure each option gets exactly one API call
3. Update expected API usage counts

### Monitoring Usage
- Review test output for actual API call counts
- Monitor API usage dashboards for unexpected spikes
- Adjust test parameters if costs exceed expectations
