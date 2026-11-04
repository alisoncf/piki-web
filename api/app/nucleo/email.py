"""Envio de e-mail pela conta do sistema (D29): um Gmail com senha de app, configurado no .env."""
import smtplib
from email.message import EmailMessage

from app.config import configuracao


class ErroEmail(Exception):
    """Sem a conta no .env, ou o servidor recusou (senha errada, sem internet...)."""


def remetente() -> str:
    usuario = configuracao().email_usuario
    if not usuario or not configuracao().email_senha:
        raise ErroEmail("Falta a conta de e-mail no .env do servidor (PIKI_EMAIL_USUARIO e PIKI_EMAIL_SENHA)")
    return usuario


def enviar(para: str, assunto: str, texto: str, anexos: list[tuple[str, bytes, str]] = ()) -> None:
    """Manda o e-mail; cada anexo é (nome do arquivo, conteúdo, tipo, como "application/pdf")."""
    c = configuracao()
    mensagem = EmailMessage()
    mensagem["From"] = f"{c.email_nome} <{remetente()}>"
    mensagem["To"] = para
    mensagem["Subject"] = assunto
    mensagem.set_content(texto)
    for nome, conteudo, tipo in anexos:
        principal, secundario = tipo.split("/")
        mensagem.add_attachment(conteudo, maintype=principal, subtype=secundario, filename=nome)
    try:
        with smtplib.SMTP(c.email_servidor, c.email_porta, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(c.email_usuario, c.email_senha)
            smtp.send_message(mensagem)
    except smtplib.SMTPAuthenticationError:
        raise ErroEmail("O Gmail recusou a conta: confira o usuário e a senha de app no .env")
    except (smtplib.SMTPException, OSError) as e:
        raise ErroEmail(f"Não foi possível mandar o e-mail ({e.__class__.__name__}): tente de novo")
