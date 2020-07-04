import requests

frame = open('unknown3.jpg', 'rb')
img = {'image': frame, 'userID':'user1', 'domainName': 'domain1'}
json = {'userID':'user1', 'domainName': 'domain1'}

# r = requests.post('http://localhost:8080/check', files=img)

r = requests.post('http://localhost:8080/register', files=img)

# r = requests.post('http://localhost:8080/update', files=img)

# r = requests.delete('http://localhost:8080/delete', json=json)

print(r.text)

