"""
邮件异步任务
"""
from app.core.celery_app import celery_app


@celery_app.task(name="send_email_async", bind=True, max_retries=3)
def send_email_async(self, to_email: str, subject: str, body: str):
    """
    异步发送邮件
    - 自动重试最多3次
    - 指数退避: 60s, 120s, 240s
    """
    try:
        # TODO: 实现邮件发送逻辑 (smtplib / aiosmtplib)
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from app.core.config import settings

        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())

        return {"status": "ok", "to": to_email}
    except Exception as exc:
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(name="send_welcome_email")
def send_welcome_email(user_email: str, username: str):
    """发送欢迎邮件"""
    subject = "欢迎加入 FastAPI CRM"
    body = f"""
    <h2>欢迎 {username}！</h2>
    <p>您已成功注册 FastAPI CRM 系统。</p>
    <p>请登录系统开始使用：<a href="/login">立即登录</a></p>
    """
    send_email_async.delay(to_email=user_email, subject=subject, body=body)
