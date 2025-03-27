import os
import time
import shutil
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from rag_youtube import get_results

def scrape_youtube_comments(url, scroll_count):
    """
    Opens the given YouTube video URL using ChromeDriver, scrolls the page
    to load more comments, and extracts the text of those comments.

    :param url: The URL of the YouTube video.
    :param scroll_count: Number of times to scroll down to load comments.
    :return: List of comment texts.
    """
    comments = []
    # Instead of making a directory with the URL, create a folder for output.
    os.makedirs("./youtube_comments", exist_ok=True)

    # Adjust the executable_path as needed or remove it if chromedriver is in your PATH.
    with Chrome() as driver:
        wait = WebDriverWait(driver, 15)
        driver.get(url)
        # Scroll to load more comments.
        for _ in range(scroll_count):
            wait.until(EC.visibility_of_element_located((By.TAG_NAME, "body"))).send_keys(Keys.END)
            time.sleep(5)
        # Now extract elements containing comments.
        comment_elements = driver.find_elements(By.ID, "content-text")
        for elem in comment_elements:
            comments.append(elem.text)

    return comments

def save_comments_to_file(comments, file_path="./youtube_comments/comments.txt"):
    """
    Saves the list of comments to a text file.

    :param comments: List of comment strings.
    :param file_path: Path to the file where comments will be saved.
    """
    with open(file_path, "w", encoding="utf-8") as file:
        for comment in comments:
            file.write(comment + "\n")
    print(f"Comments saved to {file_path}")

def main():
    youtube_video_url = "https://www.youtube.com/watch?v=WQdqgrWvy6g"
    # Scrape comments from the given YouTube video.
    comments = scrape_youtube_comments(youtube_video_url, 10)

    # Ask the user for their initial question about the video.
    user_question = input("Enter your question about the video: ")
    final_comment = get_results(user_question, comments, 1.5, 3, 0.0)
    print("\nResponse:")
    print(final_comment)

    # Loop to handle follow-up questions.
    while True:
        followup = input("\nEnter a followup question (or type 'exit' to quit): ")
        if followup.strip().lower() in ['exit', 'quit', 'q']:
            print("Exiting followup session.")
            # Delete the embeddings folder if it exists.
            embeddings_folder = "embeddings"
            if os.path.exists(embeddings_folder):
                shutil.rmtree(embeddings_folder)
                print(f"Deleted folder: {embeddings_folder}")
            else:
                print(f"Folder '{embeddings_folder}' does not exist.")
            break
        final_followup_response = get_results(followup, comments, 1.5, 3, 0.0)
        print("\nResponse:")
        print(final_followup_response)

if __name__ == "__main__":
    main()

