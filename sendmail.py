import smtplib
server = smtplib.SMTP('smtp.gmail.com',587)

server.starttls()

server.login('kanbaniitm@gmail.com','tsslafciqjfvffgz')

server.sendmail('kanbaniitm@gmail.com','saicharankmrs@gmail.com','<b>Mail From Python!!</b>')
print("mailsent")