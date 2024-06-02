# Happyfox Fetch and Process Emails Scripts

## Running the Application
### Prerequisites
Make sure you have Python installed on your system. You can get Python from [here](https://www.python.org/downloads/).
### Setting up the Application
- Open command line/shell in your machine
  - Clone the repository
    ```
    git clone https://github.com/kunaldhyani026/happyfox-challenge.git
    ```
  - Move inside cloned application directory
    ```
    cd happyfox-challenge
    ```
  - Install requirements
    ```
    pip install -r requirements.txt
    ```
    #### Application Setup Complete
    - To run the tests
      ```
      python -m unittest discover -s tests
      ```
    - To fetch the emails
      ```
      python fetch_emails.py
      ```
    - To process emails based on rules
      ```
      python process_emails.py
      ```
### Testing
Tests are written in `/tests` directory. 19 tests covers various scenarios.

To run the specs -
- Go to root directory where application resides.
- Run `python -m unittest discover -s tests`
