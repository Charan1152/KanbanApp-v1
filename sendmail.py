import smtplib
server = smtplib.SMTP('smtp.gmail.com',587)
server.starttls()
server.login('kanbaniitm@gmail.com','tsslafciqjfvffgz')

def mail_otp(mailid):
    import random as r
    otp = (r.randint(1111,9999))
    server.sendmail('kanbaniitm@gmail.com',mailid,'OTP for KanbanApp:'+otp+"\n\nValid for 10 Mins.")
    return otp