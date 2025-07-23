import requests

def call_api(query, api_url, api_key):
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "collection": "srr_collection",
        "messages": [
            {"role": "user", "content": query}
        ],
        "k": 3
    }
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()  # Success
    else:
        print(f"Error {response.status_code}: {response.text}")
        return {}  # Return empty dict for errors

api_url = "http://decisionservices-ws.c-qa4.svc.rnq.k8s.lot.com/v1/chat"
api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImdhdXRoLWtleS1pZC0xIn0.."

def apidata_retriever(query, api_url=api_url, api_key=api_key):
    resource = call_api(query, api_url, api_key)
    # Debug the structure:
    print("DEBUG resource:", resource)
    return resource.get("content", "No content found.")  # Adjust this as per actual API structure

if __name__ == "__main__":
    test_query = "What is the status of lot 12345?"
    result = apidata_retriever(test_query)
    print("Result:", result)