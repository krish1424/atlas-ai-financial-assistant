\# Atlas AI Financial Assistant



Atlas is a conversational AI financial assistant built with Python. It combines an AI agent with financial data tools, document analysis, persistent conversations, a FastAPI backend, and a Telegram interface.



The project is designed as a modular backend that can be extended with additional financial tools and integrations.



\---



\## Features



\### AI Financial Assistant



Atlas can process user questions through an AI agent and determine how the request should be handled.



Current capabilities include:



\- General financial questions

\- Market data queries

\- Financial news queries

\- Document-based financial analysis

\- Conversation history

\- Telegram-based interaction



\---



\## Financial Market Data



Atlas uses Alpha Vantage for stock market data.



The market-data component supports:



\- Stock symbol lookup

\- Latest available stock price

\- Price change

\- Percentage change

\- Trading volume

\- Latest trading day



The market-data provider uses Alpha Vantage's `GLOBAL\_QUOTE` endpoint.



\---



\## Financial News



Atlas uses Alpha Vantage's `NEWS\_SENTIMENT` endpoint for financial news.



News results include:



\- Article title

\- Summary

\- Source

\- URL

\- Publication time

\- Sentiment label

\- Sentiment score



When a company ticker is provided, Atlas applies additional company-relevance filtering instead of relying only on the provider's relevance score.



\---



\## PDF Document Analysis



Atlas can receive PDF financial documents through Telegram and analyze their contents.



The document-analysis pipeline is:



```text

PDF

&#x20;|

&#x20;v

Text Extraction

&#x20;|

&#x20;v

Text Cleaning

&#x20;|

&#x20;v

Document Chunking

&#x20;|

&#x20;v

Keyword-Based Relevance Selection

&#x20;|

&#x20;v

Grounded AI Prompt

&#x20;|

&#x20;v

Atlas AI Response
