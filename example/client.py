import requests

frame = open('unknown2.jpg', 'rb').read()
print(type(frame))
print(frame)
img = {'image': frame, 'userID':'user1', 'domainName': 'domain1'}
json = {'userID':'example', 'domainName': 'example'}
img['thres'] = '1'
# print(type(frame))
# r = requests.post('http://localhost:8080/register', files=img)

# r = requests.get('http://localhost:8080/register', json=json)

# r = requests.post('http://localhost:8080/check', files=img)

# r = requests.post('http://localhost:8080/update', files=img)

r = requests.delete('http://localhost:8080/delete', json=json)

print(r.text)

