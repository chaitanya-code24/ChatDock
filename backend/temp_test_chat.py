import requests
base='http://localhost:8000'
creds={'email':'ragtest3@example.com','password':'test1234'}
r=requests.post(base+'/auth/register', json=creds)
print('register', r.status_code, r.text)
if r.status_code!=201:
    r=requests.post(base+'/auth/login', json=creds)
    print('login', r.status_code, r.text)
token=r.json().get('access_token')
headers={'Authorization':f'Bearer {token}'}
r=requests.post(base+'/bot/create', json={'bot_name':'RAG Bot','description':'test'}, headers=headers)
print('bot', r.status_code, r.text)
bot_id=r.json().get('id')
r=requests.post(base+'/chat', json={'bot_id':bot_id,'message':'list all the policies'}, headers=headers)
print('chat', r.status_code, r.text)
