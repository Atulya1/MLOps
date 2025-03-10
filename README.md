# SocialNexus: Twitter Data Analysis Pipeline

## Project Overview
A comprehensive data pipeline that processes Twitter data related to the Ukraine-Russia crisis, implementing MLOps best practices with robust testing, logging, and monitoring.

## Architecture
```
Data-Pipeline/
├── data/               # Versioned datasets
│   ├── version_1/     # First dataset version
│   ├── version_2/     # Second dataset version
│   └── version_3/     # Third dataset version
|   └── data_versions.py # Manages dataset versions
├── scripts/           # Core processing scripts
│   ├── data_acquisition.py    # Downloads data from Kaggle
│   ├── data_preprocessing.py  # Cleans and processes tweets
│   ├── data_schema.py        # Validates data structure
│   ├── data_versions.py      # Manages dataset versions
│   └── logging_config.py     # Logging configuration
├── tests/             # Test suite
│   ├── data_acquisition_tests.py
│   └── data_preprocessing_tests.py
│   ├── data_index_elasticsearch_tests.py
│   └── es_query_tests.py
├── logs/             # Application logs
└── dags/             # Airflow DAGs
```

## Setup & Installation

1. **Environment Setup**
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. **Kaggle Authentication**
- Make sure Kaggle is installed in your environment
- Create an API token on your Kaggle account (under "Account" > "API" > "Create New API Token"). 
- Place the downloaded kaggle.json file in the correct location 
- (usually ~/.kaggle/kaggle.json on Unix or C:\Users\<User>\.kaggle\kaggle.json on Windows) or 
- Set the appropriate environment variables.
```bash
export KAGGLE_USERNAME=username
export KAGGLE_KEY=api_key
```

3. **Airflow Configuration**
- Set home variable using command: export AIRFLOW_HOME="path to DataPipeline on local"
- Verify airflow.cfg file and change path to dags_folder,base_log_folder,plugins_folder,sql_alchemy_conn,dag_processor_manager_log_location,child_process_log_directory according to your local path
- check environment is activated using command source venv/bin/activate
- Python version should be <= 3.10 to work with airflow
- Initialize the database: `airflow db init`
- Create admin user using following command:
airflow users create \
  --username admin \
  --firstname First \
  --lastname Last \
  --email admin@example.com \
  --role Admin \
  --password admin_password
- airflow scheduler
- airflow webserver

## Core Components

### 1. Data Acquisition (data_acquisition.py)
- Downloads tweet datasets from Kaggle
- Features:
  - Automatic ZIP extraction
  - Version control integration
  - Robust error handling
  - Detailed logging

### 2. Data Preprocessing (data_preprocessing.py)
- Cleans and structures tweet data
- Functions:
  - `removeHashTags()`: Extracts hashtags while preserving words
  - `remove_links()`: Removes URLs
  - `remove_special_characters()`: Cleans text
  - `createTweetObject()`: Structures data

### 3. Data Versioning
- Uses DVC for dataset version control
- Supports multiple data versions:
  - Version 1: Initial dataset
  - Version 2: Extended dataset
  - Version 3: Latest dataset

### 4. Testing Framework
Comprehensive test suite with 100% code coverage.

#### Data Acquisition Tests (data_acquisition_tests.py)
1. **Download Tests**
   - `test_download_selected_files_success`: Verifies successful file downloads
   - `test_download_selected_files_zip_handling`: Tests ZIP extraction
   - `test_download_selected_files_error`: Validates error handling
   - `test_multiple_file_downloads`: Tests batch downloading

2. **Authentication Tests**
   - `test_kaggle_authentication_error`: Verifies auth failure handling

3. **Directory Tests**
   - `test_folder_creation`: Tests directory creation
   - `test_existing_folder_handling`: Tests existing directory scenarios

4. **Integration Tests**
   - `test_main_function`: Tests end-to-end workflow
   - `test_logging_configuration`: Verifies logging setup

#### Data Preprocessing Tests (data_preprocessing_tests.py)
1. **Text Cleaning Tests**
   - `test_removeHashTags_simple`: Basic hashtag removal
   - `test_removeHashTags_multiple`: Multiple hashtag handling
   - `test_removeHashTags_invalid_json`: Invalid hashtag JSON
   - `test_remove_links_multiple`: URL removal
   - `test_remove_links_no_links`: Text without URLs
   - `test_remove_special_characters_comprehensive`: Special character handling
   - `test_text_processing_variations`: Parameterized text processing

2. **Tweet Object Tests**
   - `test_createTweetObject_complete`: Full tweet object creation
   - `test_createTweetObject_minimal`: Minimal tweet fields

3. **File Processing Tests**
   - `test_parseFile_basic`: Basic CSV parsing
   - `test_parse_folder_empty`: Empty folder handling
   - `test_parse_folder_nonexistent`: Missing folder scenarios
   - `test_parse_folder_integration`: End-to-end folder processing

Run specific test suites:
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=scripts

# Run specific test file
pytest tests/data_acquisition_tests.py -v
pytest tests/data_preprocessing_tests.py -v

# Run specific test
pytest tests/data_preprocessing_tests.py -k "test_removeHashTags_simple" -v
```

Test Coverage Requirements:
- Data Acquisition: 100% coverage
- Data Preprocessing: 100% coverage
- All critical paths tested
- Error scenarios validated
- Edge cases handled

### 5. Logging System
- Centralized logging configuration
- Log levels: INFO, WARNING, ERROR
- Separate logs for:
  - Data acquisition
  - Preprocessing
  - Tests

### 6. Data Quality Checks
- Schema validation
- Data integrity checks
- Language filtering
- Duplicate detection

### 7. Airflow Integration
- Automated pipeline scheduling
- DAG structure:
  1. Data download
  2. Preprocessing
  3. Quality checks
  4. Error reporting

## Pipeline Flow
1. **Data Acquisition**
   - Download specified dataset versions
   - Extract and validate files
   - Log acquisition metrics

2. **Preprocessing**
   - Clean and structure tweets
   - Extract relevant features
   - Apply quality filters

3. **Quality Assurance**
   - Validate against schema
   - Check data completeness
   - Monitor processing metrics

## Monitoring & Metrics
- Processing success rate
- Data quality scores
- Pipeline execution time
- Error rates and types

## Error Handling
- Robust exception handling
- Automatic retries
- Detailed error logging
- Alert system for critical failures

## Future Enhancements
1. Real-time Processing
   - Kafka integration
   - Stream processing
   - Live updates

2. Advanced Analytics
   - Sentiment analysis
   - Topic modeling
   - User network analysis

3. Infrastructure
   - Kubernetes deployment
   - Auto-scaling
   - Performance optimization

## Tweet Ranking Algorithm & Score System

Developed a new ranking algorithm for tweets, retrieving indexed tweets from Elasticsearch. 
The ranking score is based on multiple factors including engagement metrics, sentiment analysis, 
and relevance to key topics. For more details, refer - [Tweet Retrieving Algorithm](./docs/tweet_ranking.txt)

## Contributing
1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## License
MIT License - See LICENSE file for details

## Contact
For questions or collaboration, please open an issue or contact the developers.

## Pipeline Graph and Gantt Chart
![image](https://github.com/user-attachments/assets/5aed4a13-abbd-4e76-a598-b05787edb701)
![image](https://github.com/user-attachments/assets/8fb06d26-4e57-4d1d-8473-33fbd90714db)


