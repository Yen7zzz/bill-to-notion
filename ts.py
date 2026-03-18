from notion_client import Client

client = Client(auth="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")
db_id = "2c640bb7443380868f9dcf9e29387429"

results = client.databases.query(database_id=db_id)
for page in results["results"]:
    name = page["properties"]["名稱"]["title"][0]["plain_text"]
    print(f"{name}: {page['id']}")