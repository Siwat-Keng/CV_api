import requests

frame = open('unknown1.jpg', 'rb')
img = {'image': frame, 'userID':'user1', 'domainName': 'domain1'}
json = {'userID':'user1', 'domainName': 'domain1'}
# img['thres'] = '0'

# r = requests.post('http://localhost:8080/register', files=img)

# r = requests.get('http://localhost:8080/register', json=json)

r = requests.post('http://localhost:8080/check', files=img)

# r = requests.post('http://localhost:8080/update', files=img)

# r = requests.delete('http://localhost:8080/delete', json=json)

print(r.text)

