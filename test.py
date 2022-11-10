url = 'https://profi.ru/krasota/massage/?seamless=1&tabName=PROFILES&gpId=&p=1'

a = url.split('/')
print(a)
name = '/'.join(a[2:5])
print(name)