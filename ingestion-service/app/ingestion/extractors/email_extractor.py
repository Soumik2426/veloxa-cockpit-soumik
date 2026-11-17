from email import policy
from email.parser import BytesParser
from pathlib import Path


class EmailExtractor:

    @staticmethod
    def _get_body(message) -> str:

        plain_text_parts = []
        html_parts = []

        if message.is_multipart():

            for part in message.walk():

                if part.get_content_maintype() == "multipart":
                    continue

                if part.get_content_disposition() == "attachment":
                    continue

                content_type = part.get_content_type()

                try:
                    content = part.get_content()
                except Exception:
                    continue

                if not isinstance(content, str):
                    continue

                if content_type == "text/plain":
                    plain_text_parts.append(content)

                elif content_type == "text/html":
                    html_parts.append(content)

        else:

            try:
                content = message.get_content()

                if isinstance(content, str):
                    if message.get_content_type() == "text/plain":
                        plain_text_parts.append(content)

                    elif message.get_content_type() == "text/html":
                        html_parts.append(content)

            except Exception:
                pass

        # Prefer plain text to avoid unnecessary HTML conversion
        if plain_text_parts:
            return "\n\n".join(plain_text_parts).strip()

        if html_parts:
            return "\n\n".join(html_parts).strip()

        return ""

    def extract(self, file_path: Path) -> dict:

        with open(file_path, "rb") as email_file:
            message = BytesParser(policy=policy.default).parse(email_file)

        attachments = []

        if message.is_multipart():

            for part in message.walk():

                if part.get_content_disposition() == "attachment":

                    attachments.append({
                        "filename": part.get_filename(),
                        "content_type": part.get_content_type(),
                        "size_bytes": len(part.get_payload(decode=True) or b"")
                    })

        return {
            "sender": str(message.get("From", "")),
            "recipient": str(message.get("To", "")),
            "cc": str(message.get("Cc", "")),
            "subject": str(message.get("Subject", "")),
            "date": str(message.get("Date", "")),
            "message_id": str(message.get("Message-ID", "")),
            "body": self._get_body(message),
            "attachments": attachments,
            "record_status": "DATA"
        }
