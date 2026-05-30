from base64 import b64encode
from pathlib import Path
from typing import Optional
import mimetypes

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Disposition,
    FileContent,
    FileName,
    FileType,
    Mail,
)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


class SendGridEmail:
    def __init__(self, api_key: str, from_email: str = "pranavpuri.p@hotmail.com"):
        self.api_key = api_key
        self.from_email = from_email
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_template(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        attachments: Optional[list[dict]] = None,
        from_email: Optional[str] = None,
    ) -> None:
        html_content = self.render_template(template_name, context)
        message = Mail(
            from_email=from_email or self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )

        if attachments:
            for attachment in attachments:
                path = Path(attachment["path"])
                filename = attachment.get("filename", path.name)
                mime_type = attachment.get(
                    "mime_type",
                    mimetypes.guess_type(str(path))[0] or "application/octet-stream",
                )
                with path.open("rb") as f:
                    content = f.read()
                encoded = b64encode(content).decode("utf-8")
                message.add_attachment(
                    Attachment(
                        FileContent(encoded),
                        FileName(filename),
                        FileType(mime_type),
                        Disposition("attachment"),
                    )
                )

        try:
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            print(f"SendGrid status: {response.status_code}")
            print(response.headers)
        except Exception as e:
            print(f"SendGrid send failed: {e}")
            raise
