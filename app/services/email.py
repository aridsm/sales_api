import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class EmailService:
    @staticmethod
    def _build_verification_html(
        name: str, verification_link: str, expire_hours: int
    ) -> str:
        return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <title>Confirme seu e-mail | SalesApp</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap"
      rel="stylesheet"
    />
    <style>
      body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
      table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
      img {{ -ms-interpolation-mode: bicubic; border: 0; outline: none; text-decoration: none; }}
      table {{ border-collapse: separate !important; }}
      body {{ height: 100% !important; margin: 0 !important; padding: 32px 16px !important; width: 100% !important; }}
      @media only screen and (max-width: 600px) {{
        body {{ padding: 12px 8px !important; }}
        .email-header {{ padding: 22px 18px 16px 18px !important; }}
        .email-body {{ padding: 22px 18px !important; }}
        .email-footer {{ padding: 18px 14px !important; }}
        .email-title {{ font-size: 18px !important; }}
        .btn-primary {{ display: block !important; width: 100% !important; padding: 12px 16px !important; box-sizing: border-box !important; }}
      }}
    </style>
  </head>
  <body style="margin: 0; padding: 32px 16px; background-color: #f8fafc; font-family: 'Figtree', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a;">
    <div class="email-wrapper" style="max-width: 560px; margin: 0 auto;">
      
      <table class="email-card" role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 2px; overflow: hidden; border-collapse: separate !important;">
        
        <tr>
          <td class="email-topbar" style="background-color: #2563eb; height: 4px; line-height: 4px; font-size: 1px;">&nbsp;</td>
        </tr>

        <tr>
          <td class="email-header" align="center" style="padding: 28px 32px 20px 32px; border-bottom: 1px solid #f1f5f9; text-align: center;">
            <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin: 0 auto;">
              <tr>
                <td style="vertical-align: middle; padding-right: 8px;">
                  <!-- SalesApp Small Logo -->
                  <svg class="brand-icon" width="26" height="26" viewBox="0 0 480 480" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: block; border-radius: 2px;">
                    <rect width="480" height="480" rx="96" fill="#2563eb" />
                    <g transform="scale(0.65) translate(129, 129)">
                      <path d="M160 160h160v160H160zM0 320h160v160H0zM0 0h160v160H0zM320 320h160v160H320zM320 0h160v160H320z" fill="#ffffff" />
                    </g>
                  </svg>
                </td>
                <td style="vertical-align: middle;">
                  <span class="brand-name" style="font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.4px; font-family: 'Figtree', sans-serif;">
                    Sales<span style="color: #2563eb;">App</span>
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <tr>
          <td class="email-body" style="padding: 32px 32px 28px 32px;">
            
            <!-- Greeting & Main Message -->
            <h1 class="email-title" style="font-size: 20px; font-weight: 700; color: #0f172a; letter-spacing: -0.3px; margin: 0 0 16px 0; line-height: 1.3;">
              Olá, <strong style="color: #0f172a;">{name}</strong>!
            </h1>

            <p class="email-lead" style="font-size: 15px; color: #334155; line-height: 1.65; margin: 0 0 24px 0;">
              Obrigado por se cadastrar no <strong style="color: #0f172a; font-weight: 700;">SalesApp</strong>. Para ativar sua conta e começar a gerenciar suas vendas e produtos, confirme seu endereço de e-mail clicando no botão abaixo:
            </p>

            <div class="cta-container" style="text-align: center; margin: 28px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin: 0 auto; border-collapse: separate !important;">
                <tr>
                  <td align="center" style="border-radius: 2px; background-color: #2563eb;">
                    <a
                      href="{verification_link}"
                      class="btn-primary"
                      target="_blank"
                      style="display: inline-block; background-color: #2563eb; color: #ffffff !important; font-size: 14px; font-weight: 600; text-decoration: none; padding: 12px 28px; border-radius: 2px; font-family: 'Figtree', sans-serif; letter-spacing: -0.1px;"
                    >
                      Confirmar meu E-mail
                    </a>
                  </td>
                </tr>
              </table>
            </div>

            <div class="info-box" style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 2px; padding: 14px 16px; margin-bottom: 20px; font-size: 13px; color: #1e3a8a; line-height: 1.5;">
              Este link expira em <strong style="color: #172554;">{expire_hours} horas</strong>. Se você não criou uma conta no SalesApp, pode desconsiderar este e-mail com segurança.
            </div>

            <!-- Fallback URL Section -->
            <div class="link-box" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 2px; padding: 14px 16px; margin-top: 20px;">
              <div class="link-box-title" style="font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 6px;">
                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
              </div>
              <a
                href="{verification_link}"
                class="link-alt"
                style="display: block; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; color: #2563eb; text-decoration: none; word-break: break-all; line-height: 1.4;"
              >
                {verification_link}
              </a>
            </div>

          </td>
        </tr>

        <tr>
          <td class="email-footer" align="center" style="background-color: #fafbfc; border-top: 1px solid #f1f5f9; padding: 20px 32px; text-align: center;">
            <div class="footer-links" style="margin-bottom: 10px;">
              <a href="#" style="color: #64748b; text-decoration: none; font-size: 12px; margin: 0 8px; font-weight: 500;">Central de Ajuda</a>
              <span style="color: #cbd5e1;">•</span>
              <a href="#" style="color: #64748b; text-decoration: none; font-size: 12px; margin: 0 8px; font-weight: 500;">Termos de Uso</a>
              <span style="color: #cbd5e1;">•</span>
              <a href="#" style="color: #64748b; text-decoration: none; font-size: 12px; margin: 0 8px; font-weight: 500;">Privacidade</a>
            </div>
            
            <div class="footer-copyright" style="font-size: 12px; color: #64748b; line-height: 1.5;">
              © SalesApp. Todos os direitos reservados.
            </div>
            
            <div class="footer-disclaimer" style="font-size: 11px; color: #94a3b8; margin-top: 6px; line-height: 1.4;">
              Esta é uma mensagem automática enviada pelo sistema SalesApp para verificação de credenciais de acesso.
            </div>
          </td>
        </tr>

      </table>

    </div>
  </body>
</html>
"""

    @classmethod
    async def send_verification_email(cls, email: str, name: str, token: str) -> bool:
        if not settings.RESEND_API_KEY:
            logger.warning(
                "RESEND_API_KEY not configured. Verification email was NOT sent to %s. Link: %s/verify-email?token=%s",
                email,
                settings.FRONTEND_URL,
                token,
            )
            return False

        verification_link = (
            f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"
        )
        html_content = cls._build_verification_html(
            name=name,
            verification_link=verification_link,
            expire_hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS,
        )

        payload = {
            "from": settings.EMAIL_FROM,
            "to": [email],
            "subject": "Confirme seu e-mail - SalesApp",
            "html": html_content,
        }

        headers = {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    RESEND_API_URL, json=payload, headers=headers
                )
                if response.status_code in (200, 201):
                    logger.info("Verification email successfully sent to %s", email)
                    return True
                else:
                    logger.error(
                        "Failed to send verification email to %s. Status: %s. Response: %s",
                        email,
                        response.status_code,
                        response.text,
                    )
                    return False
        except Exception as exc:
            logger.exception(
                "Exception while sending verification email to %s: %s", email, exc
            )
            return False

    @staticmethod
    def _build_email_change_html(
        name: str, verification_link: str, expire_hours: int, new_email: str
    ) -> str:
        return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <title>Confirme a alteração de seu e-mail | SalesApp</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap"
      rel="stylesheet"
    />
    <style>
      body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
      table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
      img {{ -ms-interpolation-mode: bicubic; border: 0; outline: none; text-decoration: none; }}
      table {{ border-collapse: separate !important; }}
      body {{ height: 100% !important; margin: 0 !important; padding: 32px 16px !important; width: 100% !important; }}
      @media only screen and (max-width: 600px) {{
        body {{ padding: 12px 8px !important; }}
        .email-header {{ padding: 22px 18px 16px 18px !important; }}
        .email-body {{ padding: 22px 18px !important; }}
        .email-footer {{ padding: 18px 14px !important; }}
        .email-title {{ font-size: 18px !important; }}
        .btn-primary {{ display: block !important; width: 100% !important; padding: 12px 16px !important; box-sizing: border-box !important; }}
      }}
    </style>
  </head>
  <body style="margin: 0; padding: 32px 16px; background-color: #f8fafc; font-family: 'Figtree', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a;">
    <div class="email-wrapper" style="max-width: 560px; margin: 0 auto;">
      
      <table class="email-card" role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 2px; overflow: hidden; border-collapse: separate !important;">
        
        <tr>
          <td class="email-topbar" style="background-color: #2563eb; height: 4px; line-height: 4px; font-size: 1px;">&nbsp;</td>
        </tr>

        <tr>
          <td class="email-header" align="center" style="padding: 28px 32px 20px 32px; border-bottom: 1px solid #f1f5f9; text-align: center;">
            <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin: 0 auto;">
              <tr>
                <td style="vertical-align: middle; padding-right: 8px;">
                  <!-- SalesApp Small Logo -->
                  <svg class="brand-icon" width="26" height="26" viewBox="0 0 480 480" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: block; border-radius: 2px;">
                    <rect width="480" height="480" rx="96" fill="#2563eb" />
                    <g transform="scale(0.65) translate(129, 129)">
                      <path d="M160 160h160v160H160zM0 320h160v160H0zM0 0h160v160H0zM320 320h160v160H320zM320 0h160v160H320z" fill="#ffffff" />
                    </g>
                  </svg>
                </td>
                <td style="vertical-align: middle;">
                  <span class="brand-name" style="font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.4px; font-family: 'Figtree', sans-serif;">
                    Sales<span style="color: #2563eb;">App</span>
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <tr>
          <td class="email-body" style="padding: 32px 32px 28px 32px;">
            
            <!-- Greeting & Main Message -->
            <h1 class="email-title" style="font-size: 20px; font-weight: 700; color: #0f172a; letter-spacing: -0.3px; margin: 0 0 16px 0; line-height: 1.3;">
              Olá, <strong style="color: #0f172a;">{name}</strong>!
            </h1>

            <p class="email-lead" style="font-size: 15px; color: #334155; line-height: 1.65; margin: 0 0 24px 0;">
              Recebemos uma solicitação para alterar o endereço de e-mail da sua conta no <strong style="color: #0f172a; font-weight: 700;">SalesApp</strong> para <strong>{new_email}</strong>. Para confirmar esta alteração, clique no botão abaixo:
            </p>

            <div class="cta-container" style="text-align: center; margin: 28px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin: 0 auto; border-collapse: separate !important;">
                <tr>
                  <td align="center" style="border-radius: 2px; background-color: #2563eb;">
                    <a
                      href="{verification_link}"
                      class="btn-primary"
                      target="_blank"
                      style="display: inline-block; background-color: #2563eb; color: #ffffff !important; font-size: 14px; font-weight: 600; text-decoration: none; padding: 12px 28px; border-radius: 2px; font-family: 'Figtree', sans-serif; letter-spacing: -0.1px;"
                    >
                      Confirmar Novo E-mail
                    </a>
                  </td>
                </tr>
              </table>
            </div>

            <div class="info-box" style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 2px; padding: 14px 16px; margin-bottom: 20px; font-size: 13px; color: #1e3a8a; line-height: 1.5;">
              Este link expira em <strong style="color: #172554;">{expire_hours} horas</strong>. Se você não solicitou essa alteração, por favor verifique a segurança da sua conta e desconsidere este e-mail.
            </div>

            <!-- Fallback URL Section -->
            <div class="link-box" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 2px; padding: 14px 16px; margin-top: 20px;">
              <div class="link-box-title" style="font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 6px;">
                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
              </div>
              <a
                href="{verification_link}"
                class="link-alt"
                style="display: block; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; color: #2563eb; text-decoration: none; word-break: break-all; line-height: 1.4;"
              >
                {verification_link}
              </a>
            </div>

          </td>
        </tr>

        <tr>
          <td class="email-footer" align="center" style="background-color: #fafbfc; border-top: 1px solid #f1f5f9; padding: 20px 32px; text-align: center;">
            <div class="footer-links" style="margin-bottom: 10px;">
              <a href="#" style="color: #64748b; text-decoration: none; font-size: 12px; margin: 0 8px; font-weight: 500;">Central de Ajuda</a>
              <span style="color: #cbd5e1;">•</span>
              <a href="#" style="color: #64748b; text-decoration: none; font-size: 12px; margin: 0 8px; font-weight: 500;">Termos de Uso</a>
              <span style="color: #cbd5e1;">•</span>
              <a href="#" style="color: #64748b; text-decoration: none; font-size: 12px; margin: 0 8px; font-weight: 500;">Privacidade</a>
            </div>
            
            <div class="footer-copyright" style="font-size: 12px; color: #64748b; line-height: 1.5;">
              © SalesApp. Todos os direitos reservados.
            </div>
            
            <div class="footer-disclaimer" style="font-size: 11px; color: #94a3b8; margin-top: 6px; line-height: 1.4;">
              Esta é uma mensagem automática enviada pelo sistema SalesApp para verificação de credenciais de acesso.
            </div>
          </td>
        </tr>

      </table>

    </div>
  </body>
</html>
"""

    @classmethod
    async def send_email_change_verification(
        cls, email: str, name: str, token: str
    ) -> bool:
        if not settings.RESEND_API_KEY:
            logger.warning(
                "RESEND_API_KEY not configured. Email change verification email was NOT sent to %s. Link: %s/verify-email?token=%s&type=email_change",
                email,
                settings.FRONTEND_URL,
                token,
            )
            return False

        verification_link = (
            f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}&type=email_change"
        )
        html_content = cls._build_email_change_html(
            name=name,
            verification_link=verification_link,
            expire_hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS,
            new_email=email,
        )

        payload = {
            "from": settings.EMAIL_FROM,
            "to": [email],
            "subject": "Confirme a alteração do seu e-mail - SalesApp",
            "html": html_content,
        }

        headers = {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    RESEND_API_URL, json=payload, headers=headers
                )
                if response.status_code in (200, 201):
                    logger.info("Email change verification email successfully sent to %s", email)
                    return True
                else:
                    logger.error(
                        "Failed to send email change verification email to %s. Status: %s. Response: %s",
                        email,
                        response.status_code,
                        response.text,
                    )
                    return False
        except Exception as exc:
            logger.exception(
                "Exception while sending email change verification email to %s: %s",
                email,
                exc,
            )
            return False

    @staticmethod
    def _build_password_reset_html(
        name: str, reset_link: str, expire_hours: int = 1
    ) -> str:
        return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <title>Redefinir sua senha | SalesApp</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap"
      rel="stylesheet"
    />
    <style>
      body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
      table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
      img {{ -ms-interpolation-mode: bicubic; border: 0; outline: none; text-decoration: none; }}
      table {{ border-collapse: separate !important; }}
      body {{ height: 100% !important; margin: 0 !important; padding: 32px 16px !important; width: 100% !important; }}
      @media only screen and (max-width: 600px) {{
        body {{ padding: 12px 8px !important; }}
        .email-header {{ padding: 22px 18px 16px 18px !important; }}
        .email-body {{ padding: 22px 18px !important; }}
        .email-footer {{ padding: 18px 14px !important; }}
        .email-title {{ font-size: 18px !important; }}
        .btn-primary {{ display: block !important; width: 100% !important; padding: 12px 16px !important; box-sizing: border-box !important; }}
      }}
    </style>
  </head>
  <body style="margin: 0; padding: 32px 16px; background-color: #f8fafc; font-family: 'Figtree', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a;">
    <div class="email-wrapper" style="max-width: 560px; margin: 0 auto;">
      
      <table class="email-card" role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 2px; overflow: hidden; border-collapse: separate !important;">
        
        <tr>
          <td class="email-topbar" style="background-color: #2563eb; height: 4px; line-height: 4px; font-size: 1px;">&nbsp;</td>
        </tr>

        <tr>
          <td class="email-header" align="center" style="padding: 28px 32px 20px 32px; border-bottom: 1px solid #f1f5f9; text-align: center;">
            <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin: 0 auto;">
              <tr>
                <td style="vertical-align: middle; padding-right: 8px;">
                  <!-- SalesApp Small Logo -->
                  <svg class="brand-icon" width="26" height="26" viewBox="0 0 480 480" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: block; border-radius: 2px;">
                    <rect width="480" height="480" rx="96" fill="#2563eb" />
                    <g transform="scale(0.65) translate(129, 129)">
                      <path d="M160 160h160v160H160zM0 320h160v160H0zM0 0h160v160H0zM320 320h160v160H320zM320 0h160v160H320z" fill="#ffffff" />
                    </g>
                  </svg>
                </td>
                <td style="vertical-align: middle;">
                  <span class="brand-name" style="font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.4px; font-family: 'Figtree', sans-serif;">
                    Sales<span style="color: #2563eb;">App</span>
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <tr>
          <td class="email-body" style="padding: 32px 32px 28px 32px;">
            
            <!-- Greeting & Main Message -->
            <h1 class="email-title" style="font-size: 20px; font-weight: 700; color: #0f172a; letter-spacing: -0.3px; margin: 0 0 16px 0; line-height: 1.3;">
              Olá, <strong style="color: #0f172a;">{name}</strong>!
            </h1>

            <p class="email-lead" style="font-size: 15px; color: #334155; line-height: 1.65; margin: 0 0 24px 0;">
              Recebemos uma solicitação para redefinir a senha da sua conta no <strong style="color: #0f172a; font-weight: 700;">SalesApp</strong>. Para cadastrar uma nova senha, clique no botão abaixo:
            </p>

            <div class="cta-container" style="text-align: center; margin: 28px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin: 0 auto; border-collapse: separate !important;">
                <tr>
                  <td align="center" style="border-radius: 2px; background-color: #2563eb;">
                    <a
                      href="{reset_link}"
                      class="btn-primary"
                      target="_blank"
                      style="display: inline-block; background-color: #2563eb; color: #ffffff !important; font-size: 14px; font-weight: 600; text-decoration: none; padding: 12px 28px; border-radius: 2px; font-family: 'Figtree', sans-serif; letter-spacing: -0.1px;"
                    >
                      Redefinir Senha
                    </a>
                  </td>
                </tr>
              </table>
            </div>

            <div class="info-box" style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 2px; padding: 14px 16px; margin-bottom: 20px; font-size: 13px; color: #1e3a8a; line-height: 1.5;">
              Este link expira em <strong style="color: #172554;">{expire_hours} hora</strong>. Se você não solicitou esta alteração, por favor desconsidere este e-mail; sua senha permanecerá a mesma.
            </div>

            <!-- Fallback URL Section -->
            <div class="link-box" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 2px; padding: 14px 16px; margin-top: 20px;">
              <div class="link-box-title" style="font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 6px;">
                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
              </div>
              <a
                href="{reset_link}"
                class="link-alt"
                style="display: block; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; color: #2563eb; text-decoration: none; word-break: break-all; line-height: 1.4;"
              >
                {reset_link}
              </a>
            </div>

          </td>
        </tr>

        <tr>
          <td class="email-footer" align="center" style="background-color: #fafbfc; border-top: 1px solid #f1f5f9; padding: 20px 32px; text-align: center;">
            <div class="footer-links" style="margin-bottom: 10px;">
              <a href="#" style="color: #64748b; text-decoration: none; font-size: 12px; margin: 0 8px; font-weight: 500;">Central de Ajuda</a>
              <span style="color: #cbd5e1;">•</span>
              <a href="#" style="color: #64748b; text-decoration: none; font-size: 12px; margin: 0 8px; font-weight: 500;">Termos de Uso</a>
              <span style="color: #cbd5e1;">•</span>
              <a href="#" style="color: #64748b; text-decoration: none; font-size: 12px; margin: 0 8px; font-weight: 500;">Privacidade</a>
            </div>
            
            <div class="footer-copyright" style="font-size: 12px; color: #64748b; line-height: 1.5;">
              © SalesApp. Todos os direitos reservados.
            </div>
            
            <div class="footer-disclaimer" style="font-size: 11px; color: #94a3b8; margin-top: 6px; line-height: 1.4;">
              Esta é uma mensagem automática enviada pelo sistema SalesApp para recuperação de senha.
            </div>
          </td>
        </tr>

      </table>

    </div>
  </body>
</html>
"""

    @classmethod
    async def send_password_reset_email(
        cls, email: str, name: str, token: str
    ) -> bool:
        reset_link = (
            f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
        )
        if not settings.RESEND_API_KEY:
            logger.warning(
                "RESEND_API_KEY not configured. Password reset email was NOT sent to %s. Link: %s",
                email,
                reset_link,
            )
            return False

        html_content = cls._build_password_reset_html(
            name=name,
            reset_link=reset_link,
            expire_hours=1,
        )

        payload = {
            "from": settings.EMAIL_FROM,
            "to": [email],
            "subject": "Redefinição de senha - SalesApp",
            "html": html_content,
        }

        headers = {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    RESEND_API_URL, json=payload, headers=headers
                )
                if response.status_code in (200, 201):
                    logger.info("Password reset email successfully sent to %s", email)
                    return True
                else:
                    logger.error(
                        "Failed to send password reset email to %s. Status: %s. Response: %s",
                        email,
                        response.status_code,
                        response.text,
                    )
                    return False
        except Exception as exc:
            logger.exception(
                "Exception while sending password reset email to %s: %s",
                email,
                exc,
            )
            return False


