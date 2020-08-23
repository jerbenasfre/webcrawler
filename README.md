# ABOUT
This webcrawler was an assigned project for COMPSCI 121 Information Retrieval @ University of California Irvine and this repo is a slightly more cleaned up version of my original group's repo (https://github.com/invulnarable27/121SC, https://github.com/invulnarable27/CS121_InvertedIndex) 

The webcrawler crawls a static corpus of the UCI domains. It parses the contents of a website, and creates an index of the words before moving onto a linked page.

# How it Works

The crawler receives a cache host and port from the spacetime servers and instantiates the config.
It launches a crawler (launch.py) which creates a Frontier and Worker(s) using the optional parameters frontier_factory, and worker_factory.
When the crawler in started, workers are created that pick up an undownloaded link from the frontier, download it from the professor's cache server, and pass the response to scraper.py. The links that are received by the scraper is added to the list of undownloaded links in the frontier and the url that was downloaded is marked as complete. The cycle continues until there are no more urls to be downloaded in the frontier and a DEV folder filled with the html content of the pages is built. 

The DEV folder is then read by hybridIndexer.py which builds the partial indexes of the data.

First it creates folders 0-9, a-z to allow for faster retrieval of the tokens. Then it parses the JSON DEV folder to build index.txt which stores the word and its doc location. After building the index, it merges the duplicates and stores the tokens inside one of the partial indexes.

Once the tokens are separated by their first letter, tfidfIndexer.py is called to add weight to the tokens. Then main.py under the websites folder can be run to generate a UI to search for terms.