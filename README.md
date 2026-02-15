# client-python
Walleta Python API client.

Use this client to send usage data or debits to the Walleta platform.

## Installation

```bash
$ pip install walleta
```

Get your API key from the walleta application.

https://walleta.io/


Put the API key into the environment:
```bash
$ export WALLETA_API_KEY=...
```

You can also use a .env file with docker or docker compose or set it via code:

```python
import os

os.environ['WALLETA_API_KEY'] = '...'
```

## Usage Data
If you want to send usage data for OpenAI or another supported provider, you can use our context manager:


```python
import walleta

...

# Send usage data annotated with customer_id=1234
with walleta.context(customer_id=1234):
    openai.response.create(...)
```

You can also send ad-hoc usage data directy:

```python
import walleta

...

# Send consumption of 433  a chatgpt input tokens annotated with
# customer_id=1234
walleta.send_usage('chatgpt.gpt5.input', 433, customer_id=1234)

```


## Billing
To record a debit for one of your customers, send a debit. This should use one of your own internal tokens. The customer's balance will be adjust immediately.

```python
import walleta

...

# User performed a chargable event.
walleta.send_debit(
    'myproduct.myservice.mytoken', 100, customer_id=1234)
```