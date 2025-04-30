import requests

test_api=requests.get(url="http://localhost:5000/members",headers={
    'Content-Type': 'application/json',
    'accept'
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjQ1MjM5OCwianRpIjoiODlmNmZjOTUtM2RhMS00N2U4LWE3YzktY2RjYzhiNDg5N2RmIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6NywibmJmIjoxNzQyNDUyMzk4LCJjc3JmIjoiYmJhMWViODktMTA2My00YmRhLWJhNzItZDBiODJlNzk0ODI1IiwiZXhwIjoxNzQyNDUzMjk4fQ.BExHBPza8yVzu5vNR_RdsyY3a52McWQk5xTuBq05s20"
})
print(test_api.text,test_api.status_code)