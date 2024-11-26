from O365 import Account


class Mailer:
    def __init__(self, client_id: str, client_secret: str, tenant: str, email: str):
        self._email = email

        credentials = (client_id, client_secret)
        self._account = Account(credentials, auth_flow_type='credentials', tenant_id=tenant)

    def try_login(self):
        assert self._account.authenticate()

    def send_mail(self, mail_obj: str, mail_body: str, mail_recipient: str, attachments = None):
        if not self._account.is_authenticated:
            self._account.authenticate()
        m = self._account.new_message(resource=self._email)
        m.to.add(mail_recipient)
        m.subject = mail_obj
        m.body = mail_body
        if attachments:
            for attachment in attachments:
                m.attachments.add(attachment)
        m.send()

