2.1 Data Acquisition:
Our original plan was to fetch data from Twitter (X) using an API which was costly, and we were only able to fetch limited tweets per week. So, we changed our approach. Now, we are downloading tweets crawled by users for research purposes through Kaggle. Also, the tweets that we have considered is related to Russia Ukraine war. There are 20 csv files containing details about.

2.2 Data Preprocessing
Once we acquire the tweet data, we preprocess it to clean and structure the text for further analysis. The preprocessing steps ensure that the data is consistent, noise-free, and ready for embedding generation and sentiment analysis.
Steps in Data Preprocessing
1.	Removing Hashtags from Text
o	Hashtags are extracted separately and removed from the main tweet text.
o	The hashtags are stored in a structured format for later use.
2.	Removing Links
o	Any URLs present in the tweet text (e.g., https://t.co/e2uJugfi0y) are removed to clean unnecessary external links.
o	This step ensures that text analysis is not affected by URLs.
3.	Removing Special Characters & Punctuation
o	We remove non-alphanumeric characters such as punctuation marks (!@#$%^&*()_+) and symbols.
o	This step helps in standardizing the text and improving embeddings.
4.	Extracting Tweet Metadata
o	Along with text cleaning, we extract essential metadata, including:
	userid, username, location, following, followers, totaltweets, usercreatedts, tweetcreatedts, retweetcount, language, and is_retweet.
o	The cleaned text, extracted hashtags, and metadata are stored in a structured format for indexing.
5.	Handling Missing Data
o	Tweets not in English (language! = 'en') are discarded from further processing.
o	If any essential fields are missing, the data is skipped to avoid errors.

2.3 Test Modules
To ensure robustness and correctness of the preprocessing steps, we include unit tests for the key functions:
1.	Test remove links: Ensures URLs are removed correctly.
2.	Test remove special characters: Checks if special characters, punctuation, and non-alphanumeric characters are removed.
3.	Test remove HashTags: Validates hashtag removal based on provided indices.
4.	Test remove substring: Verifies correct removal of a substring from a given text.
5.	Duplicate tweets: Removes duplicate tweets from the text string.
6.	Test_query_retrieves_relevant_tweets: Ensures the Elasticsearch query retrieves relevant tweets.
7.	Test_clean_text_removes_hashtags: Checks if a single hashtag is removed from the text.
8.	Test_clean_text_removes_multiple_hashtags: Ensures multiple hashtags are removed correctly.
9.	Test_clean_text_handles_no_hashtags: Ensures text remains unchanged if there are no hashtags.
10.	Test_clean_text_handles_partial_word_matches: Ensures that removing hashtags doesn’t affect similar words (e.g., #War should not remove "War" in a sentence).
11.	Test_clean_text_handles_special_characters: Verifies that special characters are handled correctly.
 2.4.Pipeline Orchestration :
  We have structured our pipeline using Apache Airflow DAGs, ensuring logical connections between tasks for efficient execution and orchestration. Airflow is well-suited for our project because:

Task Dependencies and Workflow Structure – Airflow allows us to define and manage complex task dependencies, ensuring that tasks are executed in the correct order. Each task in the DAG represents a discrete unit of work, creating clear logical connections throughout the pipeline.

Dynamic Workflow Scheduling – With Airflow's scheduling capabilities, we can automatically trigger pipeline runs at specific intervals, making it ideal for automating our data processing workflow. This allows us to handle both batch and real-time data processing efficiently.

Monitoring and Logging – Airflow provides built-in monitoring and logging, ensuring that we can track the status of each task in the pipeline. This feature is crucial for identifying issues and optimizing the pipeline's performance.

Scalability and Extensibility – Airflow's architecture is scalable, enabling us to easily extend our pipeline as the project grows. New tasks or workflows can be added seamlessly, leveraging Airflow's extensibility to handle more complex requirements.

Centralized Execution Management – By using Airflow, we centralize the execution and management of our pipeline, which reduces the need for manual intervention and ensures consistent execution across environments.
2.5 Data Versioning with DVC: In our project, we are using Data Version Control (DVC) to efficiently track and version control our datasets, particularly the CSV files that make up different parts of our data. With DVC, we initialize the repository, add our datasets to version control, and link them to remote storage such as Azure for efficient data handling. The .dvc files corresponding to each dataset are tracked in Git alongside the code and configurations, ensuring full reproducibility of the project. This setup allows us to manage large datasets without overloading the Git repository, while also ensuring that any changes to the data are versioned and retrievable for future use or collaboration.

2.6. Tracking and Logging:

We have used Python’s logging library, which efficiently tracks the pipeline execution by recording key events such as indexing, embedding generation, and query retrieval. This helps in debugging and monitoring anomalies.

2.7. Data Schema & Statistics Generation:
We ensure data schema enforcement and basic statistics generation through Elasticsearch mappings and logging-based monitoring to maintain data integrity and quality.
 
How Schema & Statistics Are Managed in the Code:
1.	Elasticsearch Schema Enforcement
a.	The index mappings in Elasticsearch define data types for fields like userid (keyword), tweetcreatedts (date), and followers (integer), ensuring schema consistency.

 "userid": {"type": "keyword"},
 "tweetcreatedts": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
 "followers": {"type": "integer"}

2.	Basic Data Statistics
a.	Tweet counts and hashtag distributions are indirectly monitored while processing.
b.	Logs track processed, skipped, and missing tweets, helping validate data quality.

 logging.info(f"Indexing done for {len(all_tweets)} tweets.")

Thus, schema validation is managed via Elasticsearch, while data statistics are tracked using logging instead of automated tools.
2.8. Anomaly Detection & Alerts
We implement anomaly detection by applying multiple filtering and cleaning steps during data preprocessing:
•	Language Filtering – Only tweets in English are processed, ensuring consistency in text analysis.
•	Hashtag Removal – Extracts and removes hashtags separately to clean the tweet text while preserving structured metadata.
•	Link Removal – Eliminates URLs from tweets to prevent unnecessary noise in text processing.
•	Special Character Cleaning – Removes non-alphanumeric characters to standardize text formatting.
•	Logging for Monitoring – Logs the number of processed and indexed tweets, helping to track data integrity and identify any inconsistencies.
These steps help maintain clean, structured, and high-quality data throughout the pipeline.

2.9. Pipeline Flow Optimization: 


3.	Data Bias Detection Using Data Slicing
Data bias detection is not included in our project because:
1.	No Machine Learning Model is Used – Bias detection is typically applied to model predictions, but our pipeline focuses on text processing, indexing, and retrieval, not predictive modeling.
2.	No Decision-Making System – We are not training a classifier that could introduce bias in its predictions. The pipeline processes tweets as they are, without modifying or weighting certain data over others.
3.	Dataset Scope and Objective – The project does not aim to analyze fairness across demographic groups. Instead, it focuses on processing, storing, and retrieving tweets related to the Russia-Ukraine war for tweet summarization.
4.	No Structured Categorical Features – Bias detection methods typically rely on structured demographic features (e.g., age, gender, race). Our dataset consists mainly of textual data and metadata (e.g., usernames, locations) which are not used for classification.
Since no model is making predictions, and no structured demographic data is analyzed for fairness, bias detection through data slicing is not necessary for this project.